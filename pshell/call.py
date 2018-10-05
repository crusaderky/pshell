"""Functions to execute shell commands in a subprocess
"""
import io
import logging
import os
import threading
import subprocess
from contextlib import contextmanager


__all__ = ('real_fh', 'call', 'check_call', 'check_output')

_BASH_INIT = "set -o errexit -o pipefail -o nounset && "
"""Sane initialization string for new bash instances.
Set errexit, pipefail, and nounset.
"""


@contextmanager
def real_fh(fh):
    """With the :mod:`io` module, Python offers file-like objects which
    can be used to spoof a file handle. For example, this is extensively
    used by nosetests to capture stdout/stderr.

    In most cases, this is transparent; however there are exceptions, like
    the :mod:`subprocess` module, which require a file handle with a real
    file descriptor underlying it - that is, an object which defines the
    fileno() method.

    This context manager transparently detects these cases and automatically
    converts pseudo file handlers from the :mod:`io` module into real
    POSIX-based file handles.

    :param fh:
        Any of:

        - A file handle opened for write and backed by a POSIX file descriptor,
          e.g. as returned by :func:`open` or the default value of `sys.stdout`
          or `sys.stderr`.
        - A pseudo file handle such as :class:`io.StringIO`,
          :class:`io.BytesIO`, or the stub used by :mod:`nosetests` to mock
          `sys.stdout` and `sys.stderr`.
        - None (default for most subprocess functions)

    Usage::

      with real_fh(sys.stdout) as real_stdout:
          check_call(cmd, stdout=real_stdout)
    """
    if fh is None:
        yield fh
        return

    try:
        fh.fileno()
    except (AttributeError, OSError, io.UnsupportedOperation):
        pass
    else:
        # File handle is backed by POSIX file descriptor
        yield fh
        return

    # File handle isn't backed by POSIX fd

    # Detect if it's a text or binary file handle
    try:
        fh.write('')
        bin_flag = ''
    except TypeError:
        fh.write(b'')
        bin_flag = 'b'

    # 1. Create a pipe
    # 2. pass its write end to the context
    # 3. read from its read end
    # 4. dump contents into the pseudo file handle
    fd_in, fd_out = os.pipe()
    real_fh_in = open(fd_in, 'r' + bin_flag, closefd=True)
    real_fh_out = open(fd_out, 'w' + bin_flag, closefd=True)

    # The size of a pipe is 64 kbytes on Linux.
    # If you try writing more than that without reading from the other
    # side, the write will lock indefinitely, resulting in a deadlock.
    # It's very easy to exceed this limit, e.g. when calling sh.check_call().
    # Use a thread to continuously move data beetween file handles.
    def flush():
        while True:
            data = real_fh_in.read(4096)
            if not data:
                # real_fh_out has been closed and the pipe is empty
                break
            fh.write(data)

    flusher = threading.Thread(target=flush)
    flusher.start()

    try:
        yield real_fh_out
    finally:
        # Cause real_fh_in.read(4096) to return '' inside the flush
        # thread, instead of blocking and waiting for more data
        real_fh_out.close()
        # Wait for the pipe to be completeley emptied
        flusher.join()
        real_fh_in.close()


def _call_cmd(cmd, obfuscate_pwd, shell):
    """Common internal method of check_call, call, and check_output
    that pre-processes the command to be executed
    """
    log_cmd = cmd
    if not isinstance(log_cmd, str):
        log_cmd = '"' + '" "'.join(log_cmd) + '"'
    if obfuscate_pwd:
        log_cmd = log_cmd.replace(obfuscate_pwd, 'XXXX')
    if shell:
        cmd = _BASH_INIT + cmd

    logging.info("Executing: %s", log_cmd)
    return cmd


def call(cmd, *, stdout=None, stdin=None, stderr=None, obfuscate_pwd=None,
         shell=True, timeout=None):
    """Run a Linux command.

    The command is invoked with the errexit, pipefail, nounset bash switches.

    :param str obfuscate_pwd:
        if not None, search for the target password and replace it with XXXX
        before logging it.
    :param bool shell:
        Invoke inside bash. Note that the default is True, while in
        subprocess.*call it's False.
    :param int timeout:
        kill command if doesn't return within timeout limit
    :returns:
        command exit code
    :rtype:
        int
    """
    cmd = _call_cmd(cmd, obfuscate_pwd, shell)
    with real_fh(stdout) as rstdout, real_fh(stderr) as rstderr:
        return subprocess.call(cmd, shell=shell, stdin=stdin, stdout=rstdout,
                               stderr=rstderr, timeout=timeout)


def check_call(cmd, *, stdin=None, stdout=None, stderr=None,
               obfuscate_pwd=None, shell=True, timeout=None):
    """Run a Linux command.

    The command is invoked with the errexit, pipefail, nounset bash switches.

    :param str obfuscate_pwd:
        Search for the target password and replace it with XXXX
        before logging it.
    :param bool shell:
        Invoke inside bash. Note that the default is True, while in
        subprocess.*call it's False.
    :param int timeout:
        kill command if doesn't return within timeout limit
    :raise CalledProcessError:
        if the command returns with non-zero exit status
    """
    cmd = _call_cmd(cmd, obfuscate_pwd, shell)
    with real_fh(stdout) as rstdout, real_fh(stderr) as rstderr:
        subprocess.check_call(cmd, shell=shell, stdin=stdin, stdout=rstdout,
                              stderr=rstderr, timeout=timeout)


def check_output(cmd, *, stdin=None, stderr=None, obfuscate_pwd=None,
                 shell=True, timeout=None,
                 decode=True, errors='replace'):
    """Run a Linux command and return stdout.

    The command is invoked with the errexit, pipefail, nounset bash switches.

    :param str obfuscate_pwd:
        Search for the target password and replace it with XXXX
        before logging it.
    :param bool shell:
        Invoke inside bash. Note that the default is True, while in
        subprocess.*call it's False.
    :param int timeout:
        kill command if doesn't return within timeout limit. If the timeout
        expires, the child process will be killed and then waited for again.
        The TimeoutExpired exception will be re-raised after the child process
        has terminated.

        .. note::
           When using shell=True, the timeout will not work.

    :param bool decode:
        If True, decode the raw output to UTF-8 and return a str object.
        If False, return the raw bytes object.
        The default is to decode to UTF-8. Note how this differes
        from :func:`subprocess.check_output`.
    :param str errors:
        'replace', 'ignore', or 'strict'. See :meth:`str.decode`
    :returns:
        command stdout
    :rtype:
        str or bytes (see decode parameter)
    :raise CalledProcessError:
        if the command returns with non-zero exit status
    """
    cmd = _call_cmd(cmd, obfuscate_pwd, shell)
    with real_fh(stderr) as rstderr:
        raw_output = subprocess.check_output(
            cmd, shell=shell, stdin=stdin, stderr=rstderr, timeout=timeout)

    if decode:
        return raw_output.decode('utf-8', errors=errors)
    return raw_output
