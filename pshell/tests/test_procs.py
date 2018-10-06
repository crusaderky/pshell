import os
import subprocess
import pshell as sh
from . import DATADIR


def test_find_kill_procs():
    # Test landg.bash.find_procs_by_cmdline and landg.bash.kill_procs
    cmd = ['bash', '%s/test_proc.sh' % DATADIR]
    os.environ['TEST_DATADIR'] = DATADIR

    assert sh.find_procs_by_cmdline('$TEST_DATADIR') == []

    p = subprocess.Popen(cmd)

    after = sh.find_procs_by_cmdline('$TEST_DATADIR')
    assert len(after) == 1
    assert after[0].cmdline() == cmd

    # Test substrings and OR'ed matches
    assert sh.find_procs_by_cmdline('this wont match anything',
                                    DATADIR) == after

    # TODO: test runtime
    # TODO: test terminating processes resilient to SIGTERM
    sh.kill_procs(after)

    assert sh.find_procs_by_cmdline('$TEST_DATADIR') == []