import asyncio
import logging
from typing import List, Any
from app.database import AsyncSessionLocal

logger = logging.getLogger("db_batcher")

class DatabaseBatcher:
    """
    🚀 HIGH-THROUGHPUT BATCH PERSISTENCE
    Buffers database objects and flushes them in batches to reduce IOPS and transaction overhead.
    """
    def __init__(self, name: str, batch_size: int = 500, flush_interval: int = 5):
        self.name = name
        self.buffer: List[Any] = []
        self.batch_size = batch_size
        self.flush_interval = flush_interval
        self._lock = asyncio.Lock()
        self._flush_task = None
        self._running = False

    def start(self):
        """Starts the background flush loop."""
        if not self._running:
            self._running = True
            self._flush_task = asyncio.create_task(self._periodic_flush())
            logger.info(f"⚡ Batcher [{self.name}] Started (Size: {self.batch_size}, Interval: {self.flush_interval}s)")

    async def stop(self):
        """Stops the flush loop and performs a final flush."""
        self._running = False
        if self._flush_task:
            self._flush_task.cancel()
        await self.flush()
        logger.info(f"🛑 Batcher [{self.name}] Stopped")

    async def add(self, obj: Any):
        """Adds an object to the buffer and triggers a flush if batch size reached."""
        async with self._lock:
            self.buffer.append(obj)
            if len(self.buffer) >= self.batch_size:
                # Fire and forget flush to not block the caller
                asyncio.create_task(self._flush_buffer_internal())

    async def _periodic_flush(self):
        """Periodically flushes the buffer if it's not empty."""
        while self._running:
            try:
                await asyncio.sleep(self.flush_interval)
                await self.flush()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in batcher [{self.name}] loop: {e}")

    async def flush(self):
        """Force a flush of the current buffer."""
        async with self._lock:
            await self._flush_buffer_internal()

    async def _flush_buffer_internal(self):
        """Internal method to perform the database write."""
        if not self.buffer:
            return

        to_flush = self.buffer.copy()
        self.buffer.clear()
        
        try:
            async with AsyncSessionLocal() as session:
                session.add_all(to_flush)
                await session.commit()
            if len(to_flush) > 0:
                logger.debug(f"📦 [{self.name}] Batch Flush: Persisted {len(to_flush)} records.")
        except Exception as e:
            logger.error(f"❌ [{self.name}] Batch Flush Failed: {e}")

# Specialized batchers for high-volume telemetry
inspection_batcher = DatabaseBatcher("Inspections", batch_size=500, flush_interval=5)
system_event_batcher = DatabaseBatcher("SystemEvents", batch_size=100, flush_interval=10)
