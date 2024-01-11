import os
import pickle
from pathlib import Path

import pytest

import pshell as sh


def test_glob_iglob(str_or_path, tmpdir):
    os.environ["UNITTEST_BASH"] = str(tmpdir)

    # Create sample data
    results = [
        str_or_path(os.path.join(str(tmpdir), f"test{i}.txt")) for i in (1, 2, 3)
    ]
    for fname in results:
        with open(fname, "w"):
            pass

    # There's no guaranteed that glob will return the files in
    # alphabetical order
    assert sorted(sh.glob(str_or_path("$UNITTEST_BASH/test*.txt"))) == results
    assert sorted(sh.iglob(str_or_path("$UNITTEST_BASH/test*.txt"))) == results
    assert (
        sorted(
            sh.glob(
                str_or_path("$UNITTEST_BASH/test*.txt"), min_results=3, max_results=3
            )
        )
        == results
    )
    assert (
        sorted(
            sh.iglob(
                str_or_path("$UNITTEST_BASH/test*.txt"), min_results=3, max_results=3
            )
        )
        == results
    )

    # glob exceptions
    f = str_or_path("$UNITTEST_BASH/test*.txt")
    with pytest.raises(sh.FileMatchError) as e:
        sh.glob(f, min_results=4)
    assert str(e.value) == f"File match '{f}' produced 3 results; expected at least 4"

    with pytest.raises(sh.FileMatchError) as e:
        sh.glob(f, max_results=2)
    assert str(e.value) == f"File match '{f}' produced 3 results; expected up to 2"

    with pytest.raises(sh.FileMatchError) as e:
        sh.glob(f, min_results=1, max_results=2)
    assert (
        str(e.value) == f"File match '{f}' produced 3 results; expected between 1 and 2"
    )

    with pytest.raises(sh.FileMatchError) as e:
        sh.glob(f, min_results=2, max_results=2)
    assert str(e.value) == f"File match '{f}' produced 3 results; expected exactly 2"

    # iglob exceptions
    it = sh.iglob(f, max_results=1)
    # Make no assumption about the order
    assert next(it) in results
    with pytest.raises(sh.FileMatchError) as e:
        next(it)
    assert (
        str(e.value)
        == f"File match '{f}' produced at least 2 results; expected up to 1"
    )

    f = str_or_path("$UNITTEST_BASH/notfound.txt")
    it = sh.iglob(f, min_results=1)
    with pytest.raises(sh.FileMatchError) as e:
        next(it)
    assert str(e.value) == f"File match '{f}' produced 0 results; expected at least 1"


def test_glob_iglob_recursive(tmpdir):
    # Test recursive glob and iglob

    # Create sample data
    expect = []
    tmpdir.mkdir("a").mkdir("b")
    tmpdir.mkdir("c")
    for d in (os.path.join("a", "b"), "c"):
        for i in (1, 2, 3):
            fname = os.path.join(str(tmpdir), d, f"test{i}.txt")
            expect.append(fname)
            with open(fname, "w"):
                pass

    # Test recursive and non-recursive wildcards
    # Make no assumptions about order
    assert sorted(sh.glob(f"{tmpdir}/**/*.txt")) == expect
    assert sorted(sh.iglob(f"{tmpdir}/**/*.txt")) == expect
    assert sorted(sh.glob(f"{tmpdir}/*/*.txt")) == expect[3:]
    assert sorted(sh.iglob(f"{tmpdir}/*/*.txt")) == expect[3:]


def test_glob_iglob_bad_args():
    with pytest.raises(ValueError):
        sh.glob(".", min_results=-1)
    with pytest.raises(ValueError):
        next(sh.iglob(".", min_results=-1))
    with pytest.raises(ValueError):
        sh.glob(".", min_results=2, max_results=1)
    with pytest.raises(ValueError):
        next(sh.iglob(".", min_results=2, max_results=1))


@pytest.mark.parametrize(
    "args,s",
    [
        (
            ("foo", 1, None, 0),
            "File match 'foo' produced 0 results; expected at least 1",
        ),
        (
            (Path("foo"), 1, None, 0),
            "File match 'foo' produced 0 results; expected at least 1",
        ),
        (("foo", 1, 1, 0), "File match 'foo' produced 0 results; expected exactly 1"),
        (
            ("foo", 2, 3, 0),
            "File match 'foo' produced 0 results; expected between 2 and 3",
        ),
        (("foo", 0, 3, 4), "File match 'foo' produced 4 results; expected up to 3"),
        (
            ("foo", 0, 3, 4, True),
            "File match 'foo' produced at least 4 results; expected up to 3",
        ),
    ],
)
def test_filematcherror(args, s):
    e = sh.FileMatchError(*args)
    assert str(e) == s
    # Exception with required arguments typically fail to unpickle
    e2 = pickle.loads(pickle.dumps(e))
    assert str(e2) == s
