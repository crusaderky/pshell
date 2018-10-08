import bz2
import gzip
import lzma
import os
import psutil
import pytest
import pshell as sh


compression_param = pytest.mark.parametrize(
    'openfunc,ext,compression', [
        (open, '', 'auto'),
        (gzip.open, '.gz', 'auto'),
        (bz2.open, '.bz2', 'auto'),
        (lzma.open, '.xz', 'auto'),
        (gzip.open, '.GZ', 'auto'),
        (bz2.open, '.BZ2', 'auto'),
        (lzma.open, '.XZ', 'auto'),
        (open, '', False),
        (gzip.open, '', 'gzip'),
        (bz2.open, '', 'bzip2'),
        (lzma.open, '', 'lzma'),
    ])


def check_fd_was_closed(fname):
    fname = os.path.basename(fname)
    for tup in psutil.Process().open_files():
        assert fname not in tup.path


def test_check_fd_was_closed(tmpdir):
    check_fd_was_closed('notexist')
    with open('%s/test_open.123' % tmpdir, 'w'):
        with pytest.raises(AssertionError):
            check_fd_was_closed('test_open')
    check_fd_was_closed('test_open')


@compression_param
def test_open_context(tmpdir, openfunc, ext, compression):
    os.environ['UNITTEST_BASH'] = str(tmpdir)
    fname = '%s/test_open%s' % (tmpdir, ext)
    fname_env = '$UNITTEST_BASH/test_open%s' % ext

    with sh.open(fname_env, 'w', compression=compression) as fh:
        fh.write("Hello world")
    check_fd_was_closed('test_open')
    with openfunc(fname, 'rt') as fh:
        assert fh.read() == "Hello world"
    with sh.open(fname_env, 'a', compression=compression) as fh:
        fh.write(" and universe")
    check_fd_was_closed('test_open')
    with sh.open(fname_env, 'r', compression=compression) as fh:
        assert fh.read() == "Hello world and universe"
    check_fd_was_closed('test_open')


@compression_param
def test_open_nocontext(tmpdir, openfunc, ext, compression):
    fname = '%s/test_open%s' % (tmpdir, ext)
    fh = sh.open(fname, 'w', compression=compression)
    fh.write("Hello world")
    fh.close()
    check_fd_was_closed('test_open')
    with openfunc(fname, 'rt') as fh:
        assert fh.read() == "Hello world"


@compression_param
def test_open_exclusive_success(tmpdir, openfunc, ext, compression):
    fname = '%s/test_open%s' % (tmpdir, ext)
    with sh.open(fname, 'x', compression=compression) as fh:
        fh.write("Hello world")
    with openfunc(fname, 'rt') as fh:
        assert fh.read() == "Hello world"


@compression_param
def test_open_exclusive_failure(tmpdir, openfunc, ext, compression):
    fname = '%s/test_open%s' % (tmpdir, ext)
    with open(fname, 'w'):
        pass
    with pytest.raises(FileExistsError):
        sh.open(fname, 'x', compression=compression)


@compression_param
def test_open_binary(tmpdir, openfunc, ext, compression):
    fname = '%s/test_open%s' % (tmpdir, ext)

    with sh.open(fname, 'wb', compression=compression) as fh:
        fh.write(b"Hello world")
    with openfunc(fname, 'rb') as fh:
        assert fh.read() == b"Hello world"
    with sh.open(fname, 'ab', compression=compression) as fh:
        fh.write(b" and universe")
    with sh.open(fname, 'rb', compression=compression) as fh:
        assert fh.read() == b"Hello world and universe"


@compression_param
def test_open_encoding(tmpdir, openfunc, ext, compression):
    TEXT = "Crème brûlée"
    TEXT_REPLACED = "Cr�me br�l�e"
    fname_utf8 = '%s/test_utf8%s' % (tmpdir, ext)
    fname_latin1 = '%s/test_latin1%s' % (tmpdir, ext)

    with openfunc(fname_utf8, 'wt', encoding='utf-8') as fh:
        fh.write(TEXT)
    with openfunc(fname_latin1, 'wt', encoding='latin1') as fh:
        fh.write(TEXT)

    # sh.open must always default to utf-8
    with sh.open(fname_utf8, compression=compression) as fh:
        assert fh.read() == TEXT
    with sh.open(fname_latin1, compression=compression,
                 encoding='latin1') as fh:
        assert fh.read() == TEXT
    # sh.open must always default to replace unrecognized characters with ?
    with sh.open(fname_latin1, compression=compression) as fh:
        assert fh.read() == TEXT_REPLACED
    with pytest.raises(UnicodeDecodeError):
        with sh.open(fname_latin1, errors='strict',
                     compression=compression) as fh:
            fh.read()


@compression_param
@pytest.mark.parametrize('newline', ['\n', '\r', '\r\n'])
def test_open_kwargs(tmpdir, openfunc, ext, compression, newline):
    # **kwargs are passed verbatim to the underlying function
    fname = '%s/test_open%s' % (tmpdir, ext)

    with sh.open(fname, 'w', compression=compression, newline=newline) as fh:
        fh.write("Hello\nworld")
    with openfunc(fname, 'rb') as fh:
        assert fh.read() == b"Hello" + newline.encode('utf8') + b"world"


# no compression support
def test_open_fd():
    r, w = os.pipe()
    with sh.open(r, 'rb', buffering=0) as fh_r:
        with sh.open(w, 'wb', buffering=0) as fh_w:
            fh_w.write(b'hello world\n')
            assert fh_r.readline() == b'hello world\n'
