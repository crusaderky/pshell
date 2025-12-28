import logging

import pytest

import pshell as sh
from pshell import log
from pshell.tests import get_name


@pytest.mark.thread_unsafe(reason="Modifies global logger")
def test_global_log(caplog):
    caplog.set_level(10)
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
        ("pshell", 10, "1"),
        ("g1", 20, "2"),
        ("g2", 30, "3"),
        ("pshell", 20, "4"),
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
    log.error("%s %d", foo, 3)
    assert sh.get_logger().name == "pshell"

    # caplog records all log calls from all threads;
    # in pytest-run-parallel we need to filter first.
    tups = [t for t in caplog.record_tuples if foo in t[2]]

    assert tups == [
        ("pshell", 40, f"{foo} 1"),
        (bar, 40, f"{foo} 2"),
        ("pshell", 40, f"{foo} 3"),
    ]
