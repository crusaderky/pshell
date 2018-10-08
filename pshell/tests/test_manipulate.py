import pytest
import pshell as sh


@pytest.mark.parametrize('newline', ['\n', '\r\n'])
def test_concatenate_t1(tmpdir, newline):
    # Output file already exists and is non-empty. Files end without a newline.
    # Test compression.
    out = '%s/out.gz' % tmpdir
    in1 = '%s/in1' % tmpdir
    in2 = '%s/in2.bz2' % tmpdir

    with sh.open(out, 'w') as fh:
        fh.write('1')
    with sh.open(in1, 'w') as fh:
        fh.write('2\n3')
    with sh.open(in2, 'w') as fh:
        fh.write('4')

    n = newline.encode('utf-8')
    sh.concatenate([in1, in2], out, 'a', newline=newline)
    with sh.open(out, 'rb') as fh:
        assert fh.read() == b'1' + n + b'2' + n + b'3' + n + b'4' + n
    # Defaults to mode='w'
    sh.concatenate([in1, in2], out, newline=newline)
    with sh.open(out, 'rb') as fh:
        assert fh.read() == b'2' + n + b'3' + n + b'4' + n


@pytest.mark.parametrize('newline', ['\n', '\r\n'])
def test_concatenate_t2(tmpdir, newline):
    # Output file already exists and is non-empty. Files end with a newline.
    out = '%s/out' % tmpdir
    in1 = '%s/in1' % tmpdir
    in2 = '%s/in2' % tmpdir

    with sh.open(out, 'w', newline=newline) as fh:
        fh.write('1\n')
    with sh.open(in1, 'w', newline=newline) as fh:
        fh.write('2\n3\n')
    with sh.open(in2, 'w', newline=newline) as fh:
        fh.write('4\n')

    n = newline.encode('utf-8')
    sh.concatenate([in1, in2], out, 'a', newline=newline)
    with sh.open(out, 'rb') as fh:
        assert fh.read() == b'1' + n + b'2' + n + b'3' + n + b'4' + n
    sh.concatenate([in1, in2], out, newline=newline)
    with sh.open(out, 'rb') as fh:
        assert fh.read() == b'2' + n + b'3' + n + b'4' + n


def test_concatenate_t3(tmpdir):
    # Output file already exists and it is empty
    out = '%s/out' % tmpdir
    in1 = '%s/in1' % tmpdir
    in2 = '%s/in2' % tmpdir

    with sh.open(out, 'w') as fh:
        pass
    with sh.open(in1, 'w') as fh:
        fh.write('2\n')
    with sh.open(in2, 'w') as fh:
        fh.write('3\n')

    sh.concatenate([in1, in2], out, 'a')
    with sh.open(out) as fh:
        assert fh.read() == '2\n3\n'
    sh.concatenate([in1, in2], out)
    with sh.open(out) as fh:
        assert fh.read() == '2\n3\n'


def test_concatenate_t4(tmpdir):
    # Output file does not already exist
    out = '%s/out' % tmpdir
    in1 = '%s/in1' % tmpdir
    in2 = '%s/in2' % tmpdir

    with sh.open(in1, 'w') as fh:
        fh.write('2')
    with sh.open(in2, 'w') as fh:
        fh.write('3')

    sh.concatenate([in1, in2], out, 'a')
    with sh.open(out) as fh:
        assert fh.read() == '2\n3\n'
    sh.concatenate([in1, in2], out)
    with sh.open(out) as fh:
        assert fh.read() == '2\n3\n'


def test_concatenate_b(tmpdir):
    # Binary mode
    out = '%s/out' % tmpdir
    in1 = '%s/in1' % tmpdir
    in2 = '%s/in2' % tmpdir

    with sh.open(out, 'wb') as fh:
        fh.write(b'1')
    with sh.open(in1, 'wb') as fh:
        fh.write(b'2')
    with sh.open(in2, 'wb') as fh:
        fh.write(b'3')

    sh.concatenate([in1, in2], out, 'ab')
    with sh.open(out, 'rb') as fh:
        assert fh.read() == b'123'
    sh.concatenate([in1, in2], out, 'wb')
    with sh.open(out, 'rb') as fh:
        assert fh.read() == b'23'
