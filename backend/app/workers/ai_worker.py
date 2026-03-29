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
    """Main background worker loop."""
    print("==================================================")
    print("🧠 STEALTHVAULT AI WORKER INITIATED")
    print("==================================================")
    
    # Initialize models (CPU heavy)
    detector_agent._ensure_models_loaded()
    print("✅ Models loaded into worker memory.")
    
    r = redis.from_url("redis://localhost:6379/0", decode_responses=True)
    
    try:
        await r.ping()
        print("✅ Connected to Redis Queue.")
    except Exception as e:
        print(f"❌ Failed to connect to Redis: {e}")
        return
        
    # Start Observability Heartbeat
    asyncio.create_task(heartbeat(r))
    
    print("📡 Waiting for packets on 'packet_queue'...")
    
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
                    print(f"Failed to process packet: {e}")
                    # Push to Dead Letter Queue for auditing instead of silent drop
                    await r.rpush("redis_dlq", packet_data)
                    
            if processed_count > 0:
                print(f"[{datetime.utcnow().time()}] Processed {processed_count} packets from Redis.", flush=True)
                
        except Exception as e:
            print(f"⚠️ Worker Error: {e}")
            await asyncio.sleep(1)

if __name__ == "__main__":
    try:
        asyncio.run(run_worker())
    except KeyboardInterrupt:
        print("\n🛑 Worker shutdown gracefully.")
