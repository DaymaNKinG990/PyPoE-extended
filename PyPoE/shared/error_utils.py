"""
Error handling utilities - centralized error handling and decorators.

This module provides reusable error handling patterns and decorators
to eliminate code duplication and ensure consistent error handling.
"""

import functools
import traceback
from collections.abc import Callable
from typing import Any, TypeVar, cast

from PyPoE.shared.logging import get_logger

logger = get_logger(__name__)

F = TypeVar("F", bound=Callable[..., Any])


def handle_file_errors(reraise: bool = True) -> Callable[[F], F]:
    """
    Decorator to handle file-related errors with logging.

    Args:
        reraise: Whether to re-raise the exception after logging (default: True)

    Returns:
        Decorated function

    Example:
        @handle_file_errors(reraise=True)
        def read_dat_file(path: str) -> bytes:
            with open(path, 'rb') as f:
                return f.read()
    """

    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                return func(*args, **kwargs)
            except FileNotFoundError as e:
                logger.error(f"{func.__name__}: File not found - {e}")
                if reraise:
                    raise
                return None
            except PermissionError as e:
                logger.error(f"{func.__name__}: Permission denied - {e}")
                if reraise:
                    raise
                return None
            except OSError as e:
                logger.error(f"{func.__name__}: OS error - {e}")
                if reraise:
                    raise
                return None
            except Exception as e:
                logger.error(
                    f"{func.__name__}: Unexpected error - {e}\n{traceback.format_exc()}"
                )
                if reraise:
                    raise
                return None

        return cast(F, wrapper)

    return decorator


def handle_parser_errors(default_value: Any = None, reraise: bool = False) -> Callable[[F], F]:
    """
    Decorator to handle parser-related errors with logging.

    Args:
        default_value: Value to return on error (if not reraising)
        reraise: Whether to re-raise the exception after logging (default: False)

    Returns:
        Decorated function

    Example:
        @handle_parser_errors(default_value=[], reraise=False)
        def parse_items(data: bytes) -> list:
            return parse(data)
    """

    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                return func(*args, **kwargs)
            except (ValueError, KeyError, IndexError) as e:
                logger.error(f"{func.__name__}: Parsing error - {e}")
                if reraise:
                    raise
                return default_value
            except Exception as e:
                logger.error(
                    f"{func.__name__}: Unexpected parser error - {e}\n{traceback.format_exc()}"
                )
                if reraise:
                    raise
                return default_value

        return cast(F, wrapper)

    return decorator


def handle_errors(
    exceptions: tuple[type[Exception], ...] = (Exception,),
    default_value: Any = None,
    log_level: str = "error",
    reraise: bool = True,
) -> Callable[[F], F]:
    """
    Generic error handler decorator with configurable behavior.

    Args:
        exceptions: Tuple of exception types to catch
        default_value: Value to return on error (if not reraising)
        log_level: Logging level ("debug", "info", "warning", "error", "critical")
        reraise: Whether to re-raise the exception after logging

    Returns:
        Decorated function

    Example:
        @handle_errors(
            exceptions=(KeyError, ValueError),
            default_value={},
            log_level="warning",
            reraise=False
        )
        def get_config(key: str) -> dict:
            return config[key]
    """

    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                return func(*args, **kwargs)
            except exceptions as e:
                log_func = getattr(logger, log_level, logger.error)
                log_func(
                    f"{func.__name__}: Error - {e.__class__.__name__}: {e}\n"
                    f"{traceback.format_exc()}"
                )
                if reraise:
                    raise
                return default_value

        return cast(F, wrapper)

    return decorator


def log_exceptions(log_level: str = "error") -> Callable[[F], F]:
    """
    Decorator to log exceptions without catching them.

    Args:
        log_level: Logging level ("debug", "info", "warning", "error", "critical")

    Returns:
        Decorated function

    Example:
        @log_exceptions(log_level="warning")
        def risky_operation(x: int) -> int:
            return 1 / x  # Will log and raise ZeroDivisionError
    """

    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                return func(*args, **kwargs)
            except Exception as e:
                log_func = getattr(logger, log_level, logger.error)
                log_func(
                    f"{func.__name__}: Exception raised - {e.__class__.__name__}: {e}\n"
                    f"{traceback.format_exc()}"
                )
                raise

        return cast(F, wrapper)

    return decorator


def retry_on_error(
    retries: int = 3, delay: float = 0.1, exceptions: tuple[type[Exception], ...] = (Exception,)
) -> Callable[[F], F]:
    """
    Decorator to retry function on error.

    Args:
        retries: Number of retry attempts
        delay: Delay between retries in seconds
        exceptions: Tuple of exception types to catch and retry

    Returns:
        Decorated function

    Example:
        @retry_on_error(retries=3, delay=0.5, exceptions=(OSError,))
        def download_file(url: str) -> bytes:
            return requests.get(url).content
    """
    import time

    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            last_exception = None
            for attempt in range(retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < retries:
                        logger.warning(
                            f"{func.__name__}: Attempt {attempt + 1}/{retries + 1} failed - {e}. "
                            f"Retrying in {delay}s..."
                        )
                        time.sleep(delay)
                    else:
                        logger.error(
                            f"{func.__name__}: All {retries + 1} attempts failed - {e}"
                        )
            raise last_exception  # type: ignore[misc]

        return cast(F, wrapper)

    return decorator


class ErrorContext:
    """
    Context manager for handling errors with custom behavior.

    Example:
        with ErrorContext("Reading config", reraise=False):
            config = read_config()
    """

    def __init__(
        self,
        operation_name: str,
        reraise: bool = True,
        log_level: str = "error",
    ):
        """
        Initialize error context.

        Args:
            operation_name: Name of the operation for logging
            reraise: Whether to re-raise exceptions
            log_level: Logging level for errors
        """
        self.operation_name = operation_name
        self.reraise = reraise
        self.log_level = log_level
        self.exception: Exception | None = None

    def __enter__(self) -> "ErrorContext":
        """Enter context."""
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: Any,
    ) -> bool:
        """
        Exit context.

        Returns:
            True if exception should be suppressed, False otherwise
        """
        if exc_type is not None:
            self.exception = exc_val  # type: ignore[assignment]
            log_func = getattr(logger, self.log_level, logger.error)
            log_func(
                f"{self.operation_name}: {exc_type.__name__}: {exc_val}\n"
                f"{''.join(traceback.format_tb(exc_tb))}"
            )
            return not self.reraise
        return False


def format_exception(exc: Exception) -> str:
    """
    Format exception with traceback for logging.

    Args:
        exc: Exception to format

    Returns:
        Formatted exception string
    """
    return f"{exc.__class__.__name__}: {exc}\n{''.join(traceback.format_tb(exc.__traceback__))}"

