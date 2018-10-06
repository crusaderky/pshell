import os
import pytest
import pshell as sh


def test_glob_iglob(tmpdir):
    os.environ['UNITTEST_BASH'] = str(tmpdir)

    # Create sample data
    results = [
        os.path.join(str(tmpdir), 'test%d.txt' % i)
        for i in (1, 2, 3)
    ]
    for fname in results:
        with open(fname, 'w'):
            pass

    # There's no guaranteed that glob will return the files in
    # alphabetical order
    assert sorted(sh.glob('$UNITTEST_BASH/test*.txt')) == results
    assert sorted(sh.iglob('$UNITTEST_BASH/test*.txt')) == results
    assert sorted(sh.glob('$UNITTEST_BASH/test*.txt',
                          min_results=3, max_results=3)) == results
    assert sorted(sh.iglob('$UNITTEST_BASH/test*.txt',
                           min_results=3, max_results=3)) == results

    # glob exceptions
    with pytest.raises(sh.FileMatchError) as e:
        sh.glob('$UNITTEST_BASH/test*.txt', min_results=4)
    assert str(e.value) == "File match '$UNITTEST_BASH/test*.txt' produced " \
                           "3 results, expected at least 4"

    with pytest.raises(sh.FileMatchError) as e:
        sh.glob('$UNITTEST_BASH/test*.txt', max_results=2)
    assert str(e.value) == "File match '$UNITTEST_BASH/test*.txt' produced " \
                           "3 results, expected up to 2"

    with pytest.raises(sh.FileMatchError) as e:
        sh.glob('$UNITTEST_BASH/test*.txt', min_results=1, max_results=2)
    assert str(e.value) == "File match '$UNITTEST_BASH/test*.txt' produced " \
                           "3 results, expected between 1 and 2"

    with pytest.raises(sh.FileMatchError) as e:
        sh.glob('$UNITTEST_BASH/test*.txt', min_results=2, max_results=2)
    assert str(e.value) == "File match '$UNITTEST_BASH/test*.txt' produced " \
                           "3 results, expected exactly 2"

    # iglob exceptions
    it = sh.iglob('$UNITTEST_BASH/test*.txt', max_results=1)
    # Make no assumption about the order
    assert next(it) in results
    with pytest.raises(sh.FileMatchError) as e:
        next(it)
    assert str(e.value) == "File match '$UNITTEST_BASH/test*.txt' produced " \
                           "2 or more results, expected up to 1"

    it = sh.iglob('$UNITTEST_BASH/notfound', min_results=1)
    with pytest.raises(sh.FileMatchError) as e:
        next(it)
    assert str(e.value) == "File match '$UNITTEST_BASH/notfound' produced " \
                           "0 results, expected at least 1"


def test_glob_iglob_recursive(tmpdir):
    # Test recursive glob and iglob

    # Create sample data
    expect = []
    tmpdir.mkdir('a').mkdir('b')
    tmpdir.mkdir('c')
    for d in (os.path.join('a', 'b'), 'c'):
        for i in (1, 2, 3):
            fname = os.path.join(str(tmpdir), d, 'test%d.txt' % i)
            expect.append(fname)
            with open(fname, 'w'):
                pass

    # Test recursive and non-recursive wildcards
    # Make no assumptions about order
    assert sorted(sh.glob('%s/**/*.txt' % tmpdir)) == expect
    assert sorted(sh.iglob('%s/**/*.txt' % tmpdir)) == expect
    assert sorted(sh.glob('%s/*/*.txt' % tmpdir)) == expect[3:]
    assert sorted(sh.iglob('%s/*/*.txt' % tmpdir)) == expect[3:]
