"""Tests for async_utils.py — run_async and gather_with_concurrency.

Verifies correct behaviour both when no event loop is running
(normal Python) and when an event loop already exists (Houdini-like).
"""
import asyncio
import pytest
from deep_earth.async_utils import run_async, gather_with_concurrency


# ---------------------------------------------------------------------------
# run_async — no existing loop
# ---------------------------------------------------------------------------

def test_run_async_simple():
    """Runs a coroutine from a sync context when no loop is active."""
    async def add(a, b):
        return a + b

    assert run_async(add(2, 3)) == 5


def test_run_async_exception():
    """Propagates exceptions from the coroutine."""
    async def fail():
        raise ValueError("boom")

    with pytest.raises(ValueError, match="boom"):
        run_async(fail())


# ---------------------------------------------------------------------------
# run_async — existing event loop (Houdini-like)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_run_async_inside_existing_loop():
    """Uses ThreadPoolExecutor when called inside a running loop."""
    async def double(x):
        return x * 2

    # We're inside an async test, so there IS a running loop already.
    result = run_async(double(21))
    assert result == 42


@pytest.mark.asyncio
async def test_run_async_inside_loop_exception():
    """Exception propagates even from threaded executor path."""
    async def fail():
        raise RuntimeError("thread boom")

    with pytest.raises(RuntimeError, match="thread boom"):
        run_async(fail())


# ---------------------------------------------------------------------------
# gather_with_concurrency
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_gather_with_concurrency_basic():
    """Results are returned in input order."""
    async def identity(x):
        return x

    results = await gather_with_concurrency(
        3, identity(1), identity(2), identity(3),
    )
    assert results == [1, 2, 3]


@pytest.mark.asyncio
async def test_gather_with_concurrency_limits():
    """Semaphore limits concurrent execution."""
    max_concurrent = 0
    current = 0

    async def track():
        nonlocal max_concurrent, current
        current += 1
        if current > max_concurrent:
            max_concurrent = current
        await asyncio.sleep(0.01)
        current -= 1

    await gather_with_concurrency(
        2, track(), track(), track(), track(),
    )
    assert max_concurrent <= 2


@pytest.mark.asyncio
async def test_gather_with_concurrency_single():
    """Works with a single coroutine."""
    async def one():
        return 42

    results = await gather_with_concurrency(1, one())
    assert results == [42]
