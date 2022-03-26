"""Convenience aggregator for all submodules
"""

import importlib.metadata
from subprocess import CalledProcessError, TimeoutExpired  # noqa: F401

from pshell.call import call, check_call, check_output, real_fh
from pshell.env import override_env, putenv, resolve_env, source
from pshell.file import (
    backup,
    chdir,
    copy,
    exists,
    lexists,
    mkdir,
    move,
    owner,
    pushd,
    remove,
    symlink,
)
from pshell.log import context_logger, get_logger, set_global_logger
from pshell.manipulate import concatenate
from pshell.open import pshell_open as open
from pshell.procs import find_procs_by_cmdline, kill, killall, wait_for_server
from pshell.search import FileMatchError, glob, iglob

try:
    __version__ = importlib.metadata.version("pshell")
except importlib.metadata.PackageNotFoundError:  # pragma: nocover
    # Local copy, not installed with pip
    __version__ = "999"
