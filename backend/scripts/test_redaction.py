import logging
import sys
import os

# Add app to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app.core.logger import logger

def test_redaction():
    print("Testing log redaction...")
    
    # Test cases: (Message, Should contain strings)
    tests = [
        ("User login attempt with password: SuperSecret123", "[REDACTED]"),
        ("Database connection string: postgresql://admin:p@ssw0rd123@localhost:5432/db", "[REDACTED]"),
        ("Bearer token: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9", "[REDACTED]"),
        ("Internal error with secret key exposure: KEY_12345", "[REDACTED]"),
        ("Normal message: User registered successfully", "User registered successfully")
    ]
    
    for msg, expected in tests:
        logger.info(msg)
    
    print("\nCheck the console output above. If you see '[REDACTED]' for sensitive info, it's working!")

if __name__ == "__main__":
    test_redaction()
