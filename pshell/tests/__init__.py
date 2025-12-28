import os
import uuid

import pytest

DATADIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "data"))


class StubError(Exception):
    """Phony exception used to test that the cleanup in context managers always
    happens
    """


unix_only = pytest.mark.skipif(os.name == "nt", reason="Unix only")
windows_only = pytest.mark.skipif(os.name != "nt", reason="Windows only")


def get_name(suffix: str = "") -> str:
    """A unique name to be used with pytest-run-parallel"""
    suffix = f"_{suffix}" if suffix else ""
    id_ = str(uuid.uuid4()).replace("-", "")
    return f"pshell_tests{suffix}_{id_}"
