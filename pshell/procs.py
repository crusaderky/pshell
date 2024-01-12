"""Utilities to manage running processes
"""
from __future__ import annotations

import getpass
import os
import time
from collections.abc import Collection
from pathlib import Path

import psutil

from pshell import log
from pshell.env import resolve_env

__all__ = ("find_procs_by_cmdline", "kill")


def find_procs_by_cmdline(*cmdlines: str | Path) -> list[psutil.Process]:
    """Search all processes that have a partial match for at least one of the
    given command lines. Command lines are parsed through :func:`resolve_env`.

    For example, the command::

        find_procs_by_cmdline('$MYROOT')

    will return a match for the following processes:

      - ``$MYROOT/static/scripts/something.sh``
      - ``tail -f $LOGDIR/mylog.log``
      - ``myservice.sh -c /algodata/someuser/root/cfg/myservice.cfg``

    where:

      - ``MYROOT=/algodata/someuser/root``
      - ``LOGDIR=/algodata/someuser/root/log``

    This method will only return processes for the current user.

    .. warning::
       Invoking this with relative paths can give erroneous results.
       For example, invoking it with 'foo' will match, for example,
       'foo.pl', 'find_foos.sh', and 'vim foobar.cfg'.

    .. warning::
       This command can't match commands invoked with a relative path
       if the search parameter is an absolute path.
       e.g. ``find_procs_by_cmdline('$MYROOT')`` won't be able to match
       ``cd $MYROOT/bin && ./myscript``.

    :param cmdlines:
        one or more paths command lines to search for
    :returns:
        list of :class:`psutil.Process` objects
    """
    matches = [resolve_env(str(x)) for x in cmdlines]

    log.debug(
        "Finding processes that match command lines:\n  - %s", "\n  - ".join(matches)
    )

    procs = []
    for proc in psutil.process_iter():
        try:
            # On Windows, proc.username() ALWAYS fails
            if os.name != "nt" and proc.username() != getpass.getuser():
                continue
            cmdline = " ".join(proc.cmdline())

            for match in matches:
                if cmdline.find(match) != -1:
                    log.debug("Process %d matches: %s", proc.pid, cmdline)
                    procs.append(proc)
                    break
        except (psutil.NoSuchProcess, psutil.ZombieProcess):
            # Process already died
            pass
        except psutil.AccessDenied:
            # Windows-specific exception that makes psutil.Process.cmdline()
            # fail for processes belonging to other users
            pass

    return procs


def kill(*procs: int | psutil.Process | None, term_timeout: float = 10) -> None:
    """Send SIGTERM to one or more processes. After ``term_timeout`` seconds,
    send SIGKILL to the surviving processes.

    This function will return before ``term_timeout`` if all processes close
    themselves following SIGTERM.

    This function graciously skips processes that do not exist or for which the
    user doesn't have enough permissions. It also automatically skips the
    current process and its parents.

    :param procs:
        one or more PIDs (int) or :class:`psutil.Process` objects, e.g. as
        returned by :func:`find_procs_by_cmdline`.
    :param float term_timeout:
        seconds to wait between SIGTERM and SIGKILL.
        If ``term_timeout==0``, immediately send SIGKILL.
    """
    # Strip list from current process and its parents
    psutil_procs: list[psutil.Process] = []
    my_pid = os.getpid()
    for proc in procs:
        # Convert any int PIDs to psutil.Process
        if isinstance(proc, int):
            try:
                proc = psutil.Process(proc)
            except (psutil.NoSuchProcess, psutil.ZombieProcess):
                log.debug(f"PID {proc} does not exist")
                continue
        elif proc is None:
            # Silently skip - useful as e.g. psutil.Process.parent() can return None
            continue
        elif not isinstance(proc, psutil.Process):
            raise TypeError(f"Expected int or psutil.Process; got {type(proc)}")

        try:
            if proc.pid == my_pid:
                log.debug(
                    f"Not terminating PID {proc.pid} as it is the current process"
                )
                continue
            children = (child.pid for child in proc.children(recursive=True))
            if my_pid in children:
                log.debug(
                    f"Not terminating PID {proc.pid} as it is a parent of "
                    "the  current process",
                )
                continue
        except (psutil.NoSuchProcess, psutil.ZombieProcess):
            log.debug(f"PID {proc.pid} does not exist")
            continue

        psutil_procs.append(proc)

    if not psutil_procs:
        log.info("No processes terminated")
        return

    if term_timeout == 0:
        kill_procs = psutil_procs
    else:
        kill_procs = []
        log.info(
            "Sending SIGTERM to PIDs %s",
            ",".join(str(proc.pid) for proc in psutil_procs),
        )
        for proc in psutil_procs:
            try:
                proc.terminate()
                kill_procs.append(proc)
            except (psutil.NoSuchProcess, psutil.ZombieProcess):
                # Process already died
                pass
            except psutil.AccessDenied:
                log.info(f"Failed to send SIGTERM to PID {proc.pid}: access denied")

        # Wait up to <term_timeout> seconds for SIGTERM to be received
        _, kill_procs = psutil.wait_procs(kill_procs, term_timeout)

    if kill_procs:
        log.info(
            "Sending SIGKILL to PIDs %s", ",".join(str(proc.pid) for proc in kill_procs)
        )
        for proc in kill_procs:
            try:
                proc.kill()
            except (psutil.NoSuchProcess, psutil.ZombieProcess):
                # Process already died
                pass
            except psutil.AccessDenied:
                log.info(f"Failed to send SIGKILL to PID {proc.pid}: access denied")

    log.info("All processes terminated")


def killall(*cmdlines: str | Path, term_timeout: float = 10) -> None:
    """Find all processes with the target command line(s), send SIGTERM, and
    then send SIGKILL to the survivors.

    See :func:`find_procs_by_cmdline` and :func:`kill`.
    """
    kill(*find_procs_by_cmdline(*cmdlines), term_timeout=term_timeout)


def wait_for_server(
    proc: int | psutil.Process,
    port: int | None = None,
    *,
    ignore_ports: Collection[int] | None = None,
    timeout: float | None = None,
) -> int:
    """Wait until either the process starts listening on the given port, or
    it crashes because the port is occupied by something else.

    :param proc:
        psutil.Process or Process ID to observe
    :param int port:
        Port that needs to be opened in listening mode. If omitted, return when any one
        port is opened.
    :param ignore_ports:
        List or set of ports to ignore (only meaningful when port is None).
    :param int timeout:
        Number of seconds to wait before giving up; omit for no timeout
    :returns:
        Opened port number
    :raises psutil.NoSuchProcess:
        If the process dies while waiting
    :raises TimeoutError:
        Timeout expired

    Example:

    .. code-block:: python

        import subprocess
        import pshell

        proc = subprocess.Popen(["redis-server"])
        port = pshell.wait_for_server(proc.pid)
        assert port == 6379

    This can also be used to start a server on port 0, which makes it
    atomically pick up a random free port, and then retrieve said port.
    """
    if isinstance(proc, int):
        proc = psutil.Process(proc)
    ignore_ports = set(ignore_ports) if ignore_ports else set()

    if timeout is not None:
        t0 = time.time()

    while True:
        # proc.connections() will raise Exception if the process dies
        open_ports = {
            conn.laddr.port for conn in proc.connections() if conn.status == "LISTEN"
        }
        open_ports -= ignore_ports
        if port is None and open_ports:
            return open_ports.pop()
        if port is not None and port in open_ports:
            return port

        if timeout is not None and time.time() - t0 > timeout:
            raise TimeoutError("Timeout expired while waiting for port to open")
        time.sleep(0.01)
