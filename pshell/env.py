"""Functions related to environment variables"""

from __future__ import annotations

import os
import string
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import IO, overload

from pshell import log
from pshell.call import check_output

__all__ = ("override_env", "putenv", "resolve_env", "source")


@log.inc_stacklevel()
def source(bash_file: str | Path, *, stderr: IO | None = None) -> None:
    """Emulate the bash command ``source <bash_file>``.
    The stdout of the command, if any, will be redirected to stderr.
    The acquired variables are injected into ``os.environ`` and are
    exposed to any subprocess invoked afterwards.

    .. note::
        This function is not available on Windows.

        The script is always executed with bash. This includes when running in
        Ubuntu and derivatives, where /bin/sh is actually dash.

        The script is run with errexit, pipefail, nounset.

    :param bash_file:
        Path to the bash file. It can contain environment variables.
    :param stderr:
        standard error file handle. Omit for sys.stderr.
        Unlike the same parameter for :func:`subprocess.call`, which must be
        backed by a OS-level file descriptor, this can be a
        pseudo-stream like e.g. :class:`io.StringIO`.
    :raise CalledProcessError:
        if the command returns with non-zero exit status
    """
    log.info("Sourcing environment variables from %s", bash_file)

    # Thread safety: spawn a bash subprocess, make it sample the previous
    # environment, run the script and sample again.
    delim = "!!!pshell-source-delimiter!!!"
    stdout = check_output(
        f'env && echo {delim} && source "{bash_file}" 1>&2 && env', stderr=stderr
    )

    is_prev = True
    prev_env = {}
    for line in stdout.splitlines():
        if line == delim:
            is_prev = False
            continue
        (key, _, value) = line.partition("=")
        if key in ("_", "", "SHLVL"):
            continue
        if is_prev:
            prev_env[key] = value
        elif prev_env.get(key) != value:
            log.debug("Setting environment variable: %s=%s", key, value)
            os.environ[key] = value


def putenv(key: str, value: str | Path | None) -> None:
    """Set environment variable. The new variable will be visible to the
    current process and all subprocesses forked from it.

    Unlike :func:`os.putenv`, this method resolves environment variables in the
    value, and it is immediately visible to the current process.

    :param key:
        Variable name
    :param value:
        Variable value. String to set a value, or None to delete the variable.
        It can be a reference other variables, e.g. ``${FOO}.${BAR}``.
        :class:`~pathlib.Path` objects are transparently converted to strings.
    """
    _putenv(key, value, set_msg="Setting", stacklevel=3)


def _putenv(
    key: str, value: str | Path | None, *, set_msg: str, stacklevel: int
) -> None:
    """Helper of putenv() and override_env() to have the correct stacklevel."""
    if value is None:
        log.info("Deleting environment variable %s", key, stacklevel=stacklevel)
        os.environ.pop(key, None)
    else:
        log.info(
            "%s environment variable %s=%s", set_msg, key, value, stacklevel=stacklevel
        )
        # Do NOT use os.putenv() - see python documentation
        os.environ[key] = resolve_env(str(value))


@contextmanager
def override_env(key: str, value: str | Path | None) -> Iterator[None]:
    """Context manager that overrides an environment variable, returns control,
    and then restores it to its original value (or deletes it if it did not
    exist before).

    :param key:
        Variable name
    :param value:
        Variable value. String to set a value, or None to delete the variable.
        It can be a reference other variables, e.g. ``${FOO}.${BAR}``.
        :class:`~pathlib.Path` objects are transparently converted to strings.

    Example:

    >>> print(os.environ['X'])
    foo
    >>> with sh.override_env('X', 'bar'):
    ...     print(os.environ['X'])
    bar
    >>> print(os.environ['X'])
    foo
    """
    orig = os.getenv(key)
    _putenv(key, value, set_msg="Setting", stacklevel=4)

    try:
        yield
    finally:
        _putenv(key, orig, set_msg="Restoring", stacklevel=4)


@overload
def resolve_env(s: str) -> str: ...


@overload
def resolve_env(s: Path) -> Path: ...


def resolve_env(s: str | Path) -> str | Path:
    """Resolve all environment variables in target string or :class:`~pathlib.Path`.

    This command always uses the bash syntax ``$VARIABLE`` or ``${VARIABLE}``.
    This also applies in Windows. Windows native syntax ``%VARIABLE%`` is not
    supported.

    Unlike in :func:`os.path.expandvars`, undefined variables raise an
    exception instead of being silently replaced by an empty string.

    :param s:
        string or :class:`~pathlib.Path` potentially containing environment variables
    :returns:
        resolved string, or :class:`~pathlib.Path` if the input is a
        :class:`~pathlib.Path`
    :raise EnvironmentError:
        in case of missing environment variable
    """
    try:
        return type(s)(string.Template(str(s)).substitute(os.environ))
    except KeyError as e:
        raise OSError(f"Environment variable {e} not found") from None
