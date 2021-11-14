from functools import partial
from typing import Any, Awaitable, Callable

from . import xbot


def run_sync(func: Callable[..., Any]) -> Awaitable[Any]:
    """Runs the given sync function (optionally with arguments) on a separate thread."""

    async def wrapper(*args: Any, **kwargs: Any):
        return await xbot.loop.run_in_executor(None, partial(func, *args, **kwargs))

    return wrapper
