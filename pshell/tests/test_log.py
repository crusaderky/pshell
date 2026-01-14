import logging

import pytest

import pshell as sh
from pshell import log
from pshell.tests import get_name


@pytest.mark.thread_unsafe(reason="Modifies global logger")
def test_global_log(caplog):
    log.debug("%d", 1)
    assert sh.get_logger().name == "pshell"
    sh.set_global_logger(logging.getLogger("g1"))
    log.info("%d", 2)
    assert sh.get_logger().name == "g1"
    sh.set_global_logger("g2")
    log.warning("%d", 3)
    assert sh.get_logger().name == "g2"
    sh.set_global_logger(None)
    log.info("%d", 4)
    assert sh.get_logger().name == "pshell"

    assert caplog.record_tuples == [
        ("pshell", logging.DEBUG, "1"),
        ("g1", logging.INFO, "2"),
        ("g2", logging.WARNING, "3"),
        ("pshell", logging.INFO, "4"),
    ]


def test_context_log(caplog):
    foo = get_name("foo")
    bar = get_name("bar")

    log.error("%s %d", foo, 1)
    assert sh.get_logger().name == "pshell"
    tok = sh.context_logger.set(logging.getLogger(bar))
    log.error("%s %d", foo, 2)
    assert sh.get_logger().name == bar
    sh.context_logger.reset(tok)
    log.critical("%s %d", foo, 3)
    assert sh.get_logger().name == "pshell"

    # caplog records all log calls from all threads;
    # in pytest-run-parallel we need to filter first.
    tups = [t for t in caplog.record_tuples if foo in t[2]]

    assert tups == [
        ("pshell", logging.ERROR, f"{foo} 1"),
        (bar, logging.ERROR, f"{foo} 2"),
        ("pshell", logging.CRITICAL, f"{foo} 3"),
    ]


def test_default_stacklevel():
    """Test that the default stacklevel captures the function calling pshell"""
    log.debug("debug")
    log.info("info")
    log.warning("warning")
    log.error("error")
    log.critical("critical")


def test_custom_stacklevel():
    """Teest that if the user passes the stacklevel parameter, it is respected
    and matches the behaviour of the bare logging module.
    """

    def f():
        log.info("from pshell", stacklevel=2)
        logging.info("from logging", stacklevel=2)

    f()


def test_inc_stacklevel_simple():
    @log.inc_stacklevel()
    def f():
        log.info("inside f()")

    f()


def test_inc_stacklevel_nested():
    @log.inc_stacklevel(3)
    def f():
        g()

    def g():
        log.info("inside g()")

    f()


def test_inc_stacklevel_context_manager():
    def f():
        with log.inc_stacklevel(1):
            log.info("inside f()")

    f()


def test_inc_stacklevel_nested_decorators():
    @log.inc_stacklevel()
    def f():
        g()

    @log.inc_stacklevel()
    def g():
        log.info("inside g()")

    f()
