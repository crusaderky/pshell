"""Convenience aggregator for all submodules
"""

from subprocess import CalledProcessError, TimeoutExpired  # noqa: F401

import pkg_resources

from .call import call, check_call, check_output, real_fh  # noqa: F401
from .env import override_env, putenv, resolve_env, source  # noqa: F401
from .file import (  # noqa: F401
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
from .manipulate import concatenate  # noqa: F401
from .open import pshell_open as open  # noqa: F401
from .procs import find_procs_by_cmdline, kill, killall, wait_for_server  # noqa: F401
from .search import FileMatchError, glob, iglob  # noqa: F401

try:
    __version__ = pkg_resources.get_distribution("pshell").version
except Exception:
    # Local copy, not installed with setuptools
    __version__ = "999"
