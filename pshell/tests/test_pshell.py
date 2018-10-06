import getpass
import gzip
import os
import subprocess
from nose.tools import eq_, raises, assert_raises
import pshell as sh


SAMPLEDIR = os.path.abspath(os.path.join(os.path.dirname(__file__), 'data'))
cwd_backup = None
tmpdir = None
BLURB = 'helloworld'


def clean_files():
    for pos, char in enumerate(BLURB):
        try:
            os.remove(os.path.join(tmpdir.name, str(pos) + '.txt'))
        except FileNotFoundError:
            pass


def check_fd_was_closed(fname):
    for symlink in glob.glob('/proc/self/fd/*'):
        assert not os.path.realpath(symlink).endswith(fname)


def test_check_fd_was_closed1():
    check_fd_was_closed('notexist')


@raises(AssertionError)
def test_check_fd_was_closed2():
    with open(tmpdir.name + '/test_open', 'w'):
        check_fd_was_closed('test_open')



def test_open_context():
    with sh.open('$LANDG_UNITTEST_BASH/test_open', 'w') as fh:
        fh.write("Hello world")
    check_fd_was_closed('test_open')
    with open(tmpdir.name + '/test_open') as fh:
        eq_(fh.read(), "Hello world")
    with sh.open('$LANDG_UNITTEST_BASH/test_open', 'a+') as fh:
        fh.write(" and universe")
    check_fd_was_closed('test_open')
    with sh.open('$LANDG_UNITTEST_BASH/test_open', 'r') as fh:
        eq_(fh.read(), "Hello world and universe")
    check_fd_was_closed('test_open')


def test_open_nocontext():
    fh = sh.open('$LANDG_UNITTEST_BASH/test_open', 'w')
    fh.write("Hello world")
    fh.close()
    check_fd_was_closed('test_open')
    with open(tmpdir.name + '/test_open') as fh:
        eq_(fh.read(), "Hello world")


def test_open_exclusive_success_context():
    sh.remove('$LANDG_UNITTEST_BASH/test_open', force=True)
    with sh.open('$LANDG_UNITTEST_BASH/test_open', 'x') as fh:
        fh.write("Hello world")
    check_fd_was_closed('test_open')
    with open(tmpdir.name + '/test_open') as fh:
        eq_(fh.read(), "Hello world")


def test_open_exclusive_success_nocontext():
    sh.remove('$LANDG_UNITTEST_BASH/test_open', force=True)
    fh = sh.open('$LANDG_UNITTEST_BASH/test_open', 'x')
    fh.write("Hello world")
    fh.close()
    check_fd_was_closed('test_open')
    with open(tmpdir.name + '/test_open') as fh:
        eq_(fh.read(), "Hello world")


@raises(FileExistsError)
def test_open_exclusive_failure():
    open(tmpdir.name + '/test_open', 'w').close()
    try:
        sh.open('$LANDG_UNITTEST_BASH/test_open', 'x')
    finally:
        check_fd_was_closed('test_open')


def test_open_encoding():
    TEXT = "Crème brûlée"
    TEXT_REPLACED = "Cr�me br�l�e"

    with open(tmpdir.name + '/test_utf8', 'w', encoding='utf-8') as fh:
        fh.write(TEXT)
    with open(tmpdir.name + '/test_latin1', 'w', encoding='latin1') as fh:
        fh.write(TEXT)

    # sh.open must always default to utf-8
    with sh.open(tmpdir.name + '/test_utf8') as fh:
        eq_(fh.read(), TEXT)
    with sh.open(tmpdir.name + '/test_latin1', encoding='latin1') as fh:
        eq_(fh.read(), TEXT)
    # sh.open must always default to replace unrecognized characters with ?
    with sh.open(tmpdir.name + '/test_latin1') as fh:
        eq_(fh.read(), TEXT_REPLACED)
    with assert_raises(UnicodeDecodeError):
        with sh.open(tmpdir.name + '/test_latin1', errors='strict') as fh:
            fh.read()


def test_open_fd():
    r, w = os.pipe()
    with sh.open(r, 'rb', buffering=0) as fh_r:
        with sh.open(w, 'wb', buffering=0) as fh_w:
            fh_w.write(b'hello world\n')
            eq_(fh_r.readline(), b'hello world\n')


def test_gzip_open_read_default_mode():
    # Test that bash.gzip_open reads files in text mode by default
    with gzip.open(f'{tmpdir.name}/test_gzip_open_mode.gz', 'wt') as fh:
        fh.write('Hello world')
    with sh.gzip_open(f'{tmpdir.name}/test_gzip_open_mode.gz') as fh:
        eq_(fh.read(), 'Hello world')


def test_gzip_open_write_default_mode():
    # Test that bash.gzip_open writes files in text mode by default
    with sh.gzip_open(f'{tmpdir.name}/test_gzip_open_mode.gz', 'w') as fh:
        fh.write('Hello world')
    with gzip.open(f'{tmpdir.name}/test_gzip_open_mode.gz', 'rt') as fh:
        eq_(fh.read(), 'Hello world')


def test_gzip_open_read_text_mode():
    with gzip.open(f'{tmpdir.name}/test_gzip_open_mode.gz', 'wt') as fh:
        fh.write('Hello world')
    with sh.gzip_open(f'{tmpdir.name}/test_gzip_open_mode.gz', 'rt') as fh:
        eq_(fh.read(), 'Hello world')


def test_gzip_open_write_text_mode():
    with sh.gzip_open(f'{tmpdir.name}/test_gzip_open_mode.gz', 'wt') as fh:
        fh.write('Hello world')
    with gzip.open(f'{tmpdir.name}/test_gzip_open_mode.gz', 'rt') as fh:
        eq_(fh.read(), 'Hello world')


def test_gzip_open_read_binary_mode():
    with gzip.open(f'{tmpdir.name}/test_gzip_open_mode.gz', 'w') as fh:
        fh.write(b'Hello world')
    with sh.gzip_open(f'{tmpdir.name}/test_gzip_open_mode.gz', 'rb') as fh:
        eq_(fh.read(), b'Hello world')


def test_gzip_open_write_binary_mode():
    with sh.gzip_open(f'{tmpdir.name}/test_gzip_open_mode.gz', 'wb') as fh:
        fh.write(b'Hello world')
    with gzip.open(f'{tmpdir.name}/test_gzip_open_mode.gz', 'r') as fh:
        eq_(fh.read(), b'Hello world')


def test_gzip_open_unzipped_nocontext():
    fh = sh.gzip_open('$LANDG_UNITTEST_BASH/test_gzip_open', 'w')
    fh.write("Hello world")
    fh.close()
    check_fd_was_closed('test_gzip_open')
    with open(tmpdir.name + '/test_gzip_open') as fh:
        eq_(fh.read(), "Hello world")


def test_gzip_open_nocontext():
    fh = sh.gzip_open('$LANDG_UNITTEST_BASH/test_gzip_open.gz', 'w')
    fh.write("Hello world")
    fh.close()
    check_fd_was_closed('test_gzip_open.gz')
    with gzip.open(tmpdir.name + '/test_gzip_open.gz', 'rt') as fh:
        eq_(fh.read(), "Hello world")


def test_gzip_open_unzipped_exclusive_success_context():
    sh.remove('$LANDG_UNITTEST_BASH/test_gzip_open', force=True)
    with sh.gzip_open('$LANDG_UNITTEST_BASH/test_gzip_open', 'x') as fh:
        fh.write("Hello world")
    check_fd_was_closed('test_gzip_open')
    with open(tmpdir.name + '/test_gzip_open') as fh:
        eq_(fh.read(), "Hello world")


def test_gzip_open_exclusive_success_context():
    sh.remove('$LANDG_UNITTEST_BASH/test_gzip_open.gz', force=True)
    with sh.gzip_open('$LANDG_UNITTEST_BASH/test_gzip_open.gz', 'x') as fh:
        fh.write("Hello world")
    check_fd_was_closed('test_gzip_open.gz')
    with gzip.open(tmpdir.name + '/test_gzip_open.gz', 'rt') as fh:
        eq_(fh.read(), "Hello world")


def test_gzip_open_exclusive_success_nocontext():
    sh.remove('$LANDG_UNITTEST_BASH/test_gzip_open.gz', force=True)
    fh = sh.gzip_open('$LANDG_UNITTEST_BASH/test_gzip_open.gz', 'x')
    fh.write("Hello world")
    fh.close()
    check_fd_was_closed('test_gzip_open.gz')
    with gzip.open(f'{tmpdir.name}/test_gzip_open.gz', 'rt') as fh:
        eq_(fh.read(), "Hello world")


def test_gzip_open_unzipped_exclusive_success_nocontext():
    sh.remove('$LANDG_UNITTEST_BASH/test_gzip_open', force=True)
    fh = sh.gzip_open('$LANDG_UNITTEST_BASH/test_gzip_open', 'x')
    fh.write("Hello world")
    fh.close()
    check_fd_was_closed('test_gzip_open')
    with open(f'{tmpdir.name}/test_gzip_open') as fh:
        eq_(fh.read(), "Hello world")


@raises(FileExistsError)
def test_gzip_open_exclusive_failure():
    gzip.open(f'{tmpdir.name}/test_gzip_open.gz', 'w').close()
    try:
        sh.gzip_open('$LANDG_UNITTEST_BASH/test_gzip_open.gz', 'x')
    finally:
        check_fd_was_closed('test_gzip_open.gz')


@raises(FileExistsError)
def test_gzip_open_unzipped_exclusive_failure():
    open(f'{tmpdir.name}/test_gzip_open', 'w').close()
    try:
        sh.gzip_open('$LANDG_UNITTEST_BASH/test_gzip_open', 'x')
    finally:
        check_fd_was_closed('test_gzip_open')


def test_gzip_open_encoding():
    TEXT = "Crème brûlée"
    TEXT_REPLACED = "Cr�me br�l�e"

    with gzip.open(f'{tmpdir.name}/test_gzip_utf8.gz', 'wt', encoding='utf-8') as fh:
        fh.write(TEXT)
    with gzip.open(f'{tmpdir.name}/test_gzip_latin1.gz', 'wt', encoding='latin1') as fh:
        fh.write(TEXT)

    # sh.gzip_open must always default to utf-8
    with sh.gzip_open(f'{tmpdir.name}/test_gzip_utf8.gz') as fh:
        eq_(fh.read(), TEXT)
    with sh.gzip_open(f'{tmpdir.name}/test_gzip_latin1.gz', encoding='latin1') as fh:
        eq_(fh.read(), TEXT)
    # sh.gzip_open must always default to replace unrecognized characters with ?
    with sh.gzip_open(f'{tmpdir.name}/test_gzip_latin1.gz') as fh:
        eq_(fh.read(), TEXT_REPLACED)
    with assert_raises(UnicodeDecodeError):
        with sh.gzip_open(f'{tmpdir.name}/test_gzip_latin1.gz', errors='strict') as fh:
            fh.read()


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


def test_owner():
    # Create sample file
    with open(tmpdir.name + "/test_owner", 'w'):
        pass

    eq_(sh.owner('$LANDG_UNITTEST_BASH/test_owner'), getpass.getuser())


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
