"""
StealthVault AI - Async Stream Processor
Real-time packet processing pipeline using asyncio queues.
Handles the flow: Capture → Queue → AI Analysis → Alert → Broadcast
"""

import asyncio
import time
from datetime import datetime
from collections import deque
from typing import Optional

from app.models.alert import NetworkPacket, ThreatAlert, Severity, AnomalyResult, ClassificationResult, RiskScore
from app.database import log_event
from app.config import settings
from app.agents.detector import DetectionVerdict
from app.agents.orchestrator import soc_orchestrator
from app.websocket.feed import ws_manager
import json
import redis.asyncio as redis
from app.core.logger import logger


class StreamProcessor:
    """
    Async stream processor for real-time packet analysis.
    
    Architecture:
        [Packet Source] → [Async Queue] → [AI Pipeline] → [Alert Store + WebSocket]
    
    Features:
        - Non-blocking async processing
        - Rate tracking (packets/sec, alerts/sec)
        - Rolling window statistics
        - Auto-broadcasts alerts via WebSocket
    """

    def __init__(self, redis_url: str = "redis://localhost:6379/0"):
        # ⚡ Resilient Redis client settings
        try:
            self.redis = redis.from_url(
                redis_url, 
                decode_responses=True,
                retry_on_timeout=True,
                socket_keepalive=True,
                health_check_interval=30,
                socket_connect_timeout=2
            )
        except Exception:
            self.redis = None
            
        self.is_running: bool = False
        self.redis_url = redis_url

        # Statistics
        self.total_processed: int = 0
        self.total_alerts: int = 0
        self.dropped_packets: int = 0
        self.start_time: float = 0

        # Alert storage (in-memory, bounded)
        self.alert_store: list[ThreatAlert] = []
        self.max_alerts: int = 2000

        # Rate tracking (rolling window)
        self._packet_times: deque = deque(maxlen=1000)
        self._alert_times: deque = deque(maxlen=500)

        # Background task for listening to worker alerts
        self.listener_task: Optional[asyncio.Task] = None
        
        # Performance/Congestion monitoring
        self._last_congestion_alert: float = 0

    async def start(self):
        """Start the stream processor connecting to Redis."""
        self.is_running = True
        self.start_time = time.time()
        logger.info("⚡ Stream processor started (Redis Distributed Mode)")
        
        # Start a listener for alerts coming from the separate AI Worker
        if self.redis:
            self.listener_task = asyncio.create_task(self._listen_for_alerts())
        else:
            logger.info("⚡ Stream Processor: Redis is offline. Running in Local-Only mode.")

    async def stop(self):
        """Stop the stream processor."""
        self.is_running = False
        if self.listener_task:
            self.listener_task.cancel()
        if self.redis:
            await self.redis.close()
        logger.info("⚡ Stream processor stopped")

    async def submit(self, packet: NetworkPacket):
        """Submit a packet into the Redis queue with tiered backpressure."""
        try:
            self.total_processed += 1
            self._packet_times.append(time.time())
            
            # --- 🛡️ TIERED BACKPRESSURE CONTROLS (Only if Distributed) ---
            if self.redis:
                queue_len = await self.redis.llen("packet_queue")
                
                # 1. Congestion Level: Start dropping minor packets
                if queue_len > settings.CONGESTION_THRESHOLD:
                    # Basic priority check
                    priority = self._eval_priority(packet)
                    
                    # If congested, drop low priority
                    if priority < 1:
                        self.dropped_packets += 1
                        return
                    
                    # 2. Critical Level: Drop almost everything
                    if queue_len > settings.CRITICAL_THRESHOLD:
                        # Drop even medium priority
                        if priority < 2:
                            self.dropped_packets += 1
                            # Log congestion warning every 30s
                            if time.time() - self._last_congestion_alert > 30:
                                logger.critical(f"⚠️ SYSTEM CONGESTION: Queue={queue_len}. Dropping all low/medium priority traffic!")
                                self._last_congestion_alert = time.time()
                            return
                    
                    # 3. Overflow Recovery: Hard Drop to prevent OOM
                    if queue_len >= settings.MAX_QUEUE_SIZE:
                        self.dropped_packets += 1
                        # Log overflow every 10s
                        if time.time() - self._last_congestion_alert > 10:
                            logger.critical(f"🚨 QUEUE OVERFLOW: Queue={queue_len}. Emergency drop initiated.")
                            self._last_congestion_alert = time.time()
                        return

                # Push to the heavy AI workers
                packet_json = packet.model_dump_json()
                await self.redis.rpush("packet_queue", packet_json)
                
                # Hard ceiling: Ensure queue never exceeds MAX_QUEUE_SIZE
                await self.redis.ltrim("packet_queue", -settings.MAX_QUEUE_SIZE, -1)
            else:
                # 🏘️ LOCAL FALLBACK: If no Redis, process directly on main thread
                # This ensures the dashboard works even on Render Free/Dev without Redis
                verdict = await detector_agent.inspect(packet)
                await soc_orchestrator.process_verdict(verdict)
                if verdict.is_threat:
                    self.total_alerts += 1
                    self._alert_times.append(time.time())
            
        except Exception as e:
            logger.error(f"Failed to submit to Redis: {e}")

    def _eval_priority(self, packet: NetworkPacket) -> int:
        """Heuristic to determine packet priority during congestion."""
        # Priority 0: Disposable (Small ordinary TCP/UDP)
        # Priority 1: Important (HTTP/HTTPS with payloads, unknown services)
        # Priority 2: Critical (Management, infrastructure, or suspicious signatures)
        
        # 1. Check for infrastructure/management ports
        CRITICAL_PORTS = {22, 53, 161, 3389, 445} # SSH, DNS, SNMP, RDP, SMB
        if packet.src_port in CRITICAL_PORTS or packet.dst_port in CRITICAL_PORTS:
            return 2
            
        # 2. Heuristic for "heavy" or "probing" behavior
        if packet.payload_size > 1024:
            return 1
            
        # 3. New connections are often more relevant than small keep-alives
        if packet.protocol.name in ["TCP", "ICMP"]:
            return 1
            
        return 0

    async def _listen_for_alerts(self):
        """Runs in background to subscribe to processed ML results from the AI worker."""
        if not self.redis:
            return

        backoff = 1
        max_backoff = 60
        
        while self.is_running:
            try:
                # Ensure connection is fresh
                if not hasattr(self, 'redis') or self.redis is None:
                    self.redis = redis.from_url(self.redis_url, decode_responses=True)

                pubsub = self.redis.pubsub()
                await pubsub.subscribe("soc_results")
                logger.info("⚡ Stream Processor: Subscribed to 'soc_results' channel")
                
                # Reset backoff on successful connection
                backoff = 1
                
                async for message in pubsub.listen():
                    if not self.is_running:
                        break
                        
                    if message['type'] == 'message':
                        try:
                            data = json.loads(message['data'])
                            
                            # Reconstruct the Verdict
                            verdict = DetectionVerdict(
                                packet=NetworkPacket(**data["packet"]),
                                features=None, 
                                anomaly=AnomalyResult(**data["anomaly"]),
                                classification=ClassificationResult(**data["classification"]),
                                risk=RiskScore(**data["risk"]),
                                signal_count=data.get("signal_count", 0),
                                combined_confidence=data.get("combined_confidence", 0.0),
                                is_repeat_offender=data.get("is_repeat_offender", False)
                            )
                            
                            # Hand it to the Orchestrator's subsequent stages
                            await soc_orchestrator.process_verdict(verdict)
                            
                            # Update local stream processor alert counts
                            if verdict.is_threat:
                                self.total_alerts += 1
                                self._alert_times.append(time.time())
                        except Exception as e:
                            logger.error(f"⚠️ Error processing alert message: {e}")
                            
            except (redis.ConnectionError, redis.TimeoutError) as e:
                log_event("WARNING", "StreamProcessor", f"Redis connection lost: {e}. Retrying in {backoff}s...")
                await asyncio.sleep(backoff)
                backoff = min(backoff * 2, 60)
            except Exception as e:
                log_event("ERROR", "StreamProcessor", f"Critical stream loop error: {e}", stack_trace=str(e))
                await asyncio.sleep(5)

    def get_stats(self) -> dict:
        """Get real-time processing statistics."""
        now = time.time()
        elapsed = now - self.start_time if self.start_time else 0

        # Packets per second (last 10 seconds)
        recent_packets = sum(1 for t in self._packet_times if now - t < 10)
        pps = recent_packets / min(10, elapsed) if elapsed > 0 else 0

        # Alerts per minute (last 60 seconds)
        recent_alerts = sum(1 for t in self._alert_times if now - t < 60)
        apm = recent_alerts  # already per minute window

        # Severity breakdown
        severity_counts = {
            "critical": sum(1 for a in self.alert_store if a.risk.severity == Severity.CRITICAL),
            "high": sum(1 for a in self.alert_store if a.risk.severity == Severity.HIGH),
            "medium": sum(1 for a in self.alert_store if a.risk.severity == Severity.MEDIUM),
            "low": sum(1 for a in self.alert_store if a.risk.severity == Severity.LOW),
        }

        return {
            "is_running": self.is_running,
            "total_processed": self.total_processed,
            "total_dropped": self.dropped_packets,
            "total_alerts": self.total_alerts,
            "packets_per_second": round(pps, 1),
            "alerts_per_minute": apm,
            "queue_size": 0, # Cannot block in async
            "severity_counts": severity_counts,
            "uptime_seconds": round(elapsed, 1),
        }


# Singleton
stream_processor = StreamProcessor()
