import getpass
import glob
import os
import subprocess
import pytest
import pshell as sh
from . import StubError, unix_only


def test_remove(tmpdir):
    os.environ['UNITTEST_BASH'] = str(tmpdir)
    testpath = '%s/test_remove' % tmpdir
    testpath_env = '$UNITTEST_BASH/test_remove'

    # remove file
    with open(testpath, 'w'):
        pass
    assert os.path.exists(testpath)
    sh.remove(testpath_env)
    assert not os.path.exists(testpath)

    # remove dir
    os.mkdir(testpath)
    assert os.path.exists(testpath)
    sh.remove(testpath_env)
    assert not os.path.exists(testpath)

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


@unix_only
def test_remove_symlinks(tmpdir):
    os.environ['UNITTEST_BASH'] = str(tmpdir)
    testpath = '%s/test_remove' % tmpdir
    testpath_env = '$UNITTEST_BASH/test_remove'

    # remove dir and symlink to dir
    os.mkdir(testpath)
    os.symlink(testpath, testpath + ".lnk")
    assert os.path.exists(testpath)
    assert os.path.exists(testpath + ".lnk")
    sh.remove(testpath_env + ".lnk")
    sh.remove(testpath_env)
    assert not os.path.exists(testpath)
    assert not os.path.exists(testpath + ".lnk")

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


def test_remove_noperm(tmpdir):
    testpath = '%s/test_remove_noperm' % tmpdir
    os.makedirs(testpath + '/foo/bar')
    os.chmod(testpath + '/foo/bar', 0)
    with pytest.raises(PermissionError):
        sh.remove(testpath + '/foo', recursive=True)

    sh.remove(testpath + '/foo', recursive=True, rename_on_fail=True)
    assert not os.path.exists(testpath + '/foo')
    assert len(glob.glob(testpath + '/foo.DELETEME.*')) == 1


def test_ignore_readonly1(tmpdir):
    """Test the ignore_readonly=True flag
    """
    os.makedirs('%s/foo/bar/baz' % tmpdir)
    os.chmod('%s/foo/bar/baz' % tmpdir, 0o500)
    os.chmod('%s/foo/bar' % tmpdir, 0o500)
    os.chmod('%s/foo' % tmpdir, 0o500)

    with pytest.raises(PermissionError):
        sh.remove('%s/foo' % tmpdir, recursive=True)
    assert os.path.exists('%s/foo/bar/baz' % tmpdir)

    sh.remove('%s/foo' % tmpdir, force=False, recursive=True,
              ignore_readonly=True)
    assert not os.path.exists('%s/foo' % tmpdir)


def test_ignore_readonly2(tmpdir):
    """Test the case where there was no permission issue to begin with,
    so a double call to shutil.rmtree would raise FileNotFoundError
    """
    os.makedirs('%s/foo/bar' % tmpdir)
    sh.remove('%s/foo' % tmpdir, force=False, recursive=True,
              ignore_readonly=True)
    assert not os.path.exists('%s/foo' % tmpdir)


def test_chdir(tmpdir):
    os.environ['UNITTEST_BASH'] = str(tmpdir)
    assert os.getcwd() != str(tmpdir)
    sh.chdir('$UNITTEST_BASH')
    assert os.getcwd() == str(tmpdir)


def test_pushd(tmpdir):
    os.environ['UNITTEST_BASH'] = str(tmpdir)
    d0 = os.getcwd()
    assert d0 != str(tmpdir)
    with sh.pushd('$UNITTEST_BASH'):
        assert os.getcwd() == str(tmpdir)
        # test that context manager is reentrant
        tmpdir.mkdir('d1')
        with sh.pushd('d1'):
            assert os.getcwd() == os.path.join(str(tmpdir), 'd1')
        assert os.getcwd() == str(tmpdir)
    assert os.getcwd() == d0

    # Test that the cleanup also happens in case of Exception
    with pytest.raises(StubError):
        with sh.pushd('$UNITTEST_BASH'):
            assert os.getcwd() == str(tmpdir)
            raise StubError()
    assert os.getcwd() == d0


def test_move(tmpdir):
    os.environ['UNITTEST_BASH'] = str(tmpdir)
    tmpdir.mkdir('test_move1')
    sh.move('$UNITTEST_BASH/test_move1', '$UNITTEST_BASH/test_move2')
    assert not os.path.exists('%s/test_move1' % tmpdir)
    assert os.path.exists('%s/test_move2' % tmpdir)


def test_copy(tmpdir):
    os.environ['UNITTEST_BASH'] = str(tmpdir)
    # single file - copy to file
    with open('%s/test_cp1' % tmpdir, 'w'):
        pass
    sh.copy('$UNITTEST_BASH/test_cp1', '$UNITTEST_BASH/test_cp2')
    assert os.path.exists('%s/test_cp1' % tmpdir)
    assert os.path.exists('%s/test_cp2' % tmpdir)

    # single file - copy to directory
    tmpdir.mkdir('test_cp3')
    sh.copy('$UNITTEST_BASH/test_cp1', '$UNITTEST_BASH/test_cp3')
    assert os.path.exists('%s/test_cp1' % tmpdir)
    assert os.path.exists('%s/test_cp3/test_cp1' % tmpdir)

    # recursive
    tmpdir.mkdir('test_cp4')
    tmpdir.mkdir('test_cp4/dir2')
    sh.copy('$UNITTEST_BASH/test_cp4', '$UNITTEST_BASH/test_cp5')
    assert os.path.exists('%s/test_cp4/dir2' % tmpdir)
    assert os.path.exists('%s/test_cp5/dir2' % tmpdir)


# input does not exist
def test_copy_err1():
    with pytest.raises(FileNotFoundError):
        sh.copy('/does/not/exist', '$UNITTEST_BASH/')


# single file to non-existing directory
def test_copy_err2(tmpdir):
    os.environ['UNITTEST_BASH'] = str(tmpdir)
    with open('%s/test_cp_err2' % tmpdir, 'w'):
        pass
    with pytest.raises(FileNotFoundError):
        sh.copy('$UNITTEST_BASH/test_cp_err2', '$UNITTEST_BASH/does/not/exist')


# directory to non-existing parent directory automatically creates parents
def test_copy_dir_to_missing_parent(tmpdir):
    os.environ['UNITTEST_BASH'] = str(tmpdir)
    tmpdir.mkdir('test_cpdir')
    sh.copy('$UNITTEST_BASH/test_cpdir', '$UNITTEST_BASH/does/not/exist')


# directory to already existing target
def test_copy_err4(tmpdir):
    os.environ['UNITTEST_BASH'] = str(tmpdir)
    tmpdir.mkdir('test_cp_err4a')
    tmpdir.mkdir('test_cp_err4b')
    with pytest.raises(FileExistsError):
        sh.copy('$UNITTEST_BASH/test_cp_err4a',
                '$UNITTEST_BASH/test_cp_err4b')


def test_backup(tmpdir):
    os.environ['UNITTEST_BASH'] = str(tmpdir)
    fname = '%s/test' % tmpdir
    fname_env = '$UNITTEST_BASH/test'
    with open(fname, 'w'):
        pass

    # Auto extension
    new_fname = sh.backup(fname_env, action='copy')
    assert os.path.exists(fname)
    assert os.path.exists(sh.resolve_env(new_fname))

    # Manual extension
    new_fname = sh.backup('$UNITTEST_BASH/test',
                          suffix='bak', action='copy')
    assert os.path.exists('%s/test.bak' % tmpdir)
    assert new_fname == '$UNITTEST_BASH/test.bak'

    # Collisions in the backup name will generate a unique new name
    new_fname = sh.backup('$UNITTEST_BASH/test',
                          suffix='bak', action='copy')
    assert os.path.exists('%s/test.bak.2' % tmpdir)
    assert new_fname == '$UNITTEST_BASH/test.bak.2'

    # action='move'
    new_fname = sh.backup(fname_env, action='move')
    assert not os.path.exists(fname)
    assert os.path.exists(sh.resolve_env(new_fname))


def test_backup_notexist():
    with pytest.raises(FileNotFoundError):
        sh.backup('notexist.txt')


def test_backup_notexist_force():
    assert sh.backup('notexist.txt', force=True) is None


@unix_only
def test_symlink(tmpdir):
    os.environ['UNITTEST_BASH'] = str(tmpdir)
    os.chdir('/')
    with open('%s/test_ln1' % tmpdir, 'w'):
        pass
    with open('%s/test_ln2' % tmpdir, 'w'):
        pass

    # abspath = False
    sh.symlink('$UNITTEST_BASH/test_ln1',
               '$UNITTEST_BASH/test_ln3', abspath=False)
    assert subprocess.check_output(
        "ls -l %s/test_ln3 | awk '{print $NF}'" % tmpdir,
        shell=True) == b'test_ln1\n'
    os.remove('%s/test_ln3' % tmpdir)

    # abspath = True
    sh.symlink('$UNITTEST_BASH/test_ln1',
               '$UNITTEST_BASH/test_ln3', abspath=True)
    assert subprocess.check_output(
        "ls -l %s/test_ln3 | awk '{print $NF}'" % tmpdir,
        shell=True).decode('utf-8') == '%s/test_ln1\n' % tmpdir

    # no force
    with pytest.raises(FileExistsError):
        sh.symlink('$UNITTEST_BASH/test_ln2',
                   '$UNITTEST_BASH/test_ln3', force=False)

    # force must work only to override another symlink,
    # NOT another regular file
    with pytest.raises(FileExistsError):
        sh.symlink('$UNITTEST_BASH/test_ln1',
                   '$UNITTEST_BASH/test_ln2', force=True)

    # force; old symlink is different
    sh.symlink('$UNITTEST_BASH/test_ln2',
               '$UNITTEST_BASH/test_ln3', force=True)
    assert subprocess.check_output(
        "ls -l %s/test_ln3 | awk '{print $NF}'" % tmpdir,
        shell=True) == b'test_ln2\n'

    # force; old symlink is identical
    sh.symlink('$UNITTEST_BASH/test_ln2',
               '$UNITTEST_BASH/test_ln3', force=True)
    assert subprocess.check_output(
        "ls -l %s/test_ln3 | awk '{print $NF}'" % tmpdir,
        shell=True) == b'test_ln2\n'

    # Test that chdir didn't change
    assert os.getcwd() == '/'


def test_exists(tmpdir):
    os.environ['UNITTEST_BASH'] = str(tmpdir)
    assert not sh.exists('$UNITTEST_BASH/test_exists')
    assert not sh.lexists('$UNITTEST_BASH/test_exists')

    with open('%s/test_exists' % tmpdir, 'w'):
        pass
    assert sh.exists('$UNITTEST_BASH/test_exists')
    assert sh.lexists('$UNITTEST_BASH/test_exists')


@unix_only
def test_exists_symlink(tmpdir):
    os.symlink('%s/a' % tmpdir, '%s/b' % tmpdir)
    assert not sh.exists('%s/b' % tmpdir)
    assert sh.lexists('%s/b' % tmpdir)

    with open('%s/a' % tmpdir, 'w'):
        pass
    assert sh.exists('%s/b' % tmpdir)
    assert sh.lexists('%s/b' % tmpdir)


def test_mkdir(tmpdir):
    os.environ['UNITTEST_BASH'] = str(tmpdir)
    sh.mkdir('$UNITTEST_BASH/test_mkdir', force=False, parents=False)
    assert os.path.isdir('%s/test_mkdir' % tmpdir)

    # Already existing
    with pytest.raises(FileExistsError):
        sh.mkdir('$UNITTEST_BASH/test_mkdir', force=False, parents=False)

    sh.mkdir('$UNITTEST_BASH/test_mkdir', force=True, parents=False)

    assert os.path.isdir('%s/test_mkdir' % tmpdir)

    # Accidentally overwrite a non-directory
    with open('%s/test_mkdir_file' % tmpdir, 'w'):
        pass

    with pytest.raises(FileExistsError):
        sh.mkdir('$UNITTEST_BASH/test_mkdir_file',
                 force=True, parents=False)

    # Missing middle path
    with pytest.raises(FileNotFoundError):
        sh.mkdir('$UNITTEST_BASH/middle/test_mkdir',
                 parents=False, force=False)

    sh.mkdir('$UNITTEST_BASH/middle/test_mkdir',
             parents=True, force=False)
    assert os.path.isdir('%s/middle/test_mkdir' % tmpdir)


@unix_only
def test_owner(tmpdir):
    os.environ['UNITTEST_BASH'] = str(tmpdir)
    with open('%s/test_owner' % tmpdir, 'w'):
        pass
    assert sh.owner('$UNITTEST_BASH/test_owner') == getpass.getuser()
