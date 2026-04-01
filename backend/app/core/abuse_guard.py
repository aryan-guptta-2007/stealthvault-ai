from collections import defaultdict
from datetime import datetime, timedelta
import threading

"""
🛡️ STEALTHVAULT AI - API ABUSE GUARD (L7 Defense)
Mission-critical utility to track and neutralize application-layer attackers.
Tracks failed requests (4XX) to detect brute-force and scanning attempts.
"""

class AbuseGuard:
    def __init__(self, threshold: int = 15, window_seconds: int = 60):
        self.threshold = threshold
        self.window = window_seconds
        # IP -> [timestamp1, timestamp2, ...]
        self.tracker = defaultdict(list)
        self._lock = threading.Lock()
        
    def record_failure(self, ip: str) -> bool:
        """
        Record a failed request for an IP and check if it has crossed the threshold.
        Returns True if the IP is now considered abusive.
        """
        now = datetime.utcnow()
        with self._lock:
            # Add current failure
            self.tracker[ip].append(now)
            
            # Clean old entries outside the window
            self.tracker[ip] = [
                t for t in self.tracker[ip]
                if now - t < timedelta(seconds=self.window)
            ]
            
            # Check threshold
            is_abusive = len(self.tracker[ip]) >= self.threshold
            return is_abusive

    def clear(self, ip: str):
        """Reset the failure count for an IP (e.g. after a successful login or manual unblock)."""
        with self._lock:
            if ip in self.tracker:
                del self.tracker[ip]

# Singleton instance for the application
abuse_guard = AbuseGuard(threshold=15, window_seconds=60)
