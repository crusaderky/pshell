import os
import subprocess
import time
import psutil
import pshell as sh
import pytest
from . import DATADIR


def spawn_test_proc():
    """Start a long-running process
    """
    if os.name == 'nt':
        cmd = [os.path.join(DATADIR, 'test_proc.bat')]
    else:
        cmd = ['bash', os.path.join(DATADIR, 'test_proc.sh')]

    subprocess.Popen(cmd)


def test_find_kill_procs():
    """Test pshell.find_procs_by_cmdline and pshell.kill
    """
    os.environ['TEST_DATADIR'] = DATADIR

    assert sh.find_procs_by_cmdline("this won't match anything") == []
    assert sh.find_procs_by_cmdline('$TEST_DATADIR') == []

    spawn_test_proc()

    after = sh.find_procs_by_cmdline('$TEST_DATADIR')
    assert len(after) == 1
    assert after[0].status() == 'sleeping'

    # Test substrings and OR'ed matches
    assert sh.find_procs_by_cmdline("this won't match anything",
                                    DATADIR) == after

    t1 = time.time()
    sh.kill(*after)
    t2 = time.time()
    # Test that kill() did not wait the full 10 seconds since the process
    # graciously responded to SIGTERM
    assert t2 - t1 < 2

    with pytest.raises(psutil.NoSuchProcess):
        after[0].status()

    assert sh.find_procs_by_cmdline('$TEST_DATADIR') == []


def test_killall():
    spawn_test_proc()
    assert len(sh.find_procs_by_cmdline(DATADIR)) == 1
    sh.killall(DATADIR)
    assert sh.find_procs_by_cmdline(DATADIR) == []


def test_kill2():
    """Test pshell.kill:

    - procs expressed as int PIDs
    - silently skip process not owned by current user
    - silently skip non-existing process
    - silently skip current process and ancestors of current process
    - raise TypeError on unknown parameters
    """
    current = psutil.Process()
    sh.kill(1, 70000, current, current.parent(), current.parent().parent())
    with pytest.raises(TypeError):
        sh.kill('foo')


@pytest.mark.skip('TODO')
def test_sigkill():
    """Test terminating processes resilient to SIGTERM
    """
    pass
