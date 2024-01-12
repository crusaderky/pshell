"""Functions and global variables related to logging
"""
from __future__ import annotations

from contextvars import ContextVar
from logging import Logger, getLogger
from typing import Any

_global_logger: Logger | None = None

context_logger: ContextVar[Logger | None] = ContextVar("context_logger", default=None)


def set_global_logger(logger: Logger | str | None) -> Logger | None:
    """Set the pshell global logger. This logger will be used by all pshell functions
    unless ``context_logger`` is defined.

    :returns:
        Previous global logger
    """
    global _global_logger

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
    elif _global_logger:
        return _global_logger
    else:
        return getLogger("pshell")


def debug(msg: str, *args: Any, **kwargs: Any) -> None:
    """Wrapper around :meth:`logging.Logger.debug` which uses the logger returned by
    :func:`~pshell.get_logger`.
    """
    get_logger().debug(msg, *args, **kwargs)


def info(msg: str, *args: Any, **kwargs: Any) -> None:
    """Wrapper around :meth:`logging.Logger.info` which uses the logger returned by
    :func:`~pshell.get_logger`.
    """
    get_logger().info(msg, *args, **kwargs)


def warning(msg: str, *args: Any, **kwargs: Any) -> None:
    """Wrapper around :meth:`logging.Logger.warning` which uses the logger returned by
    :func:`~pshell.get_logger`.
    """
    get_logger().warning(msg, *args, **kwargs)


def error(msg: str, *args: Any, **kwargs: Any) -> None:
    """Wrapper around :meth:`logging.Logger.error` which uses the logger returned by
    :func:`~pshell.get_logger`.
    """
    get_logger().error(msg, *args, **kwargs)


def critical(msg: str, *args: Any, **kwargs: Any) -> None:
    """Wrapper around :meth:`logging.Logger.critical` which uses the logger returned by
    :func:`~pshell.get_logger`.
    """
    get_logger().critical(msg, *args, **kwargs)
