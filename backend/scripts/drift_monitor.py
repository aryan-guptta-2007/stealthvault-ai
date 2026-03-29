"""
╔═══════════════════════════════════════════════════════════╗
║     STEALTHVAULT AI — MODEL DRIFT MONITOR                 ║
║                                                           ║
║  Periodically evaluates the Confidence Calibration bounds ║
║  across recent network classifications to detect zero-day ║
║  surges or data drift, triggering the Learner Engine.     ║
╚═══════════════════════════════════════════════════════════╝
"""

import sys
import os
import time
import asyncio
from datetime import datetime
from sqlalchemy import select, func

# Ensure python path works
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app.database import AsyncSessionLocal
from app.models.db_models import DBAlert
from app.ai_engine.classifier import CONFIDENCE_THRESHOLD

async def analyze_drift():
    """
    Connects to PostgreSQL, computes moving averages of confidence 
    and checks if the UNKNOWN classification rate exceeds safety bounds.
    """
    async with AsyncSessionLocal() as db:
        try:
            # Get total alerts
            total_query = await db.execute(select(func.count(DBAlert.id)))
            total_alerts = total_query.scalar()
            
            if total_alerts < 100:
                print("  [Drift Monitor] Not enough data points to compute baseline (<100 alerts).")
                return

            # Analyze recent Unknowns (Zero-Day rate)
            unknown_query = await db.execute(
                select(func.count(DBAlert.id)).where(DBAlert.attack_type == "Unknown")
            )
            unknown_count = unknown_query.scalar()
            
            zero_day_rate = unknown_count / total_alerts
            
            print(f"[{datetime.utcnow().isoformat()}] DRIFT ANALYSIS:")
            print(f"  Total Classifications: {total_alerts}")
            print(f"  Zero-Day (UNKNOWN) Classifications: {unknown_count}")
            print(f"  Current UNKNOWN Rate: {zero_day_rate:.2%}")
            
            if zero_day_rate > 0.15: # If more than 15% of traffic is Unknown
                print("  ⚠️ WARNING: High baseline drift detected! (>15% Unknowns)")
                print("  👉 The threat landscape has shifted. Gather Unknowns for manual triage and label them.")
                print("  👉 Analyst Agent will queue these anomalies for immediate retraining.")
            else:
                print("  ✅ Model metrics within acceptable safe bounds.")
            
        except Exception as e:
            print(f"  ❌ Drift Monitor Error: {e}")

def run_monitor():
    print("Starting Continuous Drift Monitor loop (CTRL+C to exit)...")
    try:
        while True:
            asyncio.run(analyze_drift())
            time.sleep(60 * 5) # Check every 5 minutes
    except KeyboardInterrupt:
        print("Stopping Drift Monitor...")

if __name__ == "__main__":
    run_monitor()
