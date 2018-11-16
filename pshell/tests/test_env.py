import os
import pytest
import pshell as sh
from . import StubError, DATADIR, unix_only


@unix_only
def test_source():
    if 'UNITTEST_DATA_1' in os.environ:
        del os.environ['UNITTEST_DATA_1']
    os.environ['UNITTEST_DATA_2'] = 'old'

    # Also test variable name resolution
    os.environ['UNITTEST_DATADIR'] = DATADIR
    sh.source('$UNITTEST_DATADIR/source.sh')

    assert os.getenv('UNITTEST_DATA_1') == 'foo'
    assert os.getenv('UNITTEST_DATA_2') == 'bar'


def test_resolve_env():
    os.environ['UNITTEST_FOO'] = 'foo'
    os.environ['UNITTEST_BAR'] = 'bar'
    assert sh.resolve_env('$UNITTEST_FOO.${UNITTEST_BAR}') == 'foo.bar'

    with pytest.raises(EnvironmentError):
        sh.resolve_env('$NOT_EXISTING_VARIABLE')


def test_putenv():
    # Base use case
    os.environ.pop('landgbashTEST1', None)
    sh.putenv('landgbashTEST1', 'foo')
    assert os.environ['landgbashTEST1'] == 'foo'

    # Variable value contains another variable that must be resolved
    os.environ.pop('landgbashTEST2', None)
    sh.putenv('landgbashTEST2', '$landgbashTEST1/bar')
    assert os.environ['landgbashTEST2'] == 'foo/bar'

    # Delete variable when it exists
    sh.putenv('landgbashTEST1', None)
    assert 'landgbashTEST1' not in os.environ

    # Delete variable when it does not exist
    sh.putenv('landgbashTEST1', None)
    assert 'landgbashTEST1' not in os.environ

    # Set blank variable (not the same as setting None, which deletes it)
    sh.putenv('landgbashTEST1', '')
    assert os.environ['landgbashTEST1'] == ''


def test_override_env():
    os.environ.pop('landgbashTEST3', None)
    os.environ['landgbashTEST4'] = 'original'

    with sh.override_env('landgbashTEST3', 'foo'):
        with sh.override_env('landgbashTEST4', '$landgbashTEST3/bar'):
            assert os.getenv('landgbashTEST3') == 'foo'
            assert os.getenv('landgbashTEST4') == 'foo/bar'

    assert 'landgbashTEST3' not in os.environ
    assert os.environ['landgbashTEST4'] == 'original'

    # Test that the cleanup also happens in case of Exception
    with pytest.raises(StubError):
        with sh.override_env('landgbashTEST3', 'foo'):
            assert os.getenv('landgbashTEST3') == 'foo'
            raise StubError()
    assert 'landgbashTEST3' not in os.environ
