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
from app.agents.detector import DetectionVerdict
from app.agents.orchestrator import soc_orchestrator
from app.websocket.feed import ws_manager
import json
import redis.asyncio as redis


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
        self.redis = redis.from_url(
            redis_url, 
            decode_responses=True,
            retry_on_timeout=True,
            socket_keepalive=True,
            health_check_interval=30
        )
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

    async def start(self):
        """Start the stream processor connecting to Redis."""
        self.is_running = True
        self.start_time = time.time()
        print("⚡ Stream processor started (Redis Distributed Mode)")
        
        # Start a listener for alerts coming from the separate AI Worker
        self.listener_task = asyncio.create_task(self._listen_for_alerts())

    async def stop(self):
        """Stop the stream processor."""
        self.is_running = False
        if self.listener_task:
            self.listener_task.cancel()
        await self.redis.close()
        print("⚡ Stream processor stopped")

    async def submit(self, packet: NetworkPacket):
        """Submit a packet into the Redis queue for the AI Worker."""
        try:
            self.total_processed += 1
            self._packet_times.append(time.time())
            
            # Basic backpressure: Check if queue is dangerously large
            client = self.redis
            queue_len = await client.llen("packet_queue")
            
            # If queue is extremely large, drop low-priority traffic
            if queue_len > 10000:
                # Drop common harmless standard traffic to save space
                if packet.protocol.name in ["HTTP", "HTTPS", "TCP"] and packet.payload_size < 100:
                    self.dropped_packets += 1
                    return
            
            # Push to the heavy AI workers
            packet_json = packet.model_dump_json()
            await client.rpush("packet_queue", packet_json)
            
            # Hard ceiling: Ensure queue never exceeds 50,000 to prevent RAM burst
            await client.ltrim("packet_queue", -50000, -1)
            
        except Exception as e:
            print(f"Failed to submit to Redis: {e}")

    async def _listen_for_alerts(self):
        """Runs in background to subscribe to processed ML results from the AI worker."""
        backoff = 1
        max_backoff = 60
        
        while self.is_running:
            try:
                # Ensure connection is fresh
                if not hasattr(self, 'redis') or self.redis is None:
                    self.redis = redis.from_url(self.redis_url, decode_responses=True)

                pubsub = self.redis.pubsub()
                await pubsub.subscribe("soc_results")
                print("⚡ Stream Processor: Subscribed to 'soc_results' channel")
                
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
                            print(f"⚠️ Error processing alert message: {e}")
                            
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
