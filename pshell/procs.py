"""Utilities to manage running processes
"""
import getpass
import logging
import os
import psutil
from .env import resolve_env


__all__ = ('find_procs_by_cmdline', 'kill_procs')


def find_procs_by_cmdline(*cmdlines):
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
    matches = [resolve_env(x) for x in cmdlines]

    logging.debug("Finding processes that match command lines:\n  - %s",
                  "\n  - ".join(matches))

    procs = []
    for proc in psutil.process_iter():
        try:
            # Process.username() *always* fails on Windows with AccessDenied
            if os.name != 'nt' and proc.username() != getpass.getuser():
                continue
            cmdline = " ".join(proc.cmdline())

            for match in matches:
                if cmdline.find(match) != -1:
                    logging.debug("Process %d matches: %s", proc.pid, cmdline)
                    procs.append(proc)
                    break
        except psutil.NoSuchProcess:
            # Process already died
            pass
        except psutil.AccessDenied:
            # Windows-specific exception that makes psutil.Process.cmdline()
            # fail for processes belonging to other users
            pass

    return procs


def kill_procs(procs, *, term_timeout=10):
    """Send SIGTERM to a list of processes. After ``term_timeout`` seconds,
    send SIGKILL to the surviving processes.

    This function will return before ``term_timeout`` if all processes close
    themselves following SIGTERM.

    This function graciously skips processes that do not exist or for which the
    user doesn't have enough permissions. It also automatically skips the
    current process and its parents.

    :param procs:
        sequence of :class:`psutil.Process` objects, e.g. as returned by
        :func:`find_procs_by_cmdline`.

    :param float term_timeout:
        seconds to wait between SIGTERM and SIGKILL.
        If ``term_timeout==0``, skip SIGTERM and immediately send SIGKILL.
    """
    # Strip list from current process and its parents
    new_procs = []
    my_pid = os.getpid()
    for proc in procs:
        try:
            if proc.pid == my_pid:
                logging.debug("Not terminating PID %d as it is the current "
                              "process", proc.pid)
                continue
            children = (child.pid for child in proc.children(recursive=True))
            if my_pid in children:
                logging.debug("Not terminating PID %d as it is a parent of "
                              "the  current process", proc.pid)
                continue
        except psutil.NoSuchProcess:
            logging.debug("PID %d does not exist", proc.pid)
            continue

        new_procs.append(proc)
    procs = new_procs

    if term_timeout != 0 and procs:
        logging.info("Sending SIGTERM to PIDs %s",
                     ",".join(str(proc.pid) for proc in procs))
        for proc in procs:
            try:
                proc.terminate()
            except psutil.NoSuchProcess:
                # Process already died
                pass

        # Wait up to <term_timeout> seconds for SIGTERM to be received
        _, procs = psutil.wait_procs(procs, term_timeout)

    if procs:
        logging.info("Sending SIGKILL to PIDs %s",
                     ",".join(str(proc.pid) for proc in procs))
        for proc in procs:
            try:
                proc.kill()
            except psutil.NoSuchProcess:
                # Process already died
                pass

    logging.info("All processes terminated")
