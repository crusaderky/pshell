import glob
import os
import subprocess
import tempfile
import pytest
import pshell as sh
from . import StubError

cwd_backup = None
tmpdir = None


def setup():
    global cwd_backup
    global tmpdir

    cwd_backup = os.getcwd()
    tmpdir = tempfile.TemporaryDirectory()
    os.environ['LANDG_UNITTEST_BASH'] = tmpdir.name


def teardown():
    for root, dirs, files in os.walk(tmpdir.name):
        for fname in dirs + files:
            try:
                os.chmod(os.path.join(root, fname), 0o777)
            except OSError:
                pass

    os.chdir(cwd_backup)
    del os.environ['LANDG_UNITTEST_BASH']


def test_remove():
    testpath = tmpdir.name + '/test_remove'
    testpath_env = '$LANDG_UNITTEST_BASH/test_remove'

    # remove file
    with open(testpath, 'w'):
        pass
    assert os.path.exists(testpath)
    sh.remove(testpath_env)
    assert not os.path.exists(testpath)

    # remove dir and symlink to dir
    os.mkdir(testpath)
    os.symlink(testpath, testpath + ".lnk")
    assert os.path.exists(testpath)
    assert os.path.exists(testpath + ".lnk")
    sh.remove(testpath_env + ".lnk")
    sh.remove(testpath_env)
    assert not os.path.exists(testpath)
    assert not os.path.exists(testpath + ".lnk")

    # recursive
    os.mkdir(testpath)
    os.mkdir(testpath + '/dir2')
    sh.remove(testpath_env, recursive=True)
    assert not os.path.exists(testpath)

    # recursive must also work on a file
    with open(testpath, 'w'):
        pass
    assert os.path.exists(testpath)
    sh.remove(testpath_env, recursive=True)
    assert not os.path.exists(testpath)

    # recursive on a symlink to dir must delete the symlink
    os.mkdir(testpath)
    with open(testpath + '/donttouch', 'w'):
        pass
    os.symlink(testpath, testpath + '.lnk')
    sh.remove(testpath_env + '.lnk', recursive=True)
    assert not os.path.exists(testpath + '.lnk')
    assert os.path.exists(testpath + '/donttouch')
    os.remove(testpath + '/donttouch')
    os.rmdir(testpath)


def test_remove_force1():
    with pytest.raises(FileNotFoundError):
        sh.remove('NOTEXIST.txt', force=False)


def test_remove_force2():
    sh.remove('NOTEXIST.txt', force=True)


def test_remove_noperm():
    testpath = tmpdir.name + '/test_remove_noperm'
    os.makedirs(testpath + '/foo/bar')
    os.chmod(testpath + '/foo/bar', 0)
    with pytest.raises(PermissionError):
        sh.remove(testpath + '/foo', recursive=True)

    sh.remove(testpath + '/foo', recursive=True, rename_on_fail=True)
    assert not os.path.exists(testpath + '/foo')
    assert len(glob.glob(testpath + '/foo.DELETEME.*')) == 1


def test_chdir():
    sh.chdir('$LANDG_UNITTEST_BASH')
    assert os.getcwd() == tmpdir.name


def test_pushd():
    os.chdir('/')
    assert os.getcwd() == '/'
    with sh.pushd('$LANDG_UNITTEST_BASH'):
        assert os.getcwd() == tmpdir.name
    assert os.getcwd() == '/'

    # Test that the cleanup also happens in case of Exception
    with pytest.raises(StubError):
        with sh.pushd('$LANDG_UNITTEST_BASH'):
            assert os.getcwd() == tmpdir.name
            raise StubError()
    assert os.getcwd() == '/'


def test_move():
    os.mkdir(tmpdir.name + '/test_move1')
    sh.move('$LANDG_UNITTEST_BASH/test_move1', '$LANDG_UNITTEST_BASH/test_move2')
    assert not os.path.exists(tmpdir.name + '/test_move1')
    assert os.path.exists(tmpdir.name + '/test_move2')


def test_copy():
    # single file - copy to file
    with open(tmpdir.name + '/test_cp1', 'w'):
        pass
    sh.copy('$LANDG_UNITTEST_BASH/test_cp1', '$LANDG_UNITTEST_BASH/test_cp2')
    assert os.path.exists(tmpdir.name + '/test_cp1')
    assert os.path.exists(tmpdir.name + '/test_cp2')

    # single file - copy to directory
    os.mkdir(tmpdir.name + '/test_cp3')
    sh.copy('$LANDG_UNITTEST_BASH/test_cp1', '$LANDG_UNITTEST_BASH/test_cp3')
    assert os.path.exists(tmpdir.name + '/test_cp1')
    assert os.path.exists(tmpdir.name + '/test_cp3/test_cp1')

    # recursive
    os.mkdir(tmpdir.name + '/test_cp4')
    os.mkdir(tmpdir.name + '/test_cp4/dir2')
    sh.copy('$LANDG_UNITTEST_BASH/test_cp4', '$LANDG_UNITTEST_BASH/test_cp5')
    assert os.path.exists(tmpdir.name + '/test_cp4/dir2')
    assert os.path.exists(tmpdir.name + '/test_cp5/dir2')


# input does not exist
def test_copy_err1():
    with pytest.raises(FileNotFoundError):
        sh.copy('/does/not/exist', '$LANDG_UNITTEST_BASH/')


# single file to non-existing directory
def test_copy_err2():
    with open(tmpdir.name + '/test_cp_err2', 'w'):
        pass
    with pytest.raises(FileNotFoundError):
        sh.copy('$LANDG_UNITTEST_BASH/test_cp_err2',
                '$LANDG_UNITTEST_BASH/does/not/exist')


# directory to non-existing parent directory automatically creates parents
def test_copy_dir_to_missing_parent():
    os.mkdir(tmpdir.name + '/test_cpdir')
    sh.copy('$LANDG_UNITTEST_BASH/test_cpdir',
            '$LANDG_UNITTEST_BASH/does/not/exist')


# directory to already existing target
def test_copy_err4():
    os.mkdir(tmpdir.name + '/test_cp_err4a')
    os.mkdir(tmpdir.name + '/test_cp_err4b')
    with pytest.raises(FileExistsError):
        sh.copy('$LANDG_UNITTEST_BASH/test_cp_err4a',
                '$LANDG_UNITTEST_BASH/test_cp_err4b')


def test_backup():
    with open(tmpdir.name + '/test', 'w'):
        pass

    fname = tmpdir.name + '/test'
    fname_env = '$LANDG_UNITTEST_BASH/test'

    # Auto extension
    new_fname = sh.backup(fname_env, action='copy')
    assert os.path.exists(fname)
    assert os.path.exists(sh.resolve_env(new_fname))

    # Manual extension
    new_fname = sh.backup('$LANDG_UNITTEST_BASH/test',
                          suffix='bak', action='copy')
    assert os.path.exists(tmpdir.name + '/test.bak')
    assert new_fname == '$LANDG_UNITTEST_BASH/test.bak'

    # Collisions in the backup name will generate a unique new name
    new_fname = sh.backup('$LANDG_UNITTEST_BASH/test',
                          suffix='bak', action='copy')
    assert os.path.exists(tmpdir.name + '/test.bak.2')
    assert new_fname == '$LANDG_UNITTEST_BASH/test.bak.2'

    # action='move'
    new_fname = sh.backup(fname_env, action='move')
    assert not os.path.exists(fname)
    assert os.path.exists(sh.resolve_env(new_fname))


def test_backup_notexist():
    with pytest.raises(FileNotFoundError):
        sh.backup('notexist.txt')


def test_backup_notexist_force():
    assert sh.backup('notexist.txt', force=True) is None


def test_symlink():
    os.chdir('/')
    with open(tmpdir.name + '/test_ln1', 'w'):
        pass
    with open(tmpdir.name + '/test_ln2', 'w'):
        pass

    # abspath = False
    sh.symlink('$LANDG_UNITTEST_BASH/test_ln1',
               '$LANDG_UNITTEST_BASH/test_ln3', abspath=False)
    assert subprocess.check_output(
        "ls -l " + tmpdir.name + "/test_ln3 | awk '{print $NF}'",
        shell=True) == b'test_ln1\n'
    os.remove(tmpdir.name + '/test_ln3')

    # abspath = True
    sh.symlink('$LANDG_UNITTEST_BASH/test_ln1', '$LANDG_UNITTEST_BASH/test_ln3', abspath=True)
    assert subprocess.check_output(
        "ls -l " + tmpdir.name + "/test_ln3 | awk '{print $NF}'",
        shell=True).decode('utf-8') == tmpdir.name + '/test_ln1\n'

    # no force
    with pytest.raises(FileExistsError):
        sh.symlink('$LANDG_UNITTEST_BASH/test_ln2',
                   '$LANDG_UNITTEST_BASH/test_ln3', force=False)

    # force must work only to override another symlink,
    # NOT another regular file
    with pytest.raises(FileExistsError):
        sh.symlink('$LANDG_UNITTEST_BASH/test_ln1',
                   '$LANDG_UNITTEST_BASH/test_ln2', force=True)

    # force; old symlink is different
    sh.symlink('$LANDG_UNITTEST_BASH/test_ln2',
               '$LANDG_UNITTEST_BASH/test_ln3', force=True)
    assert subprocess.check_output(
        "ls -l " + tmpdir.name + "/test_ln3 | awk '{print $NF}'",
        shell=True) == b'test_ln2\n'

    # force; old symlink is identical
    sh.symlink('$LANDG_UNITTEST_BASH/test_ln2',
               '$LANDG_UNITTEST_BASH/test_ln3', force=True)
    assert subprocess.check_output(
        "ls -l " + tmpdir.name + "/test_ln3 | awk '{print $NF}'",
        shell=True) == b'test_ln2\n'

    # Test that chdir didn't change
    assert os.getcwd() == '/'


def test_exists():
    assert not sh.exists('$LANDG_UNITTEST_BASH/test_exists')
    assert not sh.lexists('$LANDG_UNITTEST_BASH/test_exists')

    with open(tmpdir.name + '/test_exists', 'w'):
        pass
    assert sh.exists('$LANDG_UNITTEST_BASH/test_exists')
    assert sh.lexists('$LANDG_UNITTEST_BASH/test_exists')

    sh.symlink('$LANDG_UNITTEST_BASH/test_exists', '$LANDG_UNITTEST_BASH/test_exists_ln')
    assert sh.exists('$LANDG_UNITTEST_BASH/test_exists_ln')
    assert sh.lexists('$LANDG_UNITTEST_BASH/test_exists_ln')

    os.remove(tmpdir.name + '/test_exists')
    assert not sh.exists('$LANDG_UNITTEST_BASH/test_exists_ln')
    assert sh.lexists('$LANDG_UNITTEST_BASH/test_exists_ln')


def test_mkdir():
    sh.mkdir('$LANDG_UNITTEST_BASH/test_mkdir', force=False, parents=False)
    assert os.path.isdir(tmpdir.name + '/test_mkdir')

    # Already existing
    with pytest.raises(FileExistsError):
        sh.mkdir('$LANDG_UNITTEST_BASH/test_mkdir', force=False, parents=False)

    sh.mkdir('$LANDG_UNITTEST_BASH/test_mkdir', force=True, parents=False)

    assert os.path.isdir(tmpdir.name + '/test_mkdir')

    # Accidentally overwrite a non-directory
    with open(tmpdir.name + '/test_mkdir_file', 'w'):
        pass

    with pytest.raises(FileExistsError):
        sh.mkdir('$LANDG_UNITTEST_BASH/test_mkdir_file',
                 force=True, parents=False)

    # Missing middle path
    with pytest.raises(FileNotFoundError):
        sh.mkdir('$LANDG_UNITTEST_BASH/middle/test_mkdir',
                 parents=False, force=False)

    sh.mkdir('$LANDG_UNITTEST_BASH/middle/test_mkdir',
             parents=True, force=False)
    assert os.path.isdir(tmpdir.name + '/middle/test_mkdir')
