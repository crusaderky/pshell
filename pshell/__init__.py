"""Convenience aggregator for all submodules
"""

import pkg_resources

try:
    __version__ = pkg_resources.get_distribution("pshell").version
except Exception:
    # Local copy, not installed with setuptools
    __version__ = "999"


from subprocess import CalledProcessError, TimeoutExpired   # noqa: F401
from .call import call, check_call, check_output, real_fh  # noqa: F401
from .env import source, putenv, override_env, resolve_env  # noqa: F401
from .file import remove, chdir, pushd, move, copy, backup   # noqa: F401
from .file import symlink, exists, lexists, mkdir, owner  # noqa: F401
from .manipulate import concatenate  # noqa: F401
from .open import pshell_open as open  # noqa: F401
from .procs import find_procs_by_cmdline, kill, killall  # noqa: F401
from .search import FileMatchError, glob, iglob  # noqa: F401
