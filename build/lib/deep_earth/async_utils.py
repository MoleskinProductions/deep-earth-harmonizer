"""
Async utilities for running coroutines from synchronous contexts.

This module provides thread-safe async execution that works correctly
in environments where the main thread may already have an event loop
(e.g., Houdini's Python interpreter).
"""

import asyncio
import concurrent.futures
from typing import TypeVar, Coroutine, Any

T = TypeVar('T')


def run_async(coro: Coroutine[Any, Any, T]) -> T:
    """
    Execute an async coroutine from a synchronous context.
    
    This function handles the case where an event loop may already be running
    (common in DCC applications like Houdini). It runs the coroutine in a 
    separate thread with its own event loop.
    
    Args:
        coro: The coroutine to execute
        
    Returns:
        The result of the coroutine
        
    Example:
        async def fetch_data():
            async with aiohttp.ClientSession() as session:
                return await session.get(url)
        
        # From Houdini Python SOP:
        result = run_async(fetch_data())
    """
    try:
        # Check if we're in an existing event loop
        loop = asyncio.get_running_loop()
    except RuntimeError:
        # No loop running, we can use asyncio.run() directly
        return asyncio.run(coro)
    
    # Loop is already running (e.g., in Houdini), use thread pool
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(asyncio.run, coro)
        return future.result()


async def gather_with_concurrency(limit: int, *coros: Coroutine[Any, Any, T]) -> list[T]:
    """
    Run coroutines with a concurrency limit using a semaphore.
    
    Useful for limiting concurrent API requests to avoid rate limiting.
    
    Args:
        limit: Maximum number of concurrent coroutines
        *coros: Coroutines to execute
        
    Returns:
        List of results in the same order as input coroutines
    """
    semaphore = asyncio.Semaphore(limit)
    
    async def limited_coro(coro: Coroutine[Any, Any, T]) -> T:
        async with semaphore:
            return await coro
    
    return await asyncio.gather(*(limited_coro(c) for c in coros))
