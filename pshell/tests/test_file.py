import getpass
import os
import subprocess

import pytest

import pshell as sh
from pshell.tests import StubError, get_name, unix_only


def test_remove(str_or_path, tmp_path):
    n = get_name()
    os.environ[n] = str(tmp_path)
    testpath = str_or_path(f"{tmp_path}/test_remove")
    testpath_env = str_or_path(f"${n}/test_remove")

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
def test_remove_symlinks(str_or_path, tmp_path):
    n = get_name()
    os.environ[n] = str(tmp_path)
    testpath = f"{tmp_path}/test_remove"
    testpath_env = str_or_path(f"${n}/test_remove")

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


def test_remove_noperm(tmp_path):
    testpath = tmp_path / "test_remove_noperm"
    os.makedirs(testpath / "foo" / "bar")
    os.chmod(testpath / "foo" / "bar", 0)
    with pytest.raises(PermissionError):
        sh.remove(testpath / "foo", recursive=True)

    sh.remove(testpath / "foo", recursive=True, rename_on_fail=True)
    assert not os.path.exists(testpath / "foo")
    fnames = list(testpath.glob("foo.DELETEME.*"))
    assert len(fnames) == 1

    # Explicit clean up (pytest won't do it)
    sh.remove(testpath, recursive=True, ignore_readonly=True)


def test_ignore_readonly1(tmp_path):
    """Test the ignore_readonly=True flag"""
    os.makedirs(f"{tmp_path}/foo/bar/baz")
    os.chmod(f"{tmp_path}/foo/bar/baz", 0o500)
    os.chmod(f"{tmp_path}/foo/bar", 0o500)
    os.chmod(f"{tmp_path}/foo", 0o500)

    with pytest.raises(PermissionError):
        sh.remove(f"{tmp_path}/foo", recursive=True)
    assert os.path.exists(f"{tmp_path}/foo/bar/baz")

    sh.remove(f"{tmp_path}/foo", force=False, recursive=True, ignore_readonly=True)
    assert not os.path.exists(f"{tmp_path}/foo")


def test_ignore_readonly2(tmp_path):
    """Test the case where there was no permission issue to begin with,
    so a double call to shutil.rmtree would raise FileNotFoundError
    """
    os.makedirs(f"{tmp_path}/foo/bar")
    sh.remove(f"{tmp_path}/foo", force=False, recursive=True, ignore_readonly=True)
    assert not os.path.exists(f"{tmp_path}/foo")


@pytest.mark.thread_unsafe("os.chdir")
def test_chdir(str_or_path, tmp_path):
    os.environ["UNITTEST_BASH"] = str(tmp_path)
    assert os.getcwd() != str(tmp_path)
    sh.chdir(str_or_path("$UNITTEST_BASH"))
    assert os.getcwd() == str(tmp_path)


@pytest.mark.thread_unsafe("os.chdir")
@pytest.mark.parametrize("use_env", [False, True])
def test_pushd(str_or_path, use_env, tmp_path):
    d0 = os.getcwd()
    assert d0 != str(tmp_path)
    if use_env:
        os.environ["UNITTEST_BASH"] = str(tmp_path)
        dir_to = str_or_path("$UNITTEST_BASH")
    else:
        dir_to = str_or_path(tmp_path)

    with sh.pushd(dir_to):
        assert os.getcwd() == str(tmp_path)
        # test that context manager is reentrant
        (tmp_path / "d1").mkdir()
        with sh.pushd(str_or_path("d1")):
            assert os.getcwd() == os.path.join(str(tmp_path), "d1")
        assert os.getcwd() == str(tmp_path)
    assert os.getcwd() == d0

    # Test that the cleanup also happens in case of Exception
    with pytest.raises(StubError), sh.pushd(dir_to):  # noqa:PT012
        assert os.getcwd() == str(tmp_path)
        raise StubError()
    assert os.getcwd() == d0


def test_move(str_or_path, tmp_path):
    n = get_name()
    os.environ[n] = str(tmp_path)
    (tmp_path / "test_move1").mkdir()
    sh.move(
        str_or_path(f"${n}/test_move1"),
        str_or_path(f"${n}/test_move2"),
    )
    assert not os.path.exists(f"{tmp_path}/test_move1")
    assert os.path.exists(f"{tmp_path}/test_move2")


def test_copy(str_or_path, tmp_path):
    n = get_name()
    os.environ[n] = str(tmp_path)
    # single file - copy to file
    with open(f"{tmp_path}/test_cp1", "w"):
        pass
    sh.copy(str_or_path(f"${n}/test_cp1"), str_or_path(f"${n}/test_cp2"))
    assert os.path.exists(f"{tmp_path}/test_cp1")
    assert os.path.exists(f"{tmp_path}/test_cp2")

    # single file - copy to directory
    (tmp_path / "test_cp3").mkdir()
    sh.copy(str_or_path(f"${n}/test_cp1"), str_or_path(f"${n}/test_cp3"))
    assert os.path.exists(f"{tmp_path}/test_cp1")
    assert os.path.exists(f"{tmp_path}/test_cp3/test_cp1")

    # recursive
    (tmp_path / "test_cp4").mkdir()
    (tmp_path / "test_cp4" / "dir2").mkdir()
    sh.copy(str_or_path(f"${n}/test_cp4"), str_or_path(f"${n}/test_cp5"))
    assert os.path.exists(f"{tmp_path}/test_cp4/dir2")
    assert os.path.exists(f"{tmp_path}/test_cp5/dir2")


# input does not exist
def test_copy_err_input_not_found():
    with pytest.raises(FileNotFoundError):
        sh.copy("/does/not/exist", "./")


# single file to non-existing directory
def test_copy_err_target_dir_not_found(tmp_path):
    n = get_name()
    os.environ[n] = str(tmp_path)
    with open(f"{tmp_path}/test_cp_err2", "w"):
        pass
    with pytest.raises(FileNotFoundError):
        sh.copy(f"${n}/test_cp_err2", f"${n}/does/not/exist")


# directory to non-existing parent directory automatically creates parents
def test_copy_dir_to_missing_parent(str_or_path, tmp_path):
    n = get_name()
    os.environ[n] = str(tmp_path)
    (tmp_path / "test_cpdir").mkdir()
    sh.copy(
        str_or_path(f"${n}/test_cpdir"),
        str_or_path(f"${n}/does/not/exist"),
    )
    assert os.path.exists(f"{tmp_path}/does/not/exist")


# directory to already existing target
def test_copy_err_fileexist(tmp_path):
    n = get_name()
    os.environ[n] = str(tmp_path)
    (tmp_path / "test_cp_err4a").mkdir()
    (tmp_path / "test_cp_err4b").mkdir()
    with pytest.raises(FileExistsError):
        sh.copy(f"${n}/test_cp_err4a", f"${n}/test_cp_err4b")


def test_backup(str_or_path, tmp_path):
    n = get_name()
    os.environ[n] = str(tmp_path)
    fname = f"{tmp_path}/test"
    fname_env = str_or_path(f"${n}/test")
    with open(fname, "w"):
        pass

    # Auto extension
    new_fname = sh.backup(fname_env, action="copy")
    assert os.path.exists(fname)
    assert os.path.exists(sh.resolve_env(new_fname))

    # Manual extension
    new_fname = sh.backup(fname_env, suffix="bak", action="copy")
    assert os.path.exists(f"{tmp_path}/test.bak")
    assert str(new_fname) == str(str_or_path(f"${n}/test.bak"))
    assert isinstance(new_fname, str_or_path)

    # Collisions in the backup name will generate a unique new name
    new_fname = sh.backup(fname_env, suffix="bak", action="copy")
    assert os.path.exists(f"{tmp_path}/test.bak.2")
    assert str(new_fname) == str(str_or_path(f"${n}/test.bak.2"))
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
def test_symlink(str_or_path, tmp_path):
    n = get_name()
    os.environ[n] = str(tmp_path)
    os.chdir("/")
    with open(f"{tmp_path}/test_ln1", "w"):
        pass
    with open(f"{tmp_path}/test_ln2", "w"):
        pass

    # abspath = False
    sh.symlink(
        str_or_path(f"${n}/test_ln1"),
        str_or_path(f"${n}/test_ln3"),
        abspath=False,
    )
    assert (
        subprocess.check_output(
            f"ls -l {tmp_path}/test_ln3 | awk '{{print $NF}}'", shell=True
        )
        == b"test_ln1\n"
    )
    os.remove(f"{tmp_path}/test_ln3")

    # abspath = True
    sh.symlink(
        str_or_path(f"${n}/test_ln1"), str_or_path(f"${n}/test_ln3"), abspath=True
    )
    assert (
        subprocess.check_output(
            f"ls -l {tmp_path}/test_ln3 | awk '{{print $NF}}'", shell=True
        ).decode("utf-8")
        == f"{tmp_path}/test_ln1\n"
    )

    # no force
    with pytest.raises(FileExistsError):
        sh.symlink(
            str_or_path(f"${n}/test_ln2"), str_or_path(f"${n}/test_ln3"), force=False
        )

    # force must work only to override another symlink, NOT another regular file
    with pytest.raises(FileExistsError):
        sh.symlink(
            str_or_path(f"${n}/test_ln1"), str_or_path(f"${n}/test_ln2"), force=True
        )

    # force; old symlink is different
    sh.symlink(str_or_path(f"${n}/test_ln2"), str_or_path(f"${n}/test_ln3"), force=True)
    assert (
        subprocess.check_output(
            f"ls -l {tmp_path}/test_ln3 | awk '{{print $NF}}'", shell=True
        )
        == b"test_ln2\n"
    )

    # force; old symlink is identical
    sh.symlink(str_or_path(f"${n}/test_ln2"), str_or_path(f"${n}/test_ln3"), force=True)
    assert (
        subprocess.check_output(
            f"ls -l {tmp_path}/test_ln3 | awk '{{print $NF}}'", shell=True
        )
        == b"test_ln2\n"
    )

    # Test that chdir didn't change
    assert os.getcwd() == "/"


def test_exists(str_or_path, tmp_path):
    n = get_name()
    os.environ[n] = str(tmp_path)
    assert not sh.exists(str_or_path(f"${n}/test_exists"))
    assert not sh.lexists(str_or_path(f"${n}/test_exists"))

    with open(f"{tmp_path}/test_exists", "w"):
        pass
    assert sh.exists(str_or_path(f"${n}/test_exists"))
    assert sh.lexists(str_or_path(f"${n}/test_exists"))


@unix_only
def test_exists_symlink(str_or_path, tmp_path):
    os.symlink(f"{tmp_path}/a", f"{tmp_path}/b")
    assert not sh.exists(str_or_path(f"{tmp_path}/b"))
    assert sh.lexists(str_or_path(f"{tmp_path}/b"))

    with open(f"{tmp_path}/a", "w"):
        pass
    assert sh.exists(f"{tmp_path}/b")
    assert sh.lexists(f"{tmp_path}/b")


def test_mkdir(str_or_path, tmp_path):
    n = get_name()
    os.environ[n] = str(tmp_path)
    sh.mkdir(str_or_path(f"${n}/test_mkdir"), force=False, parents=False)
    assert os.path.isdir(f"{tmp_path}/test_mkdir")

    # Already existing
    with pytest.raises(FileExistsError):
        sh.mkdir(str_or_path(f"${n}/test_mkdir"), force=False, parents=False)

    sh.mkdir(str_or_path(f"${n}/test_mkdir"), force=True, parents=False)

    assert os.path.isdir(f"{tmp_path}/test_mkdir")

    # Accidentally overwrite a non-directory
    with open(f"{tmp_path}/test_mkdir_file", "w"):
        pass

    with pytest.raises(FileExistsError):
        sh.mkdir(str_or_path(f"${n}/test_mkdir_file"), force=True, parents=False)

    # Missing middle path
    with pytest.raises(FileNotFoundError):
        sh.mkdir(str_or_path(f"${n}/middle/test_mkdir"), parents=False, force=False)

    sh.mkdir(str_or_path(f"${n}/middle/test_mkdir"), parents=True, force=False)
    assert os.path.isdir(f"{tmp_path}/middle/test_mkdir")


@unix_only
def test_owner(str_or_path, tmp_path):
    n = get_name()
    os.environ[n] = str(tmp_path)
    with open(f"{tmp_path}/test_owner", "w"):
        pass
    assert sh.owner(str_or_path(f"${n}/test_owner")) == getpass.getuser()
