"""Functions related to environment variables
"""
import logging
import os
import string
from contextlib import contextmanager
from .call import check_output


__all__ = ('source', 'putenv', 'override_env', 'resolve_env')


def source(bash_file, *, stderr=None):
    """Emulate the bash command ``source <bash_file>``.
    The stdout of the command, if any, will be redirected to stderr.
    The acquired variables are injected into ``os.environment`` and are
    exposed to any subprocess invoked afterwards.

    .. note::
        The script is always executed with bash. This includes in Windows,
        where the user needs to make sure bash is installed within %PATH%, and
        some unixes such as Ubuntu, where /bin/sh is actually dash.

        The script is run with errexit, pipefail, nounset.

    :param str bash_file:
        Path to the bash file. It can contain environment variables.
    :param stderr:
        standard error file handle. Omit for sys.stderr.
        Unlike the same parameter for :func:`subprocess.call`, which must be
        backed by a OS-level file descriptor, this can be a
        pseudo-stream like e.g. :class:`io.StringIO`.
    :raise CalledProcessError:
        if the command returns with non-zero exit status
    """
    logging.info("Sourcing environment variables from %s", bash_file)

    stdout = check_output('source "%s" 1>&2 && env' % bash_file, stderr=stderr)

    for line in stdout.splitlines():
        (key, _, value) = line.partition("=")

        if key not in ('_', '', 'SHLVL') and os.getenv(key) != value:
            logging.debug("Setting environment variable: %s=%s", key, value)
            os.environ[key] = value


def putenv(key, value):
    """Set environment variable. The new variable will be visible to the
    current process and all subprocesses originating from it.

    Unlike os.putenv(), this method resolves environment variables in the
    value, and it is immediately visible to the current process.

    :param key:
        Variable name
    :param value:
        Variable value. String to set a value, or None to delete the variable.
        It can be a reference other variables, e.g. ``${FOO}.${BAR}``.
    """
    if value is None:
        logging.info("Deleting environment variable %s", key)
        os.environ.pop(key, None)
    else:
        logging.info("Setting environment variable %s=%s", key, value)
        # Do NOT use os.putenv() - see python documentation
        os.environ[key] = resolve_env(value)


@contextmanager
def override_env(key, value):
    """Context manager that overrides an environment variable, returns control,
    and then restores it to its original value.

    :param key:
        Variable name
    :param value:
        Variable value. String to set a value, or None to delete the variable.
        It can be a reference other variables, e.g. ``${FOO}.${BAR}``.

    Example::

        >>> print(os.environ['X'])
        foo
        >>> with override_env('X', 'bar'):
        ...     print(os.environ['X'])
        bar
        >>> print(os.environ['X'])
        foo
    """
    value_backup = os.getenv(key)
    putenv(key, value)

    try:
        yield
    finally:
        putenv(key, value_backup)


def resolve_env(s):
    """Resolve all environment variables in target string.

    This command always uses the bash syntax ``$VARIABLE`` or ``${VARIABLE}``.
    This also applies in Windows. Windows native syntax ``%VARIABLE%`` is not
    supported.

    :returns:
        resolved string
    :raise EnvironmentError:
        in case of missing environment variable
    """
    try:
        return string.Template(s).substitute(os.environ)
    except KeyError as e:
        raise EnvironmentError("Environment variable %s not found" % e)
