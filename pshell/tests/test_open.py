import bz2
import gzip
import io
import lzma
import os

import psutil
import pytest

import pshell as sh

compression_param = pytest.mark.parametrize(
    "openfunc,ext,compression",
    [
        (open, "", "auto"),
        (gzip.open, ".gz", "auto"),
        (bz2.open, ".bz2", "auto"),
        (lzma.open, ".xz", "auto"),
        (gzip.open, ".GZ", "auto"),
        (bz2.open, ".BZ2", "auto"),
        (lzma.open, ".XZ", "auto"),
        (open, "", False),
        (gzip.open, "", "gzip"),
        (bz2.open, "", "bzip2"),
        (lzma.open, "", "lzma"),
    ],
)


def check_fd_was_closed(fname):
    fname = os.path.basename(fname)
    for tup in psutil.Process().open_files():
        assert fname not in tup.path


def test_check_fd_was_closed(tmpdir):
    check_fd_was_closed("notexist")
    with open(f"{tmpdir}/test_open.123", "w"), pytest.raises(AssertionError):
        check_fd_was_closed("test_open")
    check_fd_was_closed("test_open")


@compression_param
def test_open_context(str_or_path, tmpdir, openfunc, ext, compression):
    os.environ["UNITTEST_BASH"] = str(tmpdir)
    fname = f"{tmpdir}/test_open{ext}"
    fname_env = str_or_path(f"$UNITTEST_BASH/test_open{ext}")

    with sh.open(fname_env, "w", compression=compression) as fh:
        fh.write("Hello world")
    check_fd_was_closed("test_open")
    with openfunc(fname, "rt") as fh:
        assert fh.read() == "Hello world"
    with sh.open(fname_env, "a", compression=compression) as fh:
        fh.write(" and universe")
    check_fd_was_closed("test_open")
    with sh.open(fname_env, "r", compression=compression) as fh:
        assert fh.read() == "Hello world and universe"
    check_fd_was_closed("test_open")


@compression_param
def test_open_nocontext(str_or_path, tmpdir, openfunc, ext, compression):
    fname = str_or_path(f"{tmpdir}/test_open{ext}")
    fh = sh.open(fname, "w", compression=compression)
    fh.write("Hello world")
    fh.close()
    check_fd_was_closed("test_open")
    with openfunc(fname, "rt") as fh:
        assert fh.read() == "Hello world"


@compression_param
def test_open_exclusive_success(str_or_path, tmpdir, openfunc, ext, compression):
    fname = str_or_path(f"{tmpdir}/test_open{ext}")
    with sh.open(fname, "x", compression=compression) as fh:
        fh.write("Hello world")
    with openfunc(fname, "rt") as fh:
        assert fh.read() == "Hello world"


@compression_param
def test_open_exclusive_failure(tmpdir, openfunc, ext, compression):
    fname = f"{tmpdir}/test_open{ext}"
    with open(fname, "w"):
        pass
    with pytest.raises(FileExistsError):
        sh.open(fname, "x", compression=compression)


@compression_param
def test_open_binary(str_or_path, tmpdir, openfunc, ext, compression):
    fname = str_or_path(f"{tmpdir}/test_open{ext}")

    with sh.open(fname, "wb", compression=compression) as fh:
        fh.write(b"Hello world")
    with openfunc(fname, "rb") as fh:
        assert fh.read() == b"Hello world"
    with sh.open(fname, "ab", compression=compression) as fh:
        fh.write(b" and universe")
    with sh.open(fname, "rb", compression=compression) as fh:
        assert fh.read() == b"Hello world and universe"


@compression_param
def test_open_encoding(tmpdir, openfunc, ext, compression):
    text = "Crème brûlée"
    text_replaced = "Cr�me br�l�e"
    fname_utf8 = f"{tmpdir}/test_utf8{ext}"
    fname_latin1 = f"{tmpdir}/test_latin1{ext}"

    with openfunc(fname_utf8, "wt", encoding="utf-8") as fh:
        fh.write(text)
    with openfunc(fname_latin1, "wt", encoding="latin1") as fh:
        fh.write(text)

    # sh.open must always default to utf-8
    with sh.open(fname_utf8, compression=compression) as fh:
        assert fh.read() == text
    with sh.open(fname_latin1, compression=compression, encoding="latin1") as fh:
        assert fh.read() == text
    # sh.open must always default to replace unrecognized characters with ?
    with sh.open(fname_latin1, compression=compression) as fh:
        assert fh.read() == text_replaced
    with pytest.raises(UnicodeDecodeError):
        with sh.open(fname_latin1, errors="strict", compression=compression) as fh:
            fh.read()


@compression_param
@pytest.mark.parametrize("newline", ["\n", "\r", "\r\n"])
def test_open_kwargs(tmpdir, openfunc, ext, compression, newline):
    # **kwargs are passed verbatim to the underlying function
    fname = f"{tmpdir}/test_open{ext}"

    with sh.open(fname, "w", compression=compression, newline=newline) as fh:
        fh.write("Hello\nworld")
    with openfunc(fname, "rb") as fh:
        assert fh.read() == b"Hello" + newline.encode("utf8") + b"world"


# no compression support
def test_open_fd():
    r, w = os.pipe()
    with sh.open(r, "rb", buffering=0) as fh_r:
        with sh.open(w, "wb", buffering=0) as fh_w:
            fh_w.write(b"hello world\n")
            assert fh_r.readline() == b"hello world\n"


def test_open_invalid_compression():
    with pytest.raises(ValueError):
        sh.open("foo", compression="unk")


def test_open_fd_invalid_compression():
    r, _ = os.pipe()
    with pytest.raises(TypeError):
        sh.open(r, "rb", compression="gzip")


@pytest.mark.parametrize(
    "decompress,compression",
    [(gzip.decompress, "gzip"), (bz2.decompress, "bzip2"), (lzma.decompress, "lzma")],
)
def test_open_fh_compression(decompress, compression):
    buf = io.BytesIO()
    with sh.open(buf, "w", compression=compression) as fh:
        fh.write("hello world")
    assert decompress(buf.getvalue()) == b"hello world"
    buf.seek(0)
    with sh.open(buf, "r", compression=compression) as fh:
        assert fh.read() == "hello world"


@pytest.mark.parametrize("compression", [False, "auto"])
def test_open_fh_no_compression(compression):
    buf = io.BytesIO()
    with pytest.raises(TypeError):
        sh.open(buf, compression=compression)
