import getpass
import multiprocessing
import os
import pathlib
import shutil
import socket
import subprocess
import sys
import time

import psutil
import pytest

import pshell as sh
from pshell.tests import DATADIR, get_name

pytestmark = pytest.mark.filterwarnings(
    r"ignore:subprocess \d+ is still running:ResourceWarning"
)


def spawn_test_proc(script_name, tmp_path):
    """Start a long-running process"""
    shutil.copy(pathlib.Path(DATADIR) / script_name, tmp_path)
    cmd = [sys.executable, str(tmp_path / script_name)]
    popen = subprocess.Popen(cmd, stdout=subprocess.PIPE)
    assert popen.stdout is not None
    assert popen.stdout.readline().decode().strip() == "ready"
    popen.stdout.close()
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


def globbable_tmp_path(tmp_path: pathlib.Path, thread_index: int) -> pathlib.Path:
    """In pytest_run_parallel, tmp_path is unique to the thread, but since it contains
    thread_1 etc. this causes match collisions when you have 10 or more threads
    """
    idx = f"{thread_index:04d}"
    (tmp_path / idx).mkdir()
    return tmp_path / idx


def test_find_kill_procs(str_or_path, tmp_path, thread_index):
    """Test pshell.find_procs_by_cmdline and pshell.kill"""
    tmp_path = globbable_tmp_path(tmp_path, thread_index)
    n = get_name()
    os.environ[n] = str(tmp_path)

    assert sh.find_procs_by_cmdline("this won't match anything") == []
    assert sh.find_procs_by_cmdline(str_or_path(f"${n}")) == []
    test_proc = spawn_test_proc("sleep20.py", tmp_path)

    after = sh.find_procs_by_cmdline(str_or_path(tmp_path))
    assert after == [test_proc]

    after = sh.find_procs_by_cmdline(str_or_path(f"${n}"))
    assert after == [test_proc]

    # Test OR'ed matches
    after = sh.find_procs_by_cmdline("this won't match anything", str_or_path(tmp_path))
    assert after == [test_proc]

    t1 = time.time()
    sh.kill(test_proc)
    t2 = time.time()
    # Test that kill() did not wait the full 10 seconds since the process
    # graciously responded to SIGTERM
    assert t2 - t1 < 2

    with pytest.raises(psutil.NoSuchProcess):
        test_proc.status()

    assert sh.find_procs_by_cmdline(str_or_path(f"${n}")) == []


def test_killall(str_or_path, tmp_path, thread_index):
    tmp_path = globbable_tmp_path(tmp_path, thread_index)

    proc = spawn_test_proc("sleep20.py", tmp_path)
    assert sh.find_procs_by_cmdline(str_or_path(tmp_path)) == [proc]
    sh.killall(str_or_path(tmp_path))
    assert not sh.find_procs_by_cmdline(str_or_path(tmp_path))


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
def test_sigkill_sigterm_delay5(tmp_path, thread_index):
    """Test that kill() will send a SIGTERM to kill the target first.  Process
    that shuts itself downupon receiving SIGTERM will be able to do so
    gracefully.
    """
    tmp_path = globbable_tmp_path(tmp_path, thread_index)
    spawn_test_proc("sleep20_sigterm_delay5.py", tmp_path)

    procs = sh.find_procs_by_cmdline(tmp_path)
    assert len(procs) == 1

    t1 = time.time()
    sh.kill(procs[0])
    t2 = time.time()
    duration_of_kill = t2 - t1

    assert not sh.find_procs_by_cmdline(tmp_path)
    assert duration_of_kill > 5  # target process SIGTERM handler delay is 5s
    assert duration_of_kill < 10  # sh.kill() will retry SIGKILL in 10s


@pytest.mark.slow
@pytest.mark.skipif(
    os.name == "nt",
    reason="On Windows, os.kill() and psutil.kill() calls TerminateProcess "
    "API which does not process signals (such as SIGTERM, SIGKILL "
    "etc..) as ANSI/POSIX prescribed. The TerminateProcess API "
    "unconditionally terminates the target process.",
)
@pytest.mark.parametrize(
    "kwargs,min_elapsed,max_elapsed",
    [({}, 10, 12), ({"term_timeout": 3}, 3, 5), ({"term_timeout": 0}, 0, 2)],
)
def test_sigkill_sigterm_ignore(
    kwargs, min_elapsed, max_elapsed, tmp_path, thread_index
):
    """Test terminating processes resilient to SIGTERM, which would ignore the
    initial SIGTERM it receives.  The kill() will attempt to shut the process
    again later forcefully.
    """
    tmp_path = globbable_tmp_path(tmp_path, thread_index)
    spawn_test_proc("sleep20_sigterm_ignore.py", tmp_path)

    procs = sh.find_procs_by_cmdline(tmp_path)
    assert len(procs) == 1

    t1 = time.time()
    sh.kill(procs[0], **kwargs)
    t2 = time.time()
    elapsed = t2 - t1
    assert not sh.find_procs_by_cmdline(tmp_path)
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


def test_wait_for_server(thread_index):
    port1 = 9100 + thread_index
    # Test with PID; the process is not listening straight away
    with ListenProcess(port1, sleep=0.1) as proc:
        port = sh.wait_for_server(proc.pid)
        assert port == port1

        # Test with psutil.Process; the process is already listening
        psproc = psutil.Process(proc.pid)
        port = sh.wait_for_server(psproc)
        assert port == port1

    # Test dead process
    with pytest.raises(psutil.NoSuchProcess):
        sh.wait_for_server(psproc)


def test_wait_for_server_timeout(thread_index):
    port1 = 9100 + thread_index
    with ListenProcess(port1, sleep=0.4) as proc:
        with pytest.raises(TimeoutError):
            sh.wait_for_server(proc.pid, timeout=0.05)
        port = sh.wait_for_server(proc.pid, timeout=5)
        assert port == port1


def test_wait_for_server_multiport_whitelist(thread_index):
    port1 = 9100 + thread_index
    port2 = 9700 + thread_index
    with ListenProcess(port1, port2, sleep=0.2) as proc:
        port = sh.wait_for_server(proc.pid)
        assert port == port1
        port = sh.wait_for_server(proc.pid, port2)
        assert port == port2


def test_wait_for_server_multiport_blacklist(thread_index):
    port1 = 9100 + thread_index
    port2 = 9700 + thread_index
    with ListenProcess(port1, port2, sleep=0.2) as proc:
        port = sh.wait_for_server(proc.pid, ignore_ports=[port1])
        assert port == port2
