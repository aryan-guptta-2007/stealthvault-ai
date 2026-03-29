from slowapi import Limiter
from slowapi.util import get_remote_address
from app.config import settings

# Global Limiter Instance
limiter = Limiter(key_func=get_remote_address, storage_uri=settings.REDIS_URL or "memory://")
