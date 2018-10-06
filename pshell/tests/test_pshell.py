import os
import subprocess
from nose.tools import eq_
import pshell as sh


SAMPLEDIR = os.path.abspath(os.path.join(os.path.dirname(__file__), 'data'))
cwd_backup = None
tmpdir = None
BLURB = 'helloworld'


def test_find_kill_procs():
    # Test landg.bash.find_procs_by_cmdline and landg.bash.kill_procs
    cmdline = f'{SAMPLEDIR}/test_proc.sh'

    pids_before = sh.find_procs_by_cmdline(cmdline)
    subprocess.check_call(cmdline + ' &', shell=True)

    pids_after = sh.find_procs_by_cmdline(cmdline)
    eq_(len(pids_after), len(pids_before) + 1)

    # Test substrings and OR'ed matches
    eq_(pids_after, sh.find_procs_by_cmdline(
        'landg unit test this wont match anything',
        'tests/data/test_proc'
    ))

    sh.kill_procs(pids_after)
    eq_(sh.find_procs_by_cmdline(cmdline), [])


def test_glob():
    # Test glob and iglob

    # Create sample data
    with open(tmpdir.name + "/test1.txt", "w"):
        pass
    with open(tmpdir.name + "/test2.txt", "w"):
        pass
    with open(tmpdir.name + "/test3.txt", "w"):
        pass

    results = [
        tmpdir.name + '/test1.txt',
        tmpdir.name + '/test2.txt',
        tmpdir.name + '/test3.txt',
    ]

    # There's no guaranteed that glob will return the files in alphabetical order
    eq_(sorted(sh.glob('$LANDG_UNITTEST_BASH/test*.txt')), results)
    eq_(sorted(sh.iglob('$LANDG_UNITTEST_BASH/test*.txt')), results)
    eq_(sorted(sh.glob('$LANDG_UNITTEST_BASH/test*.txt', min_results=3, max_results=3)), results)
    eq_(sorted(sh.iglob('$LANDG_UNITTEST_BASH/test*.txt', min_results=3, max_results=3)), results)

    # glob exceptions
    try:
        sh.glob('$LANDG_UNITTEST_BASH/test*.txt', min_results=4)
    except sh.FileMatchError as e:
        eq_(str(e), r"File match '$LANDG_UNITTEST_BASH/test*.txt' produced 3 results, expected at least 4")
    else:
        assert False

    try:
        sh.glob('$LANDG_UNITTEST_BASH/test*.txt', max_results=2)
    except sh.FileMatchError as e:
        eq_(str(e), r"File match '$LANDG_UNITTEST_BASH/test*.txt' produced 3 results, expected up to 2")
    else:
        assert False

    try:
        sh.glob('$LANDG_UNITTEST_BASH/test*.txt', min_results=1, max_results=2)
    except sh.FileMatchError as e:
        eq_(str(e), r"File match '$LANDG_UNITTEST_BASH/test*.txt' produced 3 results, expected between 1 and 2")
    else:
        assert False

    try:
        sh.glob('$LANDG_UNITTEST_BASH/test*.txt', min_results=2, max_results=2)
    except sh.FileMatchError as e:
        eq_(str(e), r"File match '$LANDG_UNITTEST_BASH/test*.txt' produced 3 results, expected exactly 2")
    else:
        assert False

    #iglob exceptions
    iter = sh.iglob('$LANDG_UNITTEST_BASH/test*.txt', max_results=1)
    # Make no assumption about the order
    assert next(iter) in results
    try:
        next(iter)
    except sh.FileMatchError as e:
        eq_(str(e), r"File match '$LANDG_UNITTEST_BASH/test*.txt' produced 2 or more results, expected up to 1")
    else:
        assert False

    iter = sh.iglob('$LANDG_UNITTEST_BASH/notfound', min_results=1)
    try:
        next(iter)
    except sh.FileMatchError as e:
        eq_(str(e), r"File match '$LANDG_UNITTEST_BASH/notfound' produced 0 results, expected at least 1")
    else:
        assert False


def test_glob_recursive():
    # Test recursive glob and iglob

    # Create sample data
    testpath = tmpdir.name + '/test_glob_recursive'
    os.mkdir(testpath)
    assert os.path.exists(testpath)
    with open(testpath + "/test1.txt", "w"):
        pass
    with open(testpath + "/test2.txt", "w"):
        pass
    with open(testpath + "/test3.txt", "w"):
        pass
    testpath2 = testpath + '/test_remove_level2'
    os.mkdir(testpath2)
    assert os.path.exists(testpath2)
    with open(testpath2 + "/test1.txt", "w"):
        pass
    with open(testpath2 + "/test2.txt", "w"):
        pass
    with open(testpath2 + "/test3.txt", "w"):
        pass

    # Test recursive and non-recursive wildcards
    eq_(len(sh.glob(testpath + '/**/*.txt')), 6)
    eq_(len(list(sh.iglob(testpath + '/**/*.txt'))), 6)
    eq_(len(sh.glob(testpath + '/*/*.txt')), 3)
    eq_(len(list(sh.iglob(testpath + '/*/*.txt'))), 3)


def test_concatenate1():
    # Output file already exists and is non-empty. Files end without a newline.
    clean_files()
    filenames = [
        os.path.join(tmpdir.name, f'{pos}.txt')
        for pos, char in enumerate(BLURB)
    ]

    for fname, char in zip(filenames, BLURB):
        with open(fname, 'w') as fh:
            fh.write(char)

    sh.concatenate(*filenames)

    with open(filenames[0]) as fh:
        concatenated_file_contents = fh.readlines()

    assert concatenated_file_contents == [el + '\n' for el in BLURB]


def test_concatenate2():
    # Output file already exists and is non-empty. Files end with a newline.
    clean_files()
    filenames = [
        os.path.join(tmpdir.name, f'{pos}.txt')
        for pos, char in enumerate(BLURB)
    ]

    for fname, char in zip(filenames, BLURB):
        with open(fname, 'w') as fh:
            fh.write(char + '\n')

    sh.concatenate(*filenames)

    with open(filenames[0]) as fh:
        concatenated_file_contents = fh.readlines()

    assert concatenated_file_contents == [el + '\n' for el in BLURB]


def test_concatenate3():
    # Output file already exists and it is empty
    clean_files()
    filenames = [
        os.path.join(tmpdir.name, f'{pos}.txt')
        for pos, char in enumerate(BLURB)
    ]

    with open(filenames[0], 'w') as fh:
        pass
    for fname, char in zip(filenames[1:], BLURB[1:]):
        with open(fname, 'w') as fh:
            fh.write(char)

    sh.concatenate(*filenames)

    with open(filenames[0]) as fh:
        concatenated_file_contents = fh.readlines()

    assert concatenated_file_contents == [el + '\n' for el in BLURB[1:]]


def test_concatenate4():
    # Output file does not already exist
    clean_files()
    filenames = [
        os.path.join(tmpdir.name, f'{pos}.txt')
        for pos, char in enumerate(BLURB)
    ]

    for fname, char in zip(filenames[1:], BLURB[1:]):
        with open(fname, 'w') as fh:
            fh.write(char)

    sh.concatenate(*filenames)

    with open(filenames[0]) as fh:
        concatenated_file_contents = fh.readlines()

    assert concatenated_file_contents == [el + '\n' for el in BLURB[1:]]
