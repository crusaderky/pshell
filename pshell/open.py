"""Functions to open file descriptors
"""
import logging
import gzip
from .env import resolve_env


__all__ = ('open', 'gzip_open')


# We're going to override function open - need to preserve the original one.
_open_builtin = open


def _parse_mode(mode, encoding=None, errors=None):
    """Helper function of :func:`open` and :func:`gzip_open`.
    Parse file open mode to format logging message, and tweak encoding and
    errors parameters.

    :param str mode:
        file open mode can be one of 'r', 'rb', 'a', 'ab', 'w', 'wb',
        'x' or 'xb' for binary mode, or 'rt', 'at', 'wt', or 'xt'
    :param str encoding:
        charset used to decode or encode the file
    :param str errors:
        errors specifies how encoding errors are handled and should not be
        used in binary mode. Pass 'strict' to raise exception, 'replace',
        'backslashreplace', to replace characters or 'ignore' to ignore errors

    :returns: mode_label, encoding and errors
    """
    if 'b' in mode:
        mode_label = 'binary '
    else:
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
    return mode_label, encoding, errors


def open(file, mode='r', *, buffering=-1, encoding=None, errors=None,
         newline=None, closefd=True, opener=None):
    """Open a file handle to target file name or file descriptor.

    Unlike the builtin function, this wrapper performs automatic environment
    variable resolution in the file name and automatically logs the file
    access.

    All parameters are as in the builtin open function, with the following
    exceptions:

    - ``encoding`` always defaults to utf-8 instead of being platform-specific
    - ``errors`` default to ``replace`` instead of ``strict``
    """
    mode_label, encoding, errors = _parse_mode(mode, encoding, errors)

    # Don't accidentally pass a file descriptor to resolve_env
    if isinstance(file, str):
        logging.info("Opening '%s' for %s", file, mode_label)
        file = resolve_env(file)
    else:
        assert isinstance(file, int)
        logging.info("Opening file descriptor %d for %s", file, mode_label)

    return _open_builtin(file, mode=mode, buffering=buffering,
                         encoding=encoding, errors=errors, newline=newline,
                         closefd=closefd, opener=opener)


def gzip_open(filename, mode='r', *, compresslevel=9, encoding=None,
              errors=None, newline=None):
    """Open a gzip-compressed file in binary or text mode, returning a file
    object.

    Unlike :func:`gzip.open`, this wrapper performs automatic environment
    variable resolution in the file name and automatically logs file access.

    All parameters are as in :func:`gzip.open`, with the following exceptions:

    - the first parameter must be a file name; file handles are not supported
    - this function inspects the filename, and intelligently reverts to
      :func:`open` if the filename does not end with '.gz'.
    - defaults to text mode instead of binary mode
    - character encoding always defaults to utf-8 instead of being
      platform-specific
    - charset decoding errors default to ``replace`` instead of ``strict``
    """
    mode_label, encoding, errors = _parse_mode(mode, encoding, errors)

    assert isinstance(filename, str)
    if filename.endswith('.gz'):
        # Default to text mode if the user doesn't specify text or binary
        if 't' not in mode and 'b' not in mode:
            mode += 't'
        logging.info("Opening gzip %s for %s", filename, mode_label)
        filename = resolve_env(filename)
        return gzip.open(filename, mode, compresslevel=compresslevel,
                         encoding=encoding, errors=errors, newline=newline)

    return open(filename, mode, encoding=encoding, errors=errors,
                newline=newline)
