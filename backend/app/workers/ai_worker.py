"""
╔═══════════════════════════════════════════════════════════╗
║          AI WORKER — DISTRIBUTED SCALABILITY              ║
║                                                           ║
║  Decouples CPU-heavy ML inference from the main server.   ║
║  Pulls raw packets from Redis, runs Anomaly & Classifier  ║
║  models, and pushes structured results back.              ║
╚═══════════════════════════════════════════════════════════╝
"""

import sys
import os
import time
import json
import asyncio
import redis.asyncio as redis
from datetime import datetime

# Ensure absolute path resolution 
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from app.config import settings
from app.models.alert import NetworkPacket
from app.agents.detector import detector_agent
from app.core.logger import setup_logging, logger

async def heartbeat(r: redis.Redis):
    """Pivotal Observability: Continuously broadcast the worker's presence."""
    pid = os.getpid()
    key = f"worker:heartbeat:{pid}"
    while True:
        try:
            await r.setex(key, 5, "alive")
            await asyncio.sleep(2)
        except Exception:
            await asyncio.sleep(2)

async def run_worker():
    """Main background worker loop with persistent reconnect logic."""
    setup_logging()
    logger.info("🧠 STEALTHVAULT AI WORKER INITIATED")
    
    # Initialize models (CPU heavy)
    try:
        detector_agent._ensure_models_loaded()
        logger.info("Models loaded into worker memory.")
    except Exception as e:
        logger.critical(f"Failed to load AI models: {e}")
        # If models can't load, worker is useless
        return
    
    backoff = 1
    max_backoff = 60
    
    while True:
        try:
            r = redis.from_url("redis://localhost:6379/0", decode_responses=True)
            await r.ping()
            logger.info("Connected to Redis Queue.")
            
            # Reset backoff on success
            backoff = 1
            
            # Start Observability Heartbeat
            heartbeat_task = asyncio.create_task(heartbeat(r))
            
            logger.info("📡 Waiting for packets on 'packet_queue'...")
            
            while True:
                try:
                    processed_count = 0
                    batch_size = 10
                    
                    for _ in range(batch_size):
                        # blpop blocks until an item is available
                        result = await r.blpop("packet_queue", timeout=1)
                        if not result:
                            break
                            
                        _, packet_data = result
                        try:
                            packet_dict = json.loads(packet_data)
                            packet = NetworkPacket(**packet_dict)
                            
                            # Run the ML models (Detector Agent)
                            verdict = await detector_agent.inspect(packet)
                            
                            # Send the detection verdict back to the Orchestrator via PubSub
                            verdict_data = {
                                "packet": packet.model_dump(),
                                "anomaly": verdict.anomaly.model_dump(),
                                "classification": verdict.classification.model_dump(),
                                "risk": verdict.risk.model_dump(),
                                "signal_count": verdict.signal_count,
                                "combined_confidence": verdict.combined_confidence,
                                "is_repeat_offender": verdict.is_repeat_offender
                            }
                            
                            await r.publish("soc_results", json.dumps(verdict_data))
                            processed_count += 1
                        except Exception as e:
                            logger.error(f"Failed to process packet: {e}")
                            # Push to Dead Letter Queue for auditing instead of silent drop
                            await r.rpush("redis_dlq", packet_data)
                            
                    if processed_count > 0:
                        # Use flush=True for real-time visibility in logs
                        logger.info(f"Processed {processed_count} packets from Redis.")
                        
                except (redis.ConnectionError, redis.TimeoutError):
                    logger.warning("Redis connection lost during processing loop. Reconnecting...")
                    break # Exit inner loop to reconnect
                except Exception as e:
                    logger.error(f"Unexpected loop Error: {e}")
                    await asyncio.sleep(1)
            
            # Cancel heartbeat before reconnecting
            heartbeat_task.cancel()
            
        except (redis.ConnectionError, redis.TimeoutError, ConnectionRefusedError) as e:
            logger.warning(f"Redis unavailable: {e}. Retrying in {backoff}s...")
            await asyncio.sleep(backoff)
            backoff = min(backoff * 2, max_backoff)
        except Exception as e:
            logger.critical(f"Worker process encountered a fatal error: {e}")
            await asyncio.sleep(5)

if __name__ == "__main__":
    try:
        asyncio.run(run_worker())
    except KeyboardInterrupt:
        print("\n🛑 Worker shutdown gracefully.")
