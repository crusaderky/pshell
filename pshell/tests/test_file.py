import getpass
import glob
import os
import subprocess

import pytest

import pshell as sh
from pshell.tests import StubError, unix_only


def test_remove(str_or_path, tmpdir):
    os.environ["UNITTEST_BASH"] = str(tmpdir)
    testpath = str_or_path(f"{tmpdir}/test_remove")
    testpath_env = str_or_path("$UNITTEST_BASH/test_remove")

    # remove file
    with open(testpath, "w"):
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
    os.mkdir(f"{testpath}/dir2")
    sh.remove(testpath_env, recursive=True)
    assert not os.path.exists(testpath)

    # recursive must also work on a file
    with open(testpath, "w"):
        pass
    assert os.path.exists(testpath)
    sh.remove(testpath_env, recursive=True)
    assert not os.path.exists(testpath)


@unix_only
def test_remove_symlinks(str_or_path, tmpdir):
    os.environ["UNITTEST_BASH"] = str(tmpdir)
    testpath = f"{tmpdir}/test_remove"
    testpath_env = str_or_path("$UNITTEST_BASH/test_remove")

    # remove dir and symlink to dir
    os.mkdir(testpath)
    os.symlink(testpath, testpath + ".lnk")
    assert os.path.exists(testpath)
    assert os.path.exists(testpath + ".lnk")
    sh.remove(f"{testpath_env}.lnk")
    sh.remove(testpath_env)
    assert not os.path.exists(testpath)
    assert not os.path.exists(testpath + ".lnk")

    # recursive on a symlink to dir must delete the symlink
    os.mkdir(testpath)
    with open(f"{testpath}/donttouch", "w"):
        pass
    os.symlink(testpath, testpath + ".lnk")
    sh.remove(f"{testpath_env}.lnk", recursive=True)
    assert not os.path.exists(testpath + ".lnk")
    assert os.path.exists(f"{testpath}/donttouch")
    os.remove(f"{testpath}/donttouch")
    os.rmdir(testpath)


def test_remove_force1():
    with pytest.raises(FileNotFoundError):
        sh.remove("NOTEXIST.txt", force=False)


def test_remove_force2():
    sh.remove("NOTEXIST.txt", force=True)


def test_remove_noperm(tmpdir):
    testpath = "%s/test_remove_noperm" % tmpdir
    os.makedirs(testpath + "/foo/bar")
    os.chmod(testpath + "/foo/bar", 0)
    with pytest.raises(PermissionError):
        sh.remove(testpath + "/foo", recursive=True)

    sh.remove(testpath + "/foo", recursive=True, rename_on_fail=True)
    assert not os.path.exists(testpath + "/foo")
    assert len(glob.glob(testpath + "/foo.DELETEME.*")) == 1


def test_ignore_readonly1(tmpdir):
    """Test the ignore_readonly=True flag"""
    os.makedirs(f"{tmpdir}/foo/bar/baz")
    os.chmod(f"{tmpdir}/foo/bar/baz", 0o500)
    os.chmod(f"{tmpdir}/foo/bar", 0o500)
    os.chmod(f"{tmpdir}/foo", 0o500)

    with pytest.raises(PermissionError):
        sh.remove(f"{tmpdir}/foo", recursive=True)
    assert os.path.exists(f"{tmpdir}/foo/bar/baz")

    sh.remove(f"{tmpdir}/foo", force=False, recursive=True, ignore_readonly=True)
    assert not os.path.exists(f"{tmpdir}/foo")


def test_ignore_readonly2(tmpdir):
    """Test the case where there was no permission issue to begin with,
    so a double call to shutil.rmtree would raise FileNotFoundError
    """
    os.makedirs(f"{tmpdir}/foo/bar")
    sh.remove(f"{tmpdir}/foo", force=False, recursive=True, ignore_readonly=True)
    assert not os.path.exists(f"{tmpdir}/foo")


def test_chdir(str_or_path, tmpdir):
    os.environ["UNITTEST_BASH"] = str(tmpdir)
    assert os.getcwd() != str(tmpdir)
    sh.chdir(str_or_path("$UNITTEST_BASH"))
    assert os.getcwd() == str(tmpdir)


@pytest.mark.parametrize("use_env", [False, True])
def test_pushd(str_or_path, use_env, tmpdir):
    d0 = os.getcwd()
    assert d0 != str(tmpdir)
    if use_env:
        os.environ["UNITTEST_BASH"] = str(tmpdir)
        dir_to = str_or_path("$UNITTEST_BASH")
    else:
        dir_to = str_or_path(tmpdir)

    with sh.pushd(dir_to):
        assert os.getcwd() == str(tmpdir)
        # test that context manager is reentrant
        tmpdir.mkdir("d1")
        with sh.pushd(str_or_path("d1")):
            assert os.getcwd() == os.path.join(str(tmpdir), "d1")
        assert os.getcwd() == str(tmpdir)
    assert os.getcwd() == d0

    # Test that the cleanup also happens in case of Exception
    with pytest.raises(StubError), sh.pushd(dir_to):
        assert os.getcwd() == str(tmpdir)
        raise StubError()
    assert os.getcwd() == d0


def test_move(str_or_path, tmpdir):
    os.environ["UNITTEST_BASH"] = str(tmpdir)
    tmpdir.mkdir("test_move1")
    sh.move(
        str_or_path("$UNITTEST_BASH/test_move1"),
        str_or_path("$UNITTEST_BASH/test_move2"),
    )
    assert not os.path.exists(f"{tmpdir}/test_move1")
    assert os.path.exists(f"{tmpdir}/test_move2")


def test_copy(str_or_path, tmpdir):
    os.environ["UNITTEST_BASH"] = str(tmpdir)
    # single file - copy to file
    with open(f"{tmpdir}/test_cp1", "w"):
        pass
    sh.copy(
        str_or_path("$UNITTEST_BASH/test_cp1"), str_or_path("$UNITTEST_BASH/test_cp2")
    )
    assert os.path.exists(f"{tmpdir}/test_cp1")
    assert os.path.exists(f"{tmpdir}/test_cp2")

    # single file - copy to directory
    tmpdir.mkdir("test_cp3")
    sh.copy(
        str_or_path("$UNITTEST_BASH/test_cp1"), str_or_path("$UNITTEST_BASH/test_cp3")
    )
    assert os.path.exists(f"{tmpdir}/test_cp1")
    assert os.path.exists(f"{tmpdir}/test_cp3/test_cp1")

    # recursive
    tmpdir.mkdir("test_cp4")
    tmpdir.mkdir("test_cp4/dir2")
    sh.copy(
        str_or_path("$UNITTEST_BASH/test_cp4"), str_or_path("$UNITTEST_BASH/test_cp5")
    )
    assert os.path.exists(f"{tmpdir}/test_cp4/dir2")
    assert os.path.exists(f"{tmpdir}/test_cp5/dir2")


# input does not exist
def test_copy_err_input_not_found():
    with pytest.raises(FileNotFoundError):
        sh.copy("/does/not/exist", "$UNITTEST_BASH/")


# single file to non-existing directory
def test_copy_err_target_dir_not_found(tmpdir):
    os.environ["UNITTEST_BASH"] = str(tmpdir)
    with open(f"{tmpdir}/test_cp_err2", "w"):
        pass
    with pytest.raises(FileNotFoundError):
        sh.copy("$UNITTEST_BASH/test_cp_err2", "$UNITTEST_BASH/does/not/exist")


# directory to non-existing parent directory automatically creates parents
def test_copy_dir_to_missing_parent(str_or_path, tmpdir):
    os.environ["UNITTEST_BASH"] = str(tmpdir)
    tmpdir.mkdir("test_cpdir")
    sh.copy(
        str_or_path("$UNITTEST_BASH/test_cpdir"),
        str_or_path("$UNITTEST_BASH/does/not/exist"),
    )
    assert os.path.exists(f"{tmpdir}/does/not/exist")


# directory to already existing target
def test_copy_err_fileexist(tmpdir):
    os.environ["UNITTEST_BASH"] = str(tmpdir)
    tmpdir.mkdir("test_cp_err4a")
    tmpdir.mkdir("test_cp_err4b")
    with pytest.raises(FileExistsError):
        sh.copy("$UNITTEST_BASH/test_cp_err4a", "$UNITTEST_BASH/test_cp_err4b")


def test_backup(str_or_path, tmpdir):
    os.environ["UNITTEST_BASH"] = str(tmpdir)
    fname = f"{tmpdir}/test"
    fname_env = str_or_path("$UNITTEST_BASH/test")
    with open(fname, "w"):
        pass

    # Auto extension
    new_fname = sh.backup(fname_env, action="copy")
    assert os.path.exists(fname)
    assert os.path.exists(sh.resolve_env(new_fname))

    # Manual extension
    new_fname = sh.backup(fname_env, suffix="bak", action="copy")
    assert os.path.exists(f"{tmpdir}/test.bak")
    assert str(new_fname) == str(str_or_path("$UNITTEST_BASH/test.bak"))
    assert isinstance(new_fname, str_or_path)

    # Collisions in the backup name will generate a unique new name
    new_fname = sh.backup(fname_env, suffix="bak", action="copy")
    assert os.path.exists(f"{tmpdir}/test.bak.2")
    assert str(new_fname) == str(str_or_path("$UNITTEST_BASH/test.bak.2"))
    assert isinstance(new_fname, str_or_path)

    # action='move'
    new_fname = sh.backup(fname_env, action="move")
    assert not os.path.exists(fname)
    assert os.path.exists(sh.resolve_env(new_fname))
    assert isinstance(new_fname, str_or_path)


def test_backup_notexist():
    with pytest.raises(FileNotFoundError):
        sh.backup("notexist.txt")


def test_backup_notexist_force():
    assert sh.backup("notexist.txt", force=True) is None


@unix_only
def test_symlink(str_or_path, tmpdir):
    os.environ["UNITTEST_BASH"] = str(tmpdir)
    os.chdir("/")
    with open(f"{tmpdir}/test_ln1", "w"):
        pass
    with open(f"{tmpdir}/test_ln2", "w"):
        pass

    # abspath = False
    sh.symlink(
        str_or_path("$UNITTEST_BASH/test_ln1"),
        str_or_path("$UNITTEST_BASH/test_ln3"),
        abspath=False,
    )
    assert (
        subprocess.check_output(
            "ls -l %s/test_ln3 | awk '{print $NF}'" % tmpdir, shell=True
        )
        == b"test_ln1\n"
    )
    os.remove(f"{tmpdir}/test_ln3")

    # abspath = True
    sh.symlink(
        str_or_path("$UNITTEST_BASH/test_ln1"),
        str_or_path("$UNITTEST_BASH/test_ln3"),
        abspath=True,
    )
    assert (
        subprocess.check_output(
            "ls -l %s/test_ln3 | awk '{print $NF}'" % tmpdir, shell=True
        ).decode("utf-8")
        == f"{tmpdir}/test_ln1\n"
    )

    # no force
    with pytest.raises(FileExistsError):
        sh.symlink(
            str_or_path("$UNITTEST_BASH/test_ln2"),
            str_or_path("$UNITTEST_BASH/test_ln3"),
            force=False,
        )

    # force must work only to override another symlink, NOT another regular file
    with pytest.raises(FileExistsError):
        sh.symlink(
            str_or_path("$UNITTEST_BASH/test_ln1"),
            str_or_path("$UNITTEST_BASH/test_ln2"),
            force=True,
        )

    # force; old symlink is different
    sh.symlink(
        str_or_path("$UNITTEST_BASH/test_ln2"),
        str_or_path("$UNITTEST_BASH/test_ln3"),
        force=True,
    )
    assert (
        subprocess.check_output(
            "ls -l %s/test_ln3 | awk '{print $NF}'" % tmpdir, shell=True
        )
        == b"test_ln2\n"
    )

    # force; old symlink is identical
    sh.symlink(
        str_or_path("$UNITTEST_BASH/test_ln2"),
        str_or_path("$UNITTEST_BASH/test_ln3"),
        force=True,
    )
    assert (
        subprocess.check_output(
            "ls -l %s/test_ln3 | awk '{print $NF}'" % tmpdir, shell=True
        )
        == b"test_ln2\n"
    )

    # Test that chdir didn't change
    assert os.getcwd() == "/"


def test_exists(str_or_path, tmpdir):
    os.environ["UNITTEST_BASH"] = str(tmpdir)
    assert not sh.exists(str_or_path("$UNITTEST_BASH/test_exists"))
    assert not sh.lexists(str_or_path("$UNITTEST_BASH/test_exists"))

    with open(f"{tmpdir}/test_exists", "w"):
        pass
    assert sh.exists(str_or_path("$UNITTEST_BASH/test_exists"))
    assert sh.lexists(str_or_path("$UNITTEST_BASH/test_exists"))


@unix_only
def test_exists_symlink(str_or_path, tmpdir):
    os.symlink(f"{tmpdir}/a", f"{tmpdir}/b")
    assert not sh.exists(str_or_path(f"{tmpdir}/b"))
    assert sh.lexists(str_or_path(f"{tmpdir}/b"))

    with open(f"{tmpdir}/a", "w"):
        pass
    assert sh.exists(f"{tmpdir}/b")
    assert sh.lexists(f"{tmpdir}/b")


def test_mkdir(str_or_path, tmpdir):
    os.environ["UNITTEST_BASH"] = str(tmpdir)
    sh.mkdir(str_or_path("$UNITTEST_BASH/test_mkdir"), force=False, parents=False)
    assert os.path.isdir(f"{tmpdir}/test_mkdir")

    # Already existing
    with pytest.raises(FileExistsError):
        sh.mkdir(str_or_path("$UNITTEST_BASH/test_mkdir"), force=False, parents=False)

    sh.mkdir(str_or_path("$UNITTEST_BASH/test_mkdir"), force=True, parents=False)

    assert os.path.isdir(f"{tmpdir}/test_mkdir")

    # Accidentally overwrite a non-directory
    with open(f"{tmpdir}/test_mkdir_file", "w"):
        pass

    with pytest.raises(FileExistsError):
        sh.mkdir(
            str_or_path("$UNITTEST_BASH/test_mkdir_file"), force=True, parents=False
        )

    # Missing middle path
    with pytest.raises(FileNotFoundError):
        sh.mkdir(
            str_or_path("$UNITTEST_BASH/middle/test_mkdir"), parents=False, force=False
        )

    sh.mkdir(str_or_path("$UNITTEST_BASH/middle/test_mkdir"), parents=True, force=False)
    assert os.path.isdir(f"{tmpdir}/middle/test_mkdir")


@unix_only
def test_owner(str_or_path, tmpdir):
    os.environ["UNITTEST_BASH"] = str(tmpdir)
    with open(f"{tmpdir}/test_owner", "w"):
        pass
    assert sh.owner(str_or_path("$UNITTEST_BASH/test_owner")) == getpass.getuser()
