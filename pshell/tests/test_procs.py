import getpass
import multiprocessing
import os
import socket
import subprocess
import sys
import time

import psutil
import pytest

import pshell as sh
from pshell.tests import DATADIR

pytestmark = pytest.mark.filterwarnings(
    r"ignore:subprocess \d+ is still running:ResourceWarning"
)


def spawn_test_proc():
    """Start a long-running process"""
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
                continue  # pragma: nocover
            if all(c != current for c in proc.children(recursive=True)):
                return proc
        except psutil.AccessDenied:  # pragma: nocover
            continue
    raise OSError("All processes belong to the current user")  # pragma: nocover


def test_find_kill_procs(str_or_path):
    """Test pshell.find_procs_by_cmdline and pshell.kill"""
    os.environ["TEST_DATADIR"] = DATADIR

    assert sh.find_procs_by_cmdline("this won't match anything") == []
    assert sh.find_procs_by_cmdline("$TEST_DATADIR") == []
    assert sh.find_procs_by_cmdline(str_or_path("$TEST_DATADIR")) == []

    test_proc = spawn_test_proc()

    after = sh.find_procs_by_cmdline(str_or_path("$TEST_DATADIR"))
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

    assert sh.find_procs_by_cmdline(str_or_path("$TEST_DATADIR")) == []


def test_killall(str_or_path):
    spawn_test_proc()
    # Test for 1+ processes.
    # Don't test for exactly 1 process (see comment above)
    assert sh.find_procs_by_cmdline(str_or_path(DATADIR))
    sh.killall(str_or_path(DATADIR))
    assert not sh.find_procs_by_cmdline(str_or_path(DATADIR))


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


@pytest.mark.slow
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


@pytest.mark.slow
@pytest.mark.skipif(
    os.name == "nt",
    reason="On Windows, os.kill() and psutil.kill() calls TerminateProcess "
    "API which does not process signals (such as SIGTERM, SIGKILL "
    "etc..) as ANSI/POSIX prescribed.  The TerminateProcess API "
    "unconditionally terminates the target process.",
)
@pytest.mark.parametrize(
    "kwargs,min_elapsed,max_elapsed",
    [({}, 10, 12), ({"term_timeout": 3}, 3, 5), ({"term_timeout": 0}, 0, 2)],
)
def test_sigkill_sigterm_ignore(kwargs, min_elapsed, max_elapsed):
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
    sh.kill(procs[0], **kwargs)
    t2 = time.time()
    elapsed = t2 - t1
    assert not sh.find_procs_by_cmdline(DATADIR)
    if min_elapsed > 0:
        assert min_elapsed < elapsed
    assert elapsed < max_elapsed


class ListenProcess(multiprocessing.Process):
    """Context manager that starts a subprocess that listens on one or more ports.
    If sleep is set, it waits <sleep> seconds before listening on each port.

    e.g.::

        with ListenProcess(2000, 2001, sleep=1) as proc:
            # start; not listening on any ports
            # sleep 1 second
            # open port 2000
            # sleep 1 second
            # open port 2001
        # terminate on context exit
    """

    def __init__(self, *ports: int, sleep: float = 0):
        self.ports = ports
        self.sleep = sleep
        super().__init__()

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.terminate()
        self.join()

    def run(self):  # pragma: nocover
        sockets = []
        for port in self.ports:
            time.sleep(self.sleep)
            sk = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sk.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sk.bind(("localhost", port))
            sk.listen(10)
            sockets.append(sk)
        while True:
            time.sleep(1)


def test_wait_for_server():
    # Test with PID; the process is not listening straight away
    with ListenProcess(9123, sleep=0.1) as proc:
        port = sh.wait_for_server(proc.pid)
        assert port == 9123

        # Test with psutil.Process; the process is already listening
        psproc = psutil.Process(proc.pid)
        port = sh.wait_for_server(psproc)
        assert port == 9123

    # Test dead process
    with pytest.raises(psutil.NoSuchProcess):
        sh.wait_for_server(psproc)


def test_wait_for_server_timeout():
    with ListenProcess(9123, sleep=0.4) as proc:
        with pytest.raises(TimeoutError):
            sh.wait_for_server(proc.pid, timeout=0.05)
        port = sh.wait_for_server(proc.pid, timeout=1)
        assert port == 9123


def test_wait_for_server_multiport_whitelist():
    with ListenProcess(9123, 9124, sleep=0.2) as proc:
        port = sh.wait_for_server(proc.pid)
        assert port == 9123
        port = sh.wait_for_server(proc.pid, 9124)
        assert port == 9124


def test_wait_for_server_multiport_blacklist():
    with ListenProcess(9123, 9124, sleep=0.2) as proc:
        port = sh.wait_for_server(proc.pid, ignore_ports=[9123])
        assert port == 9124
