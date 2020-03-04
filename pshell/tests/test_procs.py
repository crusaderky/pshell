import getpass
import os
import subprocess
import sys
import time

import psutil
import pytest

import pshell as sh

from . import DATADIR


def spawn_test_proc():
    """Start a long-running process
    """
    if os.name == "nt":
        cmd = [os.path.join(DATADIR, "sleep20.bat")]
    else:
        cmd = ["bash", os.path.join(DATADIR, "sleep20.sh")]

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
    os.environ["TEST_DATADIR"] = DATADIR

    assert sh.find_procs_by_cmdline("this won't match anything") == []
    assert sh.find_procs_by_cmdline("$TEST_DATADIR") == []

    test_proc = spawn_test_proc()

    after = sh.find_procs_by_cmdline("$TEST_DATADIR")
    # Both the bash and cmd variants of the test process spawn short-lived
    # subprocesses. Testing for an exact match of 1 result causes instability
    # in the unit tests.
    assert test_proc in after

    # Test substrings and OR'ed matches
    after2 = sh.find_procs_by_cmdline("this won't match anything", DATADIR)
    assert test_proc in after2

    t1 = time.time()
    sh.kill(test_proc)
    t2 = time.time()
    # Test that kill() did not wait the full 10 seconds since the process
    # graciously responded to SIGTERM
    assert t2 - t1 < 2

    with pytest.raises(psutil.NoSuchProcess):
        test_proc.status()

    assert sh.find_procs_by_cmdline("$TEST_DATADIR") == []


def test_killall():
    spawn_test_proc()
    # Test for 1+ processes.
    # Don't test for exactly 1 process (see comment above)
    assert sh.find_procs_by_cmdline(DATADIR)
    sh.killall(DATADIR)
    assert not sh.find_procs_by_cmdline(DATADIR)


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
    sh.kill(
        70000,
        None,
        current,
        current.parent(),
        current.parent().parent(),
        get_other_users_proc(),
    )
    with pytest.raises(TypeError):
        sh.kill("foo")


@pytest.mark.skipif(
    os.name == "nt",
    reason="On Windows, os.kill() and psutil.kill() calls TerminateProcess "
    "API which does not process signals (such as SIGTERM, SIGKILL "
    "etc..) as ANSI/POSIX prescribed.  The TerminateProcess API "
    "unconditionally terminates the target process.",
)
def test_sigkill_sigterm_delay5():
    """Test that kill() will send a SIGTERM to kill the target first.  Process
    that shuts itself downupon receiving SIGTERM will be able to do so
    gracefully.
    """
    cmd = [sys.executable, os.path.join(DATADIR, "sleep20_sigterm_delay5.py")]
    subprocess.Popen(cmd)
    time.sleep(1)  # to allow enough time for python to start

    procs = sh.find_procs_by_cmdline(DATADIR)
    assert len(procs) == 1

    t1 = time.time()
    sh.kill(procs[0])
    t2 = time.time()
    duration_of_kill = t2 - t1

    assert not sh.find_procs_by_cmdline(DATADIR)
    assert duration_of_kill > 5  # target process SIGTERM handler delay is 5s
    assert duration_of_kill < 10  # sh.kill() will retry SIGKILL in 10s


@pytest.mark.skipif(
    os.name == "nt",
    reason="On Windows, os.kill() and psutil.kill() calls TerminateProcess "
    "API which does not process signals (such as SIGTERM, SIGKILL "
    "etc..) as ANSI/POSIX prescribed.  The TerminateProcess API "
    "unconditionally terminates the target process.",
)
def test_sigkill_sigterm_ignore():
    """Test terminating processes resilient to SIGTERM, which would ignore the
    initial SIGTERM it receives.  The kill() will attempt to shut the process
    again later forcefully.
    """
    cmd = [sys.executable, os.path.join(DATADIR, "sleep20_sigterm_ignore.py")]
    subprocess.Popen(cmd)
    time.sleep(1)  # to allow enough time for python to start

    procs = sh.find_procs_by_cmdline(DATADIR)
    assert len(procs) == 1

    t1 = time.time()
    sh.kill(procs[0])
    t2 = time.time()
    duration_of_kill = t2 - t1

    assert not sh.find_procs_by_cmdline(DATADIR)
    assert duration_of_kill > 10  # sh.kill() will retry SIGKILL in 10s
    assert duration_of_kill < 20  # target process only runs this long
