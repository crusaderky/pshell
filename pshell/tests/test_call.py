import io
import tempfile
import sys
import time
import pytest
import pshell as sh
from . import StubError


def test_real_fh_none():
    # Required by call, check_call, check_output
    with sh.real_fh(None) as rfh:
        assert rfh is None


def test_real_fh_trivial():
    # Real POSIX-backed file handle
    with tempfile.TemporaryFile() as fh:
        with sh.real_fh(fh) as rfh:
            assert rfh is fh


def test_real_fh_stringio():
    fh = io.StringIO()
    with sh.real_fh(fh) as rfh:
        assert rfh.fileno() > 2
        rfh.write("Hello world")
    assert fh.getvalue() == "Hello world"


def test_real_fh_bytesio():
    fh = io.BytesIO()
    with sh.real_fh(fh) as rfh:
        assert rfh.fileno() > 2
        rfh.write(b"Hello world")
    assert fh.getvalue() == b"Hello world"


def test_real_fh_crash():
    # Test that the output copy is wrapped by a `finally` clause,
    # so that it is not lost if the wrapped code raises an Exception
    fh = io.StringIO()
    try:
        with sh.real_fh(fh) as rfh:
            rfh.write("Hello world")
            raise StubError()
    except StubError:
        pass
    else:
        # Exception isn't masked
        assert False

    assert fh.getvalue() == "Hello world"


@pytest.mark.skip("no way of testing this with pytest")
def test_real_fh_nosetests():
    # sys.stdout and sys.stderr have been monkey-patched by nosetests
    # with a custom class (not io.StringIO!)
    with sh.real_fh(sys.stdout) as rfh:
        assert rfh is not sys.stdout
        assert rfh.fileno() > 2
        rfh.write("Hello world")
    with sh.real_fh(sys.stderr) as rfh:
        assert rfh is not sys.stderr
        assert rfh.fileno() > 2
        rfh.write("Hello world")


def test_real_fh_fullpipe():
    # Exceed the typical size of a pipe (64 kbytes on Linux)
    # in an attempt to trigger a deadlock if the pipe isn't
    # continuously flushed.
    fh = io.StringIO()
    payload = "x" * int(2**20)  # 1MB payload
    with sh.real_fh(fh) as rfh:
        rfh.write(payload)
    assert fh.getvalue() == payload


def test_call():
    assert sh.call('echo "Hello world!" > /dev/null') == 0


def test_call_quotes():
    assert sh.call("echo 'Hello world!' > /dev/null") == 0


def test_call_errexit():
    assert sh.call('notexist.sh') == 127


def test_call_nounset():
    assert sh.call('echo $NOT_EXISTING_VARIABLE') == 1


def test_call_pipefail():
    assert sh.call('cat NOTEXIST | cat') == 1


def test_call_obfuscate_pwd():
    # TODO intercept logging
    assert sh.call('echo -P mypass', obfuscate_pwd='mypass') == 0


def test_call_noshell1():
    assert sh.call(["echo", "Hello world!"], shell=False) == 0


def test_call_noshell2():
    with pytest.raises(FileNotFoundError):
        sh.call('notexist.sh', shell=False)


def test_call_timeout():
    ts_start = time.time()
    with pytest.raises(sh.TimeoutExpired):
        sh.call('sleep 2', timeout=0.1)
    assert time.time() - ts_start < 0.5


def test_call_real_fh_stringio():
    stderr = io.StringIO()
    stdout = io.StringIO()
    assert sh.call('echo hello 1>&2 && echo world',
                   stdout=stdout, stderr=stderr) == 0
    assert stderr.getvalue() == 'hello\n'
    assert stdout.getvalue() == 'world\n'


def test_call_real_fh_nosetests():
    assert sh.call('echo hello 1>&2 && echo world',
                   stdout=sys.stdout, stderr=sys.stderr) == 0


def test_check_call():
    sh.check_call('echo "Hello world!" > /dev/null')


def test_check_call_quotes():
    sh.check_call("echo 'Hello world!' > /dev/null")


def test_check_call_errexit():
    with pytest.raises(sh.CalledProcessError):
        sh.check_call('notexist.sh')


def test_check_call_nounset():
    with pytest.raises(sh.CalledProcessError):
        sh.check_call('echo $NOT_EXISTING_VARIABLE')


def test_check_call_pipefail():
    with pytest.raises(sh.CalledProcessError):
        sh.check_call('cat NOTEXIST | cat')


def test_check_call_obfuscate_pwd():
    # TODO intercept logging
    sh.check_call('echo -P mypass', obfuscate_pwd='mypass')


def test_check_call_noshell1():
    sh.check_call(["echo", "Hello world!"], shell=False)


def test_check_call_noshell2():
    with pytest.raises(sh.CalledProcessError):
        sh.check_call(['cat', 'notexist.txt'], shell=False)


def test_check_call_noshell3():
    with pytest.raises(FileNotFoundError):
        sh.check_call('notexist.sh', shell=False)


def test_check_call_timeout():
    ts_start = time.time()
    with pytest.raises(sh.TimeoutExpired):
        sh.check_call('sleep 2', timeout=0.1)
    assert time.time() - ts_start < 0.5


def test_check_call_real_fh_stringio():
    stderr = io.StringIO()
    stdout = io.StringIO()
    sh.check_call('echo hello 1>&2 && echo world',
                  stdout=stdout, stderr=stderr)
    assert stderr.getvalue() == 'hello\n'
    assert stdout.getvalue() == 'world\n'


def test_check_call_real_fh_nosetests():
    assert sh.call('echo hello 1>&2 && echo world',
                   stdout=sys.stdout, stderr=sys.stderr) == 0


def test_check_output():
    assert sh.check_output('echo -n "Hello world"') == 'Hello world'


def test_check_output_quotes():
    assert sh.check_output("echo 'Hello world!'") == "Hello world!\n"


def test_check_output_nodecode():
    assert sh.check_output('echo -n "Hello world"',
                           decode=False) == b'Hello world'


def test_check_output_unicode():
    assert sh.check_output(r"printf '\xE2\x98\xA0'") == '☠'

    # Test invalid unicode character
    assert sh.check_output(r"printf '\x85'") == '�'
    assert sh.check_output(r"printf '\x85'", errors='replace') == '�'
    assert sh.check_output(r"printf '\x85'", errors='ignore') == ''
    with pytest.raises(UnicodeDecodeError):
        sh.check_output(r"printf '\x85'", errors='strict')


def test_check_output_errexit():
    with pytest.raises(sh.CalledProcessError):
        sh.check_output('notexist.sh')


def test_check_output_nounset():
    with pytest.raises(sh.CalledProcessError):
        sh.check_output('echo $NOT_EXISTING_VARIABLE')


def test_check_output_pipefail():
    with pytest.raises(sh.CalledProcessError):
        sh.check_output('cat NOTEXIST | cat')


def test_check_output_obfuscate_pwd():
    # TODO intercept logging
    assert sh.check_output('echo -P mypass',
                           obfuscate_pwd='mypass') == "-P mypass\n"


def test_check_output_noshell1():
    assert sh.check_output(['echo', '-n', 'Hello world'],
                           shell=False) == 'Hello world'


def test_check_output_noshell2():
    with pytest.raises(sh.CalledProcessError):
        sh.check_output(['cat', 'notexist.txt'], shell=False)


def test_check_output_noshell3():
    with pytest.raises(FileNotFoundError):
        sh.check_output('notexist.sh', shell=False)


# Do not change shell=False to True
# If the timeout expires, the child process will be killed
# and then waited for again The TimeoutExpired exception will
# be re-raised after the child process has terminated.
def test_check_output_timeout():
    ts_start = time.time()
    with pytest.raises(sh.TimeoutExpired):
        sh.check_output(["sleep", "2"], timeout=0.1, shell=False)
    assert time.time() - ts_start < 0.5


def test_check_output_real_fh_stringio():
    stderr = io.StringIO()
    sh.check_output('echo hello 1>&2', stderr=stderr)
    assert stderr.getvalue() == 'hello\n'


def test_check_output_real_fh_nosetests():
    sh.check_output('echo hello 1>&2', stderr=sys.stderr)
