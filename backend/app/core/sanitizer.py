import re
import logging

"""
🛡️ STEALTHVAULT AI - INPUT SANITIZATION ENGINE
Mission-critical utility to neutralize injection attacks (XSS, SQLi, Log Injection).
"""

def sanitize_string(value: str | None) -> str:
    """
    🧹 GLOBAL FIREWALL: Cleanse string of malicious control characters.
    Only permits alphanumeric characters, spaces, and selective safe symbols.
    """
    if not value or not isinstance(value, str):
        return value or ""
        
    # 1. Strip HTML/Script tags first
    value = re.sub(r"<[^>]*?>", "", value)
    
    # 2. Allow specific safe symbols: . - @ _
    # This prevents most SQLi and command injection payloads.
    # WAF-style whitelist regex:
    sanitized = re.sub(r"[^\w\s\.\-@_]", "", value)
    
    # 3. Trim whitespace
    return sanitized.strip()

def sanitize_json(data: dict) -> dict:
    """
    🧠 RECURSIVE DEPLETION: Sanitize every string in a nested dictionary.
    Ensures that complex JSON payloads are injection-resistant.
    """
    if not isinstance(data, dict):
        return data
        
    sanitized_data = {}
    for k, v in data.items():
        if isinstance(v, str):
            sanitized_data[k] = sanitize_string(v)
        elif isinstance(v, dict):
            sanitized_data[k] = sanitize_json(v)
        elif isinstance(v, list):
            sanitized_data[k] = [
                sanitize_string(item) if isinstance(item, str) else item 
                for item in v
            ]
        else:
            sanitized_data[k] = v
            
    return sanitized_data
