"""
StealthVault AI - Threat Intelligence Service
Fetched and caches real-time malicious IP feeds from external providers.
"""

import requests
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ThreatIntel")

# Global in-memory cache
malicious_ips = set()


def load_static_blacklist():
    """Load basic static malicious IPs (starter)"""
    return {
        "1.1.1.1",
        "8.8.8.8",   # Google DNS - used for testing block logic
        "123.45.67.89"
    }


def fetch_threat_feed():
    """Fetch external threat intel from Feodo Tracker (abuse.ch)"""
    try:
        logger.info("Fetching external threat intel feed...")
        url = "https://feodotracker.abuse.ch/downloads/ipblocklist.txt"
        response = requests.get(url, timeout=10)
        response.raise_for_status()

        ips = set()
        for line in response.text.splitlines():
            line = line.strip()
            if line and not line.startswith("#"):
                ips.add(line)

        logger.info(f"Successfully fetched {len(ips)} IPs from external feed.")
        return ips
    except Exception as e:
        logger.error(f"Failed to fetch threat feed: {e}")
        return set()


def update_threat_intel():
    """Master update function to refresh the global cache."""
    global malicious_ips

    static_ips = load_static_blacklist()
    external_ips = fetch_threat_feed()

    malicious_ips = static_ips.union(external_ips)
    logger.info(f"Threat Intelligence Cache Updated. Total Malicious IPs: {len(malicious_ips)}")


def is_malicious(ip: str) -> bool:
    """Check if an IP address exists in the threat blacklist."""
    return str(ip) in malicious_ips
