import glob
import gzip
import os
import pytest
import pshell as sh


def check_fd_was_closed(fname):
    for symlink in glob.glob('/proc/self/fd/*'):
        assert not os.path.realpath(symlink).endswith(fname)


def test_check_fd_was_closed(tmpdir):
    check_fd_was_closed('notexist')
    with open('%s/test_open' % tmpdir, 'w'):
        with pytest.raises(AssertionError):
            check_fd_was_closed('test_open')


def test_open_context(tmpdir):
    os.environ['UNITTEST_BASH'] = str(tmpdir)
    with sh.open('$UNITTEST_BASH/test_open', 'w') as fh:
        fh.write("Hello world")
    check_fd_was_closed('test_open')
    with open('%s/test_open' % tmpdir) as fh:
        assert fh.read() == "Hello world"
    with sh.open('$UNITTEST_BASH/test_open', 'a+') as fh:
        fh.write(" and universe")
    check_fd_was_closed('test_open')
    with sh.open('$UNITTEST_BASH/test_open', 'r') as fh:
        assert fh.read() == "Hello world and universe"
    check_fd_was_closed('test_open')


def test_open_nocontext(tmpdir):
    os.environ['UNITTEST_BASH'] = str(tmpdir)
    fh = sh.open('$UNITTEST_BASH/test_open', 'w')
    fh.write("Hello world")
    fh.close()
    check_fd_was_closed('test_open')
    with open('%s/test_open' % tmpdir) as fh:
        assert fh.read() == "Hello world"


def test_open_exclusive_success_context(tmpdir):
    os.environ['UNITTEST_BASH'] = str(tmpdir)
    with sh.open('$UNITTEST_BASH/test_open', 'x') as fh:
        fh.write("Hello world")
    check_fd_was_closed('test_open')
    with open('%s/test_open' % tmpdir) as fh:
        assert fh.read() == "Hello world"


def test_open_exclusive_success_nocontext(tmpdir):
    os.environ['UNITTEST_BASH'] = str(tmpdir)
    fh = sh.open('$UNITTEST_BASH/test_open', 'x')
    fh.write("Hello world")
    fh.close()
    check_fd_was_closed('test_open')
    with open('%s/test_open' % tmpdir) as fh:
        assert fh.read() == "Hello world"


def test_open_exclusive_failure(tmpdir):
    os.environ['UNITTEST_BASH'] = str(tmpdir)
    open('%s/test_open' % tmpdir, 'w').close()
    with pytest.raises(FileExistsError):
        sh.open('$UNITTEST_BASH/test_open', 'x')
    check_fd_was_closed('test_open')


def test_open_encoding(tmpdir):
    TEXT = "Crème brûlée"
    TEXT_REPLACED = "Cr�me br�l�e"

    with open('%s/test_utf8' % tmpdir, 'w', encoding='utf-8') as fh:
        fh.write(TEXT)
    with open('%s/test_latin1' % tmpdir, 'w', encoding='latin1') as fh:
        fh.write(TEXT)

    # sh.open must always default to utf-8
    with sh.open('%s/test_utf8' % tmpdir) as fh:
        assert fh.read() == TEXT
    with sh.open('%s/test_latin1' % tmpdir, encoding='latin1') as fh:
        assert fh.read() == TEXT
    # sh.open must always default to replace unrecognized characters with ?
    with sh.open('%s/test_latin1' % tmpdir) as fh:
        assert fh.read() == TEXT_REPLACED
    with pytest.raises(UnicodeDecodeError):
        with sh.open('%s/test_latin1' % tmpdir, errors='strict') as fh:
            fh.read()


def test_open_fd():
    r, w = os.pipe()
    with sh.open(r, 'rb', buffering=0) as fh_r:
        with sh.open(w, 'wb', buffering=0) as fh_w:
            fh_w.write(b'hello world\n')
            assert fh_r.readline() == b'hello world\n'


def test_gzip_open_read_default_mode(tmpdir):
    # Test that bash.gzip_open reads files in text mode by default
    with gzip.open('%s/test_gzip_open_mode.gz' % tmpdir, 'wt') as fh:
        fh.write("Hello world")
    with sh.gzip_open('%s/test_gzip_open_mode.gz' % tmpdir) as fh:
        assert fh.read() == "Hello world"


def test_gzip_open_write_default_mode(tmpdir):
    # Test that bash.gzip_open writes files in text mode by default
    with sh.gzip_open('%s/test_gzip_open_mode.gz' % tmpdir, 'w') as fh:
        fh.write("Hello world")
    with gzip.open('%s/test_gzip_open_mode.gz' % tmpdir, 'rt') as fh:
        assert fh.read() == "Hello world"


def test_gzip_open_read_text_mode(tmpdir):
    with gzip.open('%s/test_gzip_open_mode.gz' % tmpdir, 'wt') as fh:
        fh.write("Hello world")
    with sh.gzip_open('%s/test_gzip_open_mode.gz' % tmpdir, 'rt') as fh:
        assert fh.read() == "Hello world"


def test_gzip_open_write_text_mode(tmpdir):
    with sh.gzip_open('%s/test_gzip_open_mode.gz' % tmpdir, 'wt') as fh:
        fh.write("Hello world")
    with gzip.open('%s/test_gzip_open_mode.gz' % tmpdir, 'rt') as fh:
        assert fh.read() == "Hello world"


def test_gzip_open_read_binary_mode(tmpdir):
    with gzip.open('%s/test_gzip_open_mode.gz' % tmpdir, 'w') as fh:
        fh.write(b"Hello world")
    with sh.gzip_open('%s/test_gzip_open_mode.gz' % tmpdir, 'rb') as fh:
        assert fh.read() == b"Hello world"


def test_gzip_open_write_binary_mode(tmpdir):
    with sh.gzip_open('%s/test_gzip_open_mode.gz' % tmpdir, 'wb') as fh:
        fh.write(b"Hello world")
    with gzip.open('%s/test_gzip_open_mode.gz' % tmpdir, 'r') as fh:
        assert fh.read() == b"Hello world"


def test_gzip_open_unzipped_nocontext(tmpdir):
    os.environ['UNITTEST_BASH'] = str(tmpdir)
    fh = sh.gzip_open('$UNITTEST_BASH/test_gzip_open', 'w')
    fh.write("Hello world")
    fh.close()
    check_fd_was_closed('test_gzip_open')
    with open('%s/test_gzip_open' % tmpdir) as fh:
        assert fh.read() == "Hello world"


def test_gzip_open_nocontext(tmpdir):
    os.environ['UNITTEST_BASH'] = str(tmpdir)
    fh = sh.gzip_open('$UNITTEST_BASH/test_gzip_open.gz', 'w')
    fh.write("Hello world")
    fh.close()
    check_fd_was_closed('test_gzip_open.gz')
    with gzip.open('%s/test_gzip_open.gz' % tmpdir, 'rt') as fh:
        assert fh.read() == "Hello world"


def test_gzip_open_unzipped_exclusive_success_context(tmpdir):
    os.environ['UNITTEST_BASH'] = str(tmpdir)
    with sh.gzip_open('$UNITTEST_BASH/test_gzip_open', 'x') as fh:
        fh.write("Hello world")
    check_fd_was_closed('test_gzip_open')
    with open('%s/test_gzip_open' % tmpdir) as fh:
        assert fh.read() == "Hello world"


def test_gzip_open_exclusive_success_context(tmpdir):
    os.environ['UNITTEST_BASH'] = str(tmpdir)
    with sh.gzip_open('$UNITTEST_BASH/test_gzip_open.gz', 'x') as fh:
        fh.write("Hello world")
    check_fd_was_closed('test_gzip_open.gz')
    with gzip.open('%s/test_gzip_open.gz' % tmpdir, 'rt') as fh:
        assert fh.read() == "Hello world"


def test_gzip_open_exclusive_success_nocontext(tmpdir):
    os.environ['UNITTEST_BASH'] = str(tmpdir)
    fh = sh.gzip_open('$UNITTEST_BASH/test_gzip_open.gz', 'x')
    fh.write("Hello world")
    fh.close()
    check_fd_was_closed('test_gzip_open.gz')
    with gzip.open('%s/test_gzip_open.gz' % tmpdir, 'rt') as fh:
        assert fh.read() == "Hello world"


def test_gzip_open_unzipped_exclusive_success_nocontext(tmpdir):
    os.environ['UNITTEST_BASH'] = str(tmpdir)
    fh = sh.gzip_open('$UNITTEST_BASH/test_gzip_open', 'x')
    fh.write("Hello world")
    fh.close()
    check_fd_was_closed('test_gzip_open')
    with open('%s/test_gzip_open' % tmpdir) as fh:
        assert fh.read() == "Hello world"


def test_gzip_open_exclusive_failure(tmpdir):
    open('%s/test_gzip_open.gz' % tmpdir, 'w').close()
    with pytest.raises(FileExistsError):
        sh.gzip_open('%s/test_gzip_open.gz' % tmpdir, 'x')
    check_fd_was_closed('test_gzip_open.gz')


def test_gzip_open_unzipped_exclusive_failure(tmpdir):
    open('%s/test_gzip_open' % tmpdir, 'w').close()
    with pytest.raises(FileExistsError):
        sh.gzip_open('%s/test_gzip_open' % tmpdir, 'x')
    check_fd_was_closed('test_gzip_open')


def test_gzip_open_encoding(tmpdir):
    TEXT = "Crème brûlée"
    TEXT_REPLACED = "Cr�me br�l�e"

    with gzip.open('%s/test_gzip_utf8.gz' % tmpdir,
                   'wt', encoding='utf-8') as fh:
        fh.write(TEXT)
    with gzip.open('%s/test_gzip_latin1.gz' % tmpdir,
                   'wt', encoding='latin1') as fh:
        fh.write(TEXT)

    # sh.gzip_open must always default to utf-8
    with sh.gzip_open('%s/test_gzip_utf8.gz' % tmpdir) as fh:
        assert fh.read() == TEXT
    with sh.gzip_open('%s/test_gzip_latin1.gz' % tmpdir,
                      encoding='latin1') as fh:
        assert fh.read() == TEXT
    # sh.gzip_open must always default to replace
    # unrecognized characters with ?
    with sh.gzip_open('%s/test_gzip_latin1.gz' % tmpdir) as fh:
        assert fh.read() == TEXT_REPLACED
    with pytest.raises(UnicodeDecodeError):
        with sh.gzip_open('%s/test_gzip_latin1.gz' % tmpdir,
                          errors='strict') as fh:
            fh.read()
