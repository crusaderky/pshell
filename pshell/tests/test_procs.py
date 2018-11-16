import getpass
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
        cmd = [os.path.join(DATADIR, 'sleep20.bat')]
    else:
        cmd = ['bash', os.path.join(DATADIR, 'sleep20.sh')]

    popen = subprocess.Popen(cmd)
    return psutil.Process(popen.pid)


def get_other_users_proc():
    """Find a process belonging to another user, which is not a parent of the
    current process
    """
    current = psutil.Process()
    for proc in psutil.process_iter():
        try:
            if proc.username() == getpass.getuser():
                continue
            if all(c != current for c in proc.children(recursive=True)):
                return proc
        except psutil.AccessDenied:
            continue
    raise EnvironmentError("All processes belong to the current user")


def test_find_kill_procs():
    """Test pshell.find_procs_by_cmdline and pshell.kill
    """
    os.environ['TEST_DATADIR'] = DATADIR

    assert sh.find_procs_by_cmdline("this won't match anything") == []
    assert sh.find_procs_by_cmdline('$TEST_DATADIR') == []

    test_proc = spawn_test_proc()

    after = sh.find_procs_by_cmdline('$TEST_DATADIR')
    assert after == [test_proc]

    # Test substrings and OR'ed matches
    after2 = sh.find_procs_by_cmdline("this won't match anything", DATADIR)
    assert after2 == after

    t1 = time.time()
    sh.kill(test_proc)
    t2 = time.time()
    # Test that kill() did not wait the full 10 seconds since the process
    # graciously responded to SIGTERM
    assert t2 - t1 < 2

    with pytest.raises(psutil.NoSuchProcess):
        test_proc.status()

    assert sh.find_procs_by_cmdline('$TEST_DATADIR') == []


def test_killall():
    spawn_test_proc()
    assert len(sh.find_procs_by_cmdline(DATADIR)) == 1
    sh.killall(DATADIR)
    assert sh.find_procs_by_cmdline(DATADIR) == []


def test_kill2():
    """Test pshell.kill:

    - procs expressed as int PIDs
    - silently skip processes not owned by current user
    - silently skip non-existing processes
    - silently skip None
    - silently skip current process and ancestors of current process
    - raise TypeError on unknown parameters
    """
    current = psutil.Process()
    sh.kill(70000, None, current, current.parent(),
            current.parent().parent(), get_other_users_proc())
    with pytest.raises(TypeError):
        sh.kill('foo')


@pytest.mark.skip('TODO')
def test_sigkill():
    """Test terminating processes resilient to SIGTERM
    """
    pass
