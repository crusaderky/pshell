"""Functions to open file descriptors
"""
import logging
import os.path
from .env import resolve_env


__all__ = ('pshell_open', )


# When importing in __init__, we're going to rename pshell_open to just
# open
def pshell_open(file, mode='r', *, encoding=None, errors=None,
                compression='auto', **kwargs):
    """Open a file handle to target file name or file descriptor.

    Unlike the builtin function, this wrapper:

    - performs automatic environment variable resolution in the file name
    - logs the file access
    - supports transparent compression

    :param str mode:
        As in the builtin :func:`open` function. It always defaults to text
        mode unless 'b' is explicitly specified; this is unlike
        :func:`gzip.open`, :func:`bz2.open`, and :func:`lzma.open` which
        instead default to binary mode.
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
        'gzip'
            gzip compression (use :func:`gzip.open`)
        'bzip2':
            bzip2 compression (use :func:`bz2.open`)
        'lzma':
            lzma compression (use :func:`lzma.open`)
        'auto':
            Automatically set compression if the file extension is ``.gz``,
            ``.bz2``, or ``.xz`` (case insensitive)
    :param kwargs:
        Passed verbatim to the underlying open function
    """
    # Build log message and override default mode, encoding and errors
    if 'b' in mode:
        mode_label = 'binary '
    else:
        # Default to text mode if the user doesn't specify text or binary. This
        # overrides gzip.open, bz2.open, lzma.open which default to binary.
        if 't' not in mode:
            mode += 't'

        mode_label = ''
        if encoding is None:
            encoding = 'utf-8'
        if errors is None:
            errors = 'replace'

    if 'w' in mode:
        mode_label += 'write'
    elif 'x' in mode:
        mode_label += 'exclusive create'
    elif 'a' in mode:
        mode_label += 'append'
    else:
        mode_label += 'read'

    # Parse compression
    if compression == 'auto':
        if isinstance(file, str):
            _, ext = os.path.splitext(file)
            ext = ext.lower()

            if ext == '.gz':
                compression = 'gzip'
            elif ext == '.bz2':
                compression = 'bzip2'
            elif ext == '.xz':
                compression = 'lzma'
            else:
                compression = False
        else:
            compression = False

    if compression:
        compress_label = ' (%s compression)' % compression
    else:
        compress_label = ''

    # resolve env variables and write log message.
    if isinstance(file, str):
        logging.info("Opening '%s' for %s%s", file, mode_label, compress_label)
        file = resolve_env(file)
    elif isinstance(file, int):
        if compression:
            raise ValueError("compression not supported when opening a "
                             "file descriptor")
        logging.info("Opening file descriptor %d for %s", file, mode_label)
    else:
        logging.info("Opening file handle for %s%s%s",
                     file, mode_label, compress_label)

    if compression is False:
        open_func = open
    elif compression == 'gzip':
        import gzip
        open_func = gzip.open
    elif compression == 'bzip2':
        import bz2
        open_func = bz2.open
    elif compression == 'lzma':
        import lzma
        open_func = lzma.open
    else:
        raise ValueError("compression must be False, 'auto', 'gzip', 'bzip2', "
                         "or 'lzma'")

    return open_func(file, mode, encoding=encoding, errors=errors, **kwargs)
