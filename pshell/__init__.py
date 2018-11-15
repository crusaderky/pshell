"""Convenience aggregator for all submodules
"""

try:
    from .version import version as __version__  # noqa: F401
except ImportError:  # pragma: no cover
    raise ImportError('pshell not properly installed. If you are running'
                      ' from the source directory, please instead '
                      'create a new virtual environment (using conda or '
                      'virtualenv) and then install it in-place by running: '
                      'pip install -e .')


from subprocess import CalledProcessError, TimeoutExpired   # noqa: F401
from .call import call, check_call, check_output, real_fh  # noqa: F401
from .env import source, putenv, override_env, resolve_env  # noqa: F401
from .file import remove, chdir, pushd, move, copy, backup   # noqa: F401
from .file import symlink, exists, lexists, mkdir, owner  # noqa: F401
from .manipulate import concatenate  # noqa: F401
from .open import pshell_open as open  # noqa: F401
from .procs import find_procs_by_cmdline, kill, killall  # noqa: F401
from .search import FileMatchError, glob, iglob  # noqa: F401
