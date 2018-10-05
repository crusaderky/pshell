"""Functions related to environment variables
"""
import logging
import os
import string
import subprocess
from contextlib import contextmanager
from .call import _BASH_INIT


__all__ = ('source', 'putenv', 'override_env', 'resolve_env')


def source(bash_file, *, stderr=None):
    """Emulate the bash command source <bash_file>.
    The stdout of the command, if any, will be redirected to stderr.
    The acquired variables are exposed to any subprocess afterwards.

    .. note::
        The script is run with errexit, pipefail, nounset. This may cause
        failures when those flags are otherwise not set.

    :raise CalledProcessError: if the command returns with non-zero exit status
    """
    logging.info("Sourcing environment variables from %s", bash_file)

    cmd = _BASH_INIT + "source %s 1>&2 && env" % bash_file

    stdout = subprocess.check_output(cmd, shell=True, stderr=stderr)

    for line in stdout.decode('utf-8').split("\n"):
        (key, _, value) = line.partition("=")

        if key not in ('_', '', 'SHLVL') and os.getenv(key) != value:
            logging.debug("Setting environment variable: %s=%s", key, value)
            os.environ[key] = value


def putenv(var, value):
    """Set environment variable. The new variable will be visible to the
    current process and all subprocesses originating from it.

    Unlike os.putenv(), this method resolves environment variables in the
    value, and it is immediately visible to the current process.

    :param var:
        Variable name
    :param value:
        Variable value. String to set a value, or None to delete the variable
    """
    if value is None:
        logging.info("Deleting environment variable %s", var)
        os.environ.pop(var, None)
    else:
        logging.info("Setting environment variable %s=%s", var, value)
        # Do NOT use os.putenv() - see python manual
        os.environ[var] = resolve_env(value)


@contextmanager
def override_env(var, value):
    """Context manager that overrides an environment variable, returns control,
    and then restores it to its original value

    :param var:
        Variable name
    :param value:
        Variable value. String to set a value, or None to delete the variable
    """
    value_backup = os.getenv(var)
    putenv(var, value)

    try:
        yield
    finally:
        putenv(var, value_backup)


def resolve_env(s):
    """Resolve all environment variables in target string.

    :returns: resolved string
    :raise EnvironmentError: in case of missing environment variable
    """
    try:
        return string.Template(s).substitute(os.environ)
    except KeyError as e:
        raise EnvironmentError("Environment variable %s not found" % str(e))
