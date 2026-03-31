from locust import HttpUser, task, between
import random

class StealthVaultSOCUser(HttpUser):
    """
    🛡️ STEALTHVAULT SOC OPERATOR (Load Simulation)
    Simulates real-world security analysts querying the SOC brain.
    """
    wait_time = between(1, 5) # Realistic operator pacing
    
    def on_start(self):
        """Perform initial setup (e.g., getting a mock JWT if needed)."""
        # For this load test, we'll assume public endpoints or baked-in defaults
        pass

    @task(3)
    def view_tactical_stats(self):
        """Simulates an analyst checking the global threat stats."""
        self.client.get("/api/v1/stats/")

    @task(5)
    def fetch_threat_alerts(self):
        """Simulates an analyst scrolling through the live alert feed."""
        self.client.get("/api/v1/alerts/?limit=50")

    @task(1)
    def check_system_health(self):
        """Simulates a system administrator monitoring the SOC health."""
        self.client.get("/health")

    @task(2)
    def view_critical_threats(self):
        """Simulates a lead responder focusing on critical incidents."""
        self.client.get("/api/v1/alerts/critical")

# 🚀 HOW TO RUN:
# 1. Install locust: pip install locust
# 2. Run: locust -f scripts/load_test.py --host http://localhost:8000
# 3. Open http://localhost:8089 to start the stress test.
