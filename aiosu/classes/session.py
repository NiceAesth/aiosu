# Based on: https://github.com/Jylpah/blitz-tools/blob/master/blitzutils.py
from __future__ import annotations

import asyncio
import functools
import time

import aiohttp
import orjson


class Session(aiohttp.ClientSession):
    """
    Client session class with customizable rate limiting.
    This implementation is based on the leaky bucket algorithm.

    ...

    Attributes
    ----------
    rate_limit : int
        the amount of requests allowed per minute (default: 1200)
        set to None to disable
    """

    MIN_SLEEP = 0.1

    def __init__(self, rate_limit: int = 1200, *args, **kwargs) -> None:
        super().__init__(*args, json_serialize=orjson.dumps, **kwargs)
        self.set_rate_limit(rate_limit)
        self._filler_task = asyncio.create_task(self._filler())
        self._queue = asyncio.Queue(min(2, rate_limit + 1))
        self._start_time = time.time()
        self._count = 0
        self.__ended = False

    def create_aiohttp_closed_event(self) -> asyncio.Event:
        """Work around aiohttp issue that doesn't properly close transports on exit.

        See https://github.com/aio-libs/aiohttp/issues/1925#issuecomment-639080209

        Returns:
        An event that will be set once all transports have been properly closed.
        """

        transports = 0
        all_is_lost = asyncio.Event()

        def connection_lost(exc, orig_lost):
            nonlocal transports

            try:
                orig_lost(exc)
            finally:
                transports -= 1
                if transports == 0:
                    all_is_lost.set()

        def eof_received(orig_eof_received):
            try:
                orig_eof_received()
            except AttributeError:
                # It may happen that eof_received() is called after
                # _app_protocol and _transport are set to None.
                pass

        for conn in self.connector._conns.values():
            for handler, _ in conn:
                proto = getattr(handler.transport, "_ssl_protocol", None)
                if proto is None:
                    continue

                transports += 1
                orig_lost = proto.connection_lost
                orig_eof_received = proto.eof_received

                proto.connection_lost = functools.partial(
                    connection_lost,
                    orig_lost=orig_lost,
                )
                proto.eof_received = functools.partial(
                    eof_received,
                    orig_eof_received=orig_eof_received,
                )

        if transports == 0:
            all_is_lost.set()

        return all_is_lost

    def __get_sleep(self) -> list:
        return None if self.rate_limit is None else 1 / self.rate_limit

    def get_rate(self) -> float:
        """Get the rate of requests"""
        return self._count / (time.time() - self._start_time)

    def get_stats(self) -> dict:
        """Get session usage statistics"""
        return {
            "rate": self.get_rate(),
            "rate_limit": self.rate_limit,
            "count": self._count,
        }

    def reset_counters(self) -> None:
        """Reset the rate counter"""
        self._start_time = time.time()
        self._count = 0

    def set_rate_limit(self, rate_limit: int = 1200) -> None:
        if rate_limit != None and rate_limit <= 0:
            raise ValueError("rate_limit must be positive")
        self.rate_limit = rate_limit

    async def close(self) -> None:
        """Close the bucket-fill task on session end"""
        if self.__ended:
            return
        self.__ended = True  # Prevent calling if session is already closed
        try:
            if self._filler_task:
                self._filler_task.cancel()
            await asyncio.wait_for(self._filler_task, timeout=0.5)
        except (asyncio.CancelledError, asyncio.TimeoutError):
            pass  # Pass if task is already ended
        closed_event = self.create_aiohttp_closed_event()
        await super().close()  # Close the session
        await closed_event.wait()

    async def _filler(self) -> None:
        """Bucker-filler task"""
        if self._queue is None:
            return
        sleep = self.__get_sleep()
        updated_at = time.monotonic()
        fraction = 0
        extra_increment = 0
        for i in range(0, self._queue.maxsize):
            self._queue.put_nowait(i)
        while True:
            if not self._queue.full():
                now = time.monotonic()
                increment = self.rate_limit * (now - updated_at)
                fraction += increment % 1
                extra_increment = fraction // 1
                pending_items = int(
                    min(
                        self._queue.maxsize - self._queue.qsize(),
                        int(increment) + extra_increment,
                    ),
                )
                fraction = fraction % 1
                for i in range(0, pending_items):
                    self._queue.put_nowait(i)
                updated_at = now
            await asyncio.sleep(sleep)

    async def _request(self, *args, **kwargs):
        """Throttled request"""
        if self._queue:
            await self._queue.get()
            self._queue.task_done()
        self._count += 1
        return await super()._request(*args, **kwargs)
