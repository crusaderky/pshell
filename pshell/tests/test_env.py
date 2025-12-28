import os

import pytest

import pshell as sh
from pshell.tests import StubError, get_name, unix_only


@unix_only
def test_source(str_or_path, tmp_path):
    foo = get_name("foo")
    bar = get_name("bar")
    baz = get_name("baz")
    with open(tmp_path / "source.sh", "w") as fh:
        # Do not confuse stdout of the sourced script with variable assignments
        fh.write("echo pshell_test_ignore=me\n")
        fh.write("echo pshell_test_ignore me too\n")
        fh.write(f"export {foo}='foo'\n")
        fh.write(f"export {bar}='bar'\n")

    print(f"reset {bar}")
    os.environ[bar] = "old"

    # Also test variable name resolution
    os.environ[baz] = str(tmp_path)
    sh.source(str_or_path(f"${baz}/source.sh"))

    assert os.environ[foo] == "foo"
    assert os.environ[bar] == "bar"
    assert "pshell_test_ignore" not in os.environ


def test_resolve_env(str_or_path):
    foo = get_name("foo")
    bar = get_name("bar")
    os.environ[foo] = "foo"
    os.environ[bar] = "bar"

    out = sh.resolve_env(str_or_path(f"${foo}.${bar}"))
    assert str(out) == "foo.bar"
    assert isinstance(out, str_or_path)

    # Variant syntax ${VAR}
    out = sh.resolve_env(str_or_path(f"${{{foo}}}.${{{bar}}}"))
    assert str(out) == "foo.bar"
    assert isinstance(out, str_or_path)

    with pytest.raises(EnvironmentError, match="NOT_EXISTING_VARIABLE"):
        sh.resolve_env("$NOT_EXISTING_VARIABLE")


def test_putenv(str_or_path):
    foo = get_name("foo")
    bar = get_name("bar")
    # Base use case
    sh.putenv(foo, str_or_path("foo"))
    assert os.environ[foo] == "foo"

    # Variable value contains another variable that must be resolved
    sh.putenv(bar, f"${foo}/bar")
    assert os.environ[bar] == "foo/bar"

    # Delete variable when it exists
    sh.putenv(foo, None)
    assert foo not in os.environ

    # Delete variable when it does not exist
    sh.putenv(foo, None)
    assert foo not in os.environ

    # Set blank variable (not the same as setting None, which deletes it)
    sh.putenv(foo, "")
    assert os.environ[foo] == ""


def test_override_env(str_or_path):
    foo = get_name("foo")
    bar = get_name("bar")
    os.environ[bar] = "original"

    with sh.override_env(foo, str_or_path("foo")), sh.override_env(bar, f"${foo}/bar"):
        assert os.getenv(foo) == "foo"
        assert os.getenv(bar) == "foo/bar"

    assert foo not in os.environ
    assert os.environ[bar] == "original"

    # Test that the cleanup also happens in case of Exception
    with pytest.raises(StubError), sh.override_env(foo, "foo"):  # noqa: PT012
        assert os.getenv(foo) == "foo"
        raise StubError()
    assert "foo" not in os.environ
