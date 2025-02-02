import functools
import logging
from time import time
from typing import Callable, Any

logger = logging.getLogger(__name__)


def log_execution(func: Callable) -> Callable:
    """Decorator to log function execution time and status"""

    @functools.wraps(func)
    async def async_wrapper(*args, **kwargs) -> Any:
        start = time()
        try:
            result = await func(*args, **kwargs)
            elapsed = time() - start
            logger.info(f"{func.__name__} completed in {elapsed:.2f} seconds")
            return result
        except Exception as e:
            elapsed = time() - start
            logger.error(
                f"{func.__name__} failed after {elapsed:.2f} seconds: {str(e)}"
            )
            raise

    @functools.wraps(func)
    def sync_wrapper(*args, **kwargs) -> Any:
        start = time()
        try:
            result = func(*args, **kwargs)
            elapsed = time() - start
            logger.info(f"{func.__name__} completed in {elapsed:.2f} seconds")
            return result
        except Exception as e:
            elapsed = time() - start
            logger.error(
                f"{func.__name__} failed after {elapsed:.2f} seconds: {str(e)}"
            )
            raise

    return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
