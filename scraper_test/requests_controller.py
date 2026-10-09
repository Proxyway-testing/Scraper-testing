import asyncio
from typing import Callable, Coroutine, List, Any

class RequestsController:
    """
    is a batching rate limiter/scheduler for async requests. 
    Instead of firing every submitted item immediately, it collects items 
    into batches and releases a batch at most once per fixed time interval.
    In the context of scrapers, the RequestsController starts X jobs per Y
    time interval. E.g. 10 requests(jobs) per 1 second (inverval = 1.0)
    """

    def __init__(
        self,
        request_fn: Callable[[dict], Coroutine],
        interval: float = 1.0,
        batch_size: int = 2,
        max_concurrency: int = 50
    ):
        self.request_fn = request_fn
        self.interval = interval
        self.batch_size = batch_size
        self._semaphore = asyncio.Semaphore(max_concurrency)

        self._queue = asyncio.Queue()
        self._stop_event = asyncio.Event()
        self._task: asyncio.Task | None = None

    def start(self):
        self._task = asyncio.create_task(self._run())

    async def stop (self):
        """The controller will not accept any more items into the queue after
        stop is called."""
        self._stop_event.set()
        if self._task:
            await self._task

    async def submit(self, item: Any):
        """ xx """
        await self._queue.put(item)

    async def _run(self):
        loop = asyncio.get_event_loop()
        pending_sends: list[asyncio.Task] = []

        #while not self._stop_event.is_set():
        while True:
            cycle_start = loop.time()
            batch = []

            # Collect items up to interval seconds or until max batch size is reached
            while len(batch) < self.batch_size:
                elapsed = loop.time() - cycle_start
                remaining = self.interval - elapsed

                if remaining <= 0: #remaining time
                    break
                try:
                    item = await asyncio.wait_for(self._queue.get(), timeout = remaining)
                    batch.append(item)
                except asyncio.TimeoutError:
                    break

            if batch:
                print (f"Sending batch of {len(batch)} at {loop.time()}")
                #send the batch to be run in the background
                task = asyncio.create_task(self._send_batch(batch))
                pending_sends.append(task)
                pending_sends = [t for t in pending_sends if not t.done()]

            # If item feeding is done and queue is empty and no active batch then stop
            if self._stop_event.is_set() and self._queue.empty() and not batch:
                break
            #always wait the full interval even if batch fills up
            elapsed = loop.time() - cycle_start
            if elapsed < self.interval:
                await asyncio.sleep(self.interval - elapsed)
        if pending_sends:
            await asyncio.gather(*pending_sends)  
        

    def _time_until_next_flush(self, last_flush: float) -> float:
        elapsed = asyncio.get_event_loop().time() - last_flush
        return max(0.0, self.interval - elapsed)

    async def _flush_all_remaining(self):
        batch = []
        while not self._queue.empty():
            batch.append(self._queue.get_nowait())
        if batch:
            await self._send_batch(batch)

    async def _send_batch(self, batch: List[Any]):
        async def bound_request(item):
            async with self._semaphore:
                try:
                    return await self.request_fn(item) #item has target, url and scraper
                except Exception as e:
                    # proper log later
                    print (f"Request error: {e}")
                    return None

        await asyncio.gather(*(bound_request(item) for item in batch))