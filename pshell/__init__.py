"""Convenience aggregator for all submodules
"""

import importlib.metadata
from subprocess import CalledProcessError, TimeoutExpired  # noqa: F401

from pshell.call import call as call
from pshell.call import check_call as check_call
from pshell.call import check_output as check_output
from pshell.call import real_fh as real_fh
from pshell.env import override_env as override_env
from pshell.env import putenv as putenv
from pshell.env import resolve_env as resolve_env
from pshell.env import source as source
from pshell.file import backup as backup
from pshell.file import chdir as chdir
from pshell.file import copy as copy
from pshell.file import exists as exists
from pshell.file import lexists as lexists
from pshell.file import mkdir as mkdir
from pshell.file import move as move
from pshell.file import owner as owner
from pshell.file import pushd as pushd
from pshell.file import remove as remove
from pshell.file import symlink as symlink
from pshell.log import context_logger as context_logger
from pshell.log import get_logger as get_logger
from pshell.log import set_global_logger as set_global_logger
from pshell.manipulate import concatenate as concatenate
from pshell.open import pshell_open as open  # noqa: F401
from pshell.procs import find_procs_by_cmdline as find_procs_by_cmdline
from pshell.procs import kill as kill
from pshell.procs import killall as killall
from pshell.procs import wait_for_server as wait_for_server
from pshell.search import FileMatchError as FileMatchError
from pshell.search import glob as glob
from pshell.search import iglob as iglob

try:
    __version__ = importlib.metadata.version("pshell")
except importlib.metadata.PackageNotFoundError:  # pragma: nocover
    # Local copy, not installed with pip
    __version__ = "999"
