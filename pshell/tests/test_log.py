import logging

import pshell as sh
from pshell import log


def test_log(caplog):
    caplog.set_level(10)
    log.debug("%d", 1)
    assert sh.get_logger().name == "pshell"
    sh.set_global_logger(logging.getLogger("g1"))
    log.info("%d", 2)
    assert sh.get_logger().name == "g1"
    sh.set_global_logger("g2")
    log.warning("%d", 3)
    assert sh.get_logger().name == "g2"
    tok = sh.context_logger.set(logging.getLogger("c"))
    log.error("%d", 4)
    assert sh.get_logger().name == "c"
    sh.context_logger.reset(tok)
    log.critical("%d", 5)
    assert sh.get_logger().name == "g2"
    sh.set_global_logger(None)
    log.info("%d", 6)
    assert sh.get_logger().name == "pshell"

    assert caplog.record_tuples == [
        ("pshell", 10, "1"),
        ("g1", 20, "2"),
        ("g2", 30, "3"),
        ("c", 40, "4"),
        ("g2", 50, "5"),
        ("pshell", 20, "6"),
    ]
