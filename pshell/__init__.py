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
from .call import *  # noqa: F401, F403
from .env import *  # noqa: F401, F403
from .file import *  # noqa: F401, F403
from .manipulate import *  # noqa: F401, F403
from .open import *  # noqa: F401, F403
from .procs import *  # noqa: F401, F403
from .search import *  # noqa: F401, F403
