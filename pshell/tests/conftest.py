import logging
import os
import sys
from pathlib import Path

import pytest


@pytest.fixture(params=[str, Path])
def str_or_path(request):
    """Run a test that uses this fixture twice, with and without pathlib

    Usage:

    >>> def test_open(str_or_path):
    ...     sh.open(str_or_path("foo/bar/baz"))
    """
    return request.param


@pytest.fixture(autouse=True)
def clear_names():
    """Clear any environment variables created with get_name()"""
    yield
    for key in list(os.environ.keys()):
        if key.startswith("pshell_tests"):
            del os.environ[key]


if "pytest_run_parallel" not in sys.modules:

    @pytest.fixture
    def thread_index():
        return 0


@pytest.fixture(autouse=True)
def assert_log_stacklevel(request, caplog):
    """Test that all log messages emitted by the test that uses this fixture are logged
    as emitted by the test function itself, and not by pshell.
    """
    with caplog.at_level(logging.DEBUG):
        yield
    records = caplog.get_records("call")
    for record in records:
        assert record.filename == os.path.basename(request.node.fspath)
