import os
import subprocess
import pshell as sh
from . import DATADIR


def test_find_kill_procs():
    # Test landg.bash.find_procs_by_cmdline and landg.bash.kill_procs

    if os.name == 'nt':
        cmd = [os.path.join(DATADIR, 'test_proc.bat')]
    else:
        cmd = ['bash', os.path.join(DATADIR, 'test_proc.sh')]

    os.environ['TEST_DATADIR'] = DATADIR

    assert sh.find_procs_by_cmdline('$TEST_DATADIR') == []

    subprocess.Popen(cmd)

    after = sh.find_procs_by_cmdline('$TEST_DATADIR')
    assert len(after) == 1

    # Test substrings and OR'ed matches
    assert sh.find_procs_by_cmdline('this wont match anything',
                                    DATADIR) == after

    # TODO: test runtime
    # TODO: test terminating processes resilient to SIGTERM
    sh.kill_procs(after)

    assert sh.find_procs_by_cmdline('$TEST_DATADIR') == []
