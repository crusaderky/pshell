"""Functions to open file descriptors"""

from __future__ import annotations

import os.path
import sys
from collections.abc import Callable
from pathlib import Path
from typing import IO, Any, BinaryIO, Literal

from pshell import log
from pshell.env import resolve_env

__all__ = ("pshell_open",)


_HAS_PY314 = sys.version_info >= (3, 14)


# When importing in __init__, we're going to rename pshell_open to just open
def pshell_open(
    file: str | Path | int | BinaryIO,
    mode: str = "r",
    *,
    encoding: str | None = None,
    errors: str | None = None,
    compression: Literal[
        False, "gzip", "bzip2", "lzma", "zstd", "zstandard", "auto"
    ] = "auto",
    **kwargs: Any,
) -> IO:
    """Open a file handle to target file name or file descriptor.

    Unlike the builtin function, this wrapper:

    - performs automatic environment variable resolution in the file name
    - logs the file access
    - supports automatic compression/decompression

    :param file:
        Path to the file to be opened or file descriptor to be wrapped.
        If compression is set to 'auto', 'gzip', 'bzip2', 'lzma', 'zstd', or
        'zstandard', `file` can also be a binary file handle.
    :param str mode:
        As in the builtin :func:`open` function. It always defaults to text
        mode unless 'b' is explicitly specified; this is unlike
        :func:`gzip.open`, :func:`bz2.open`, :func:`lzma.open`, or
        :func:`compression.zstd.open`  which instead default to binary mode.
    :param str encoding:
        Character encoding when in text mode. Unlike the builtin :func:`open`
        function, it always defaults to utf-8 instead of being
        platform-specific.
    :param str errors:
        As in the builtin :func:`open` function, but it defaults to ``replace``
        instead of ``strict``.
    :param compression:
        One of:

        False
            No compression (use builtin :func:`open`)
        ``gzip``
            gzip compression (use :func:`gzip.open`)
        ``bzip2``
            bzip2 compression (use :func:`bz2.open`)
        ``lzma``
            lzma compression (use :func:`lzma.open`)
        ``zstd``, ``zstandard``
            zstd compression (use :func:`compression.zstd.open`).
            Requires either Python 3.14+ or the ``backports.zstd`` package.
        ``auto`` *(default)*:
            Automatically set compression if the file extension is ``.gz``,
            ``.bz2``, ``.xz``, ``.zst``, or ``.zstd`` (case insensitive)
    :param kwargs:
        Passed verbatim to the underlying open function
    """
    # Build log message and override default mode, encoding and errors
    if "b" in mode:
        mode_label = "binary "
    else:
        # Default to text mode if the user doesn't specify text or binary. This
        # overrides gzip.open, bz2.open, lzma.open, compression.zstd.open
        # which default to binary.
        if "t" not in mode:
            mode += "t"

        mode_label = ""
        if encoding is None:
            encoding = "utf-8"
        if errors is None:
            errors = "replace"

    if "w" in mode:
        mode_label += "write"
    elif "x" in mode:
        mode_label += "exclusive create"
    elif "a" in mode:
        mode_label += "append"
    else:
        mode_label += "read"

    # Parse compression
    if compression == "auto":
        if isinstance(file, (str, Path)):
            _, ext = os.path.splitext(str(file))
            ext = ext.lower()

            if ext == ".gz":
                compression = "gzip"
            elif ext == ".bz2":
                compression = "bzip2"
            elif ext == ".xz":
                compression = "lzma"
            elif ext in (".zst", ".zstd"):
                compression = "zstd"
            else:
                compression = False
        else:
            compression = False
    elif compression == "zstandard":
        compression = "zstd"

    if compression:
        compress_label = f" ({compression} compression)"
    else:
        compress_label = ""

    # resolve env variables and write log message.
    if isinstance(file, (str, Path)):
        log.info(
            "Opening '%s' for %s%s", file, mode_label, compress_label, stacklevel=2
        )
        file = resolve_env(file)
    elif isinstance(file, int):
        if compression:
            raise TypeError("compression not supported when opening a file descriptor")
        log.info("Opening file descriptor %d for %s", file, mode_label, stacklevel=2)
    else:
        log.info(
            "Opening file handle for %s%s%s",
            file,
            mode_label,
            compress_label,
            stacklevel=2,
        )

    open_func: Callable[..., IO]
    if compression is False:
        open_func = open
    elif compression == "gzip":
        if _HAS_PY314:
            from compression import gzip  # noqa: PLC0415
        else:
            import gzip  # noqa: PLC0415

        open_func = gzip.open
    elif compression == "bzip2":
        if _HAS_PY314:
            from compression import bz2  # noqa: PLC0415
        else:
            import bz2  # noqa: PLC0415

        open_func = bz2.open
    elif compression == "lzma":
        if _HAS_PY314:
            from compression import lzma  # noqa: PLC0415
        else:
            import lzma  # noqa: PLC0415

        open_func = lzma.open
    elif compression == "zstd":
        if _HAS_PY314:
            from compression import zstd  # noqa: PLC0415
        else:
            # Optional dependency; will raise ImportError if not installed
            from backports import zstd  # noqa: PLC0415

        open_func = zstd.open
    else:
        raise ValueError(
            "compression must be False, 'auto', 'gzip', 'bzip2', 'lzma', "
            "'zstd', or 'zstandard'"
        )

    return open_func(file, mode, encoding=encoding, errors=errors, **kwargs)  # type: ignore[arg-type]
