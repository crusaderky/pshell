"""Functions and global variables related to logging"""

from __future__ import annotations

import contextlib
from collections.abc import Generator
from contextvars import ContextVar
from logging import Logger, getLogger
from typing import Any

__all__ = (
    "context_logger",
    "critical",
    "debug",
    "error",
    "get_logger",
    "inc_stacklevel",
    "info",
    "set_global_logger",
    "warning",
)

_global_logger: Logger | None = None

context_logger: ContextVar[Logger | None] = ContextVar("context_logger", default=None)
_inc_stacklevel: ContextVar[int] = ContextVar("_inc_stacklevel", default=1)


def set_global_logger(logger: Logger | str | None) -> Logger | None:
    """Set the pshell global logger. This logger will be used by all pshell functions
    unless ``context_logger`` is defined.

    :returns:
        Previous global logger (not thread-safe).
    """
    global _global_logger  # noqa: PLW0603

    prev = _global_logger
    if isinstance(logger, str):
        logger = getLogger(logger)
    _global_logger = logger
    return prev


def get_logger() -> Logger:
    """
    #. If ``context_logger`` is set, return it.
    #. Otherwise, if :func:`set_global_logger` was called, return the global logger.
    #. Otherwise, return the **pshell** logger.
    """
    ctx = context_logger.get()
    if ctx:
        return ctx
    if _global_logger:
        return _global_logger
    return getLogger("pshell")


@contextlib.contextmanager
def inc_stacklevel(levels: int = 2) -> Generator[None]:
    """Function decorator to be added to helper functions.
    Will cause all log messages to be logged as if they were emitted
    by the function's caller instead of the function itself.

    :param levels:
        Number of stack levels to increase. Default: 2 (1 for contextlib, 1 for the
        decorated function)

    Example:

    >>> @sh.log.inc_stacklevel()
    >>> def f():
    ...     sh.log.info("This is logged as coming from g()")
    >>> def g():
    ...     f()
    """
    prev = _inc_stacklevel.get()
    tok = _inc_stacklevel.set(prev + levels)
    try:
        yield
    finally:
        _inc_stacklevel.reset(tok)


def debug(msg: str, *args: Any, stacklevel: int = 1, **kwargs: Any) -> None:
    """Wrapper around :meth:`logging.Logger.debug` which uses the logger set by
    :func:`~pshell.set_global_logger` or by :attr:`~pshell.context_logger`.
    """
    stacklevel += _inc_stacklevel.get()
    get_logger().debug(msg, *args, stacklevel=stacklevel, **kwargs)


def info(msg: str, *args: Any, stacklevel: int = 1, **kwargs: Any) -> None:
    """Wrapper around :meth:`logging.Logger.info` which uses the logger set by
    :func:`~pshell.set_global_logger` or by :attr:`~pshell.context_logger`.
    """
    stacklevel += _inc_stacklevel.get()
    get_logger().info(msg, *args, stacklevel=stacklevel, **kwargs)


def warning(msg: str, *args: Any, stacklevel: int = 1, **kwargs: Any) -> None:
    """Wrapper around :meth:`logging.Logger.warning` which uses the logger set by
    :func:`~pshell.set_global_logger` or by :attr:`~pshell.context_logger`.
    """
    stacklevel += _inc_stacklevel.get()
    get_logger().warning(msg, *args, stacklevel=stacklevel, **kwargs)


def error(msg: str, *args: Any, stacklevel: int = 1, **kwargs: Any) -> None:
    """Wrapper around :meth:`logging.Logger.error` which uses the logger set by
    :func:`~pshell.set_global_logger` or by :attr:`~pshell.context_logger`.
    """
    stacklevel += _inc_stacklevel.get()
    get_logger().error(msg, *args, stacklevel=stacklevel, **kwargs)


def critical(msg: str, *args: Any, stacklevel: int = 1, **kwargs: Any) -> None:
    """Wrapper around :meth:`logging.Logger.critical` which uses the logger set by
    :func:`~pshell.set_global_logger` or by :attr:`~pshell.context_logger`.
    """
    stacklevel += _inc_stacklevel.get()
    get_logger().critical(msg, *args, stacklevel=stacklevel, **kwargs)
