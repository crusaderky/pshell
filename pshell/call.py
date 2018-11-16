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
    """The :mod:`io` module offers file-like objects which can be used to spoof
    a file handle. Among other things, they are extensively used by nosetests
    and py.test to capture stdout/stderr.

    In most cases, this is transparent; however there are exceptions, like
    the :mod:`subprocess` module, which require a file handle with a real
    file descriptor underlying it - that is, an object which defines the
    ``fileno()`` method.

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

      buf = io.StringIO()
      with real_fh(buf) as real_buf:
          subprocess.check_call(cmd, stderr=real_buf)

    All pshell functions that wrap around :mod:`subprocess` internally use this
    context manager. You don't need to use it explicitly::

      buf = io.StringIO()
      pshell.check_call(cmd, stderr=buf)
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
    """Common internal helper of check_call, call, and check_output
    that pre-processes the command to be executed
    """
    log_cmd = cmd
    if not isinstance(log_cmd, str):
        log_cmd = '"' + '" "'.join(log_cmd) + '"'
    if obfuscate_pwd:
        log_cmd = log_cmd.replace(obfuscate_pwd, 'XXXX')
    if shell:
        if not isinstance(cmd, str):
            raise ValueError("cmd must be a string when shell=True")
        if os.name != 'nt':
            cmd = ['bash', '-c',
                   'set -o errexit; set -o nounset; set -o pipefail; ' + cmd]
            shell = False

    logging.info("Executing: %s", log_cmd)
    return cmd, shell


def call(cmd, *, stdout=None, stdin=None, stderr=None, obfuscate_pwd=None,
         shell=True, timeout=None):
    """Run another program in a subprocess and wait for it to terminate.

    :param cmd:
        Command to be executed (str or list). If shell=True, it must be a str.
    :param stdout:
        standard output file handle. Omit for sys.stdout.
        Unlike the same parameter for :func:`subprocess.call`, which must be
        backed by a OS-level file descriptor, this can be a
        pseudo-stream like e.g. :class:`io.StringIO`.
    :param stdin:
        standard input file handle. Omit for no input.
    :param stderr:
        standard error file handle. Omit for sys.stderr.
        Unlike the same parameter for :func:`subprocess.call`, which must be
        backed by a OS-level file descriptor, this can be a
        pseudo-stream like e.g. :class:`io.StringIO`.
    :param str obfuscate_pwd:
        if set, search for the target password and replace it with XXXX
        before logging it.
    :param bool shell:
        Invoke inside the shell. This differes from the same parameter of
        :func:`subprocess.call` in several ways:

        - It is True by default instead of False
        - In Linux and MacOSX, it sets some sane settings:
          errexit, nounset, pipefail
        - In Linux and MacOSX, it is always guaranteed to be bash.
          This differs from :func:`subprocess.call`, which on Ubuntu will
          invoke dash and RedHat will invoke bash.
          On Windows it is CMD.

    :param float timeout:
        kill command if doesn't return within timeout limit
    :returns:
        command exit code
    :rtype:
        int
    """
    cmd, shell = _call_cmd(cmd, obfuscate_pwd, shell)
    with real_fh(stdout) as rstdout, real_fh(stderr) as rstderr:
        return subprocess.call(cmd, stdin=stdin, stdout=rstdout,
                               stderr=rstderr, timeout=timeout, shell=shell)


def check_call(cmd, *, stdin=None, stdout=None, stderr=None,
               obfuscate_pwd=None, shell=True, timeout=None):
    """Run another program in a subprocess and wait for it to terminate; raise
    exception in case of non-zero exit code.

    See :func:`call` for parameters documentation.

    :returns:
        None
    :raise CalledProcessError:
        if the command returns a non-zero exit code
    """
    cmd, shell = _call_cmd(cmd, obfuscate_pwd, shell)
    with real_fh(stdout) as rstdout, real_fh(stderr) as rstderr:
        subprocess.check_call(cmd, stdin=stdin, stdout=rstdout,
                              stderr=rstderr, timeout=timeout, shell=shell)


def check_output(cmd, *, stdin=None, stderr=None, obfuscate_pwd=None,
                 shell=True, timeout=None,
                 decode=True, encoding='utf-8', errors='replace'):
    """Run another program in a subprocess and wait for it to terminate; return
    its stdout. Raise exception in case of non-zero exit code.

    See :func:`call` for parameters documentation.

    :param bool decode:
        If True, decode the raw output to UTF-8 and return a str object.
        If False, return the raw bytes object.
        The default is to decode to UTF-8. This differs
        from :func:`subprocess.check_output`, which always returns the raw
        output.
    :param str encoding:
        Encoding of the raw bytes output. Ignored if decode=False.
    :param str errors:
        'replace', 'ignore', or 'strict'. See :meth:`str.decode`.
        Ignored if decode=False. Note that the default value is ``replace``,
        whereas the default in :meth:`bytes.decode` is ``strict``.
    :returns:
        command stdout
    :rtype:
        str or bytes (see ``decode`` parameter)
    :raise CalledProcessError:
        if the command returns a non-zero exit code
    """
    cmd, shell = _call_cmd(cmd, obfuscate_pwd, shell)
    with real_fh(stderr) as rstderr:
        raw_output = subprocess.check_output(
            cmd, stdin=stdin, stderr=rstderr, timeout=timeout, shell=shell)

    if decode:
        return raw_output.decode(encoding=encoding, errors=errors)
    return raw_output
