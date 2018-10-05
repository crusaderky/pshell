"""Utilities to manage running processes
"""
import getpass
import logging
import os
import psutil
from .env import resolve_env


def kill_procs(procs, *, term_timeout=10):
    """Send SIGTERM to a list of processes. After <term_timeout> seconds,
    send SIGKILL to the surviving processes.

    This method will actually terminate before <term_timeout>, if all processes
    close themselves following SIGTERM.

    :param list procs:
        list of psutil.Process objects, e.g. as returned by
        :func:`find_procs_by_cmdline`.
        Graciously skip processes that do not exist or for which you don't have
        enough permissions. Automatically skip current process or parents of
        it.
    :param int term_timeout:
        seconds to wait between SIGTERM and SIGKILL.
        If term_timeout==0, immediately send SIGKILL.
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


def find_procs_by_cmdline(*cmdlines):
    """Search all processes that have a partial match for at least one of the
    given command lines. Command lines are parsed through :func:`resolve_env`.

    For example, the command::

        find_procs_by_cmdline('$ALGO_TOP')

    will return a match for the following processes:

      - $ALGO_TOP/static/scripts/something.sh
      - tail -f $ALGO_LOG/mylog.log
      - myservice.sh -c /algodata/someuser/TOP/cfg/myservice.cfg

    where:

      - ALGO_TOP=/algodata/someuser/TOP
      - ALGO_LOG=/algodata/someuser/TOP/log

    This method will only return processes for the current user.

    .. warning::
       Invoking this with relative paths can give errouneous results.
       For example, invoking it with 'fanfare' will match, for example,
       'fanfare.pl', 'find_fanfares.sh', and 'vim ara_fanfare.cfg'.

    .. warning::
       This command can't match commands invoked with a relative path
       if the search parameter is an absolute path.
       e.g. ``find_procs_by_cmdline('$RW_HOME')`` won't be able to match
       ``cd $RW_HOME/bin && ./runrw``.

    :param cmdlines: one or more paths command lines to search for
    :returns: list of psutil.Process objects.

    See also: http://code.google.com/p/psutil/wiki/Documentation
    """
    matches = [resolve_env(x) for x in cmdlines]

    logging.debug("Finding processes that match command lines:\n  - %s",
                  "\n  - ".join(matches))

    procs = []
    for proc in psutil.process_iter():
        try:
            if proc.username() != getpass.getuser():
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
    return procs
