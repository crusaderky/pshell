"""Functions for handling files and directories
"""
import datetime
import errno
import logging
import os
import shutil
import stat
from contextlib import contextmanager
from .env import resolve_env


__all__ = ('remove', 'chdir', 'pushd', 'move', 'copy', 'backup', 'symlink',
           'exists', 'lexists', 'mkdir', 'owner')


def _unix_only():
    """Crash if running on Windows
    """
    if os.name == 'nt':
        raise EnvironmentError("Not supported on Windows")


def remove(path, *, recursive=False, force=True, ignore_readonly=False,
           rename_on_fail=False):
    """Remove file or directory

    :param str path:
        Target file or directory
    :param bool recursive:
        If True, recursively delete tree starting at path
    :param bool force:
        If True, don't raise OSError if path doesn't exist
    :param bool ignore_readonly:
        If True, also delete files and directories with the read-only flag
    :param bool rename_on_fail:
        If True, don't raise OSError if deletion fails.
        This typically happens if the user does not have enough permissions
        to delete the file or directory, or in case of NFS locks.
        In this case, rename the file to <path>.DELETEME.<timestamp>.
        If the rename also fails, then raise OSError.
    :raise FileNotFoundError:
        If ``force==False`` and path doesn't exist
    :raise OSError:
        - if ``rename_on_fail==False`` and path can't be deleted
        - if ``rename_on_fail==True`` and path can be neither deleted nor
          renamed
    """
    realpath = resolve_env(path)

    logging.info("Deleting %s", path)
    try:
        if os.path.islink(realpath):
            os.remove(realpath)
        elif recursive and os.path.isdir(realpath):
            if ignore_readonly:
                # Potentially perform a two-pass deletion
                # On the first round, every time there is a failure deleting
                # something do chmod u+w on the failed path and continue
                has_errors = False

                def onerror(function, path, excinfo):
                    # Do not act only on PermissionError.
                    # It could also be OSError('Directory not empty').
                    nonlocal has_errors
                    has_errors = True
                    try:
                        # chmod u+w
                        mode = os.stat(path).st_mode
                        os.chmod(path, mode | stat.S_IWUSR)
                    except OSError:
                        pass
                shutil.rmtree(realpath, onerror=onerror)

                # If there were any errors on the first round, perform a second
                # deletion pass this time with no error control. At this point,
                # if the only problems were caused by read-only files owned by
                # the current user they should not crop up anymore. Raise
                # exception in eny other case (e.g. directory owned by another
                # user, file not found)
                if has_errors:
                    shutil.rmtree(realpath)
            else:  # not ignore_readonly
                # Directly perform recursive deletion with no error control.
                # Raise exception in case of read-only files.
                shutil.rmtree(realpath)
        elif os.path.isdir(realpath):
            os.rmdir(realpath)
        else:
            os.remove(realpath)
    except OSError as e:
        if force and e.errno == errno.ENOENT:
            # Graciously do nothing if the file does not exist to begin with.
            # Note: this is different than testing for existence and then
            # deleting, as it prevents race conditions when the same path is
            # being deleted from multiple scripts in parallel.
            logging.info("%s", e)
        elif rename_on_fail and e.errno != errno.ENOENT:
            logging.warning("%s", e)
            timestamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
            backup(path, suffix='DELETEME.' + timestamp, action='move')
        else:
            raise


def chdir(path):
    """Move the present-working directory (pwd) into the target directory.
    """
    if path == '':
        path = '.'
    logging.info("chdir %s", path)
    os.chdir(resolve_env(path))


@contextmanager
def pushd(path):
    """Context manager that moves the pwd into target directory. When leaving
    the context, the pwd is changed back to what it originally was.

    Usage::

        with pushd("mydir"):
            ...

    Is equivalent to the bash commands::

        pushd mydir
        ...
        popd
    """
    if path == '':
        path = '.'

    cwd = os.getcwd()
    logging.info("pushd %s", path)
    os.chdir(resolve_env(path))
    try:
        yield
    finally:
        logging.info("popd")
        os.chdir(cwd)


def move(src, dst):
    """Recursively move a file or directory (src) to another location (dst).
    If the destination is a directory or a symlink to a directory, then src is
    moved inside that directory. The destination directory must not already
    exist. If the destination already exists but is not a directory, it may be
    overwritten depending on :func:`os.rename` semantics.
    """
    logging.info("Moving %s to %s", src, dst)
    shutil.move(resolve_env(src), resolve_env(dst))


def copy(src, dst, *, ignore=None):
    """Recursively copy a file or directory. If src is a regular file and dst
    is a directory, a file with the same basename as src is created (or
    overwritten) in the directory specified. Permission bits and last modified
    dates are copied. Symlinks are preserved. Users and groups are discarded.

    .. note::
       This function behaves slightly differently from bash when src is a
       directory. bash alters its behaviour if dst exists or not, e.g.::

         $ mkdir foo
         $ touch foo/hello.txt
         $ cp -r foo bar        # First copy; bar does not exist
         $ cp -r foo bar        # Identical command as before;
                                # but it will behave differently!
         $ find
         ./bar
         ./bar/hello.txt
         ./bar/foo
         ./bar/foo/hello.txt
         ./foo
         ./foo/hello.txt

       This function instead always requires the full destination path; the
       second invocation of ``copy('foo', 'bar')`` will raise
       :class:`FileExistsError` because ``bar`` already exists.

    :param ignore:
        Only effective when copying a directory. See :func:`shutil.copytree`.
    """
    logging.info("Copying %s to %s", src, dst)
    src = resolve_env(src)
    dst = resolve_env(dst)
    if os.path.isdir(src):
        if os.path.exists(dst):
            raise FileExistsError(errno.EEXIST, "File exists", dst)
        shutil.copytree(src, dst, symlinks=True, ignore=ignore)
    else:
        shutil.copy2(src, dst)


def backup(path, *, suffix=None, force=False, action='copy'):
    """Recursively copy or move a file of directory from <path> to
    <path>.<suffix>.

    :param str suffix:
        suffix for the backup file. Default: .YYYYMMDD-HHMMSS
    :param bool force:
        if True, silently do nothing if file doesn't exist.
    :param str action:
        copy|move
    :raise FileNotFoundError:
        if path does not exist and force=False
    :returns:
        renamed path, or None if no backup was performed
    """
    assert action in ('copy', 'move')

    if force and not os.path.lexists(resolve_env(path)):
        # Do nothing
        logging.info("%s does not exist, skipping backup", path)
        return None

    if suffix is None:
        suffix = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")

    path_bak = "%s.%s" % (path, suffix)

    # In case of collision, call the subsequent backups as .2, .3, etc.
    i = 2
    while os.path.lexists(resolve_env(path_bak)):
        logging.info("%s already exists, generating a unique name")
        path_bak = "%s.%s.%d" % (path, suffix, i)
        i += 1

    if action == 'copy':
        copy(path, path_bak)
    else:
        move(path, path_bak)

    return path_bak


def symlink(src, dst, *, force=False, abspath=False):
    """Create a symbolic link pointing to src named dst.

    This exclusively works in Unix, on POSIX-compatible filesystems.

    :param bool force:
        if True, remove previous dst if it exists and it's a different symlink.
        If it's the same symlink, do not replace it in order to prevent race
        conditions.
    :param bool abspath:
        if False, build the shortest possible relative link. If True, generate
        a link using absolute paths. This is regardless of src and dst being
        absolute or relative paths, and regardless of the current working
        directory (cwd).

    Examples::

        >>> symlink('/common/foo', '/common/bar')
        /common/foo => bar

        >>> symlink('/common/foo', '/common/bar', abspath=True)
        /common/foo => /common/bar

        >>> chdir('/common')
        >>> symlink('foo', 'bar')
        /common/foo => bar

        >>> chdir('/common')
        >>> symlink('foo', 'bar', abspath=True)
        /common/foo => /common/bar
    """
    _unix_only()

    real_src = os.path.abspath(resolve_env(src))
    real_dst = os.path.abspath(resolve_env(dst))
    if force and os.path.islink(real_dst):
        if os.path.abspath(os.path.realpath(real_dst)) == real_src:
            logging.info("Symlink %s => %s already exists", src, dst)
            return
        remove(dst)

    logging.info("Creating symlink %s => %s", src, dst)

    if abspath:
        os.symlink(real_src, real_dst)
    else:
        cwd_backup = os.getcwd()
        os.chdir(os.path.realpath(os.path.dirname(real_dst)))
        try:
            # Generate shortest possible relative path
            real_src = os.path.relpath(os.path.realpath(real_src))
            real_dst = os.path.relpath(os.path.realpath(real_dst))
            os.symlink(real_src, real_dst)
        finally:
            os.chdir(cwd_backup)


def exists(path):
    """Wrapper around :func:`os.path.exists`, with automated resolution of
    environment variables and logging.
    """
    respath = resolve_env(path)
    if os.path.exists(respath):
        logging.debug("File exists: %s", path)
        return True
    logging.debug("File does not exist or is a broken symlink: %s", path)
    return False


def lexists(path):
    """Wrapper around :func:`os.path.lexists`, with automated resolution of
    environment variables and logging.
    """
    respath = resolve_env(path)
    if os.path.lexists(respath):
        logging.debug("File exists: %s", path)
        return True
    logging.debug("File does not exist: %s", path)
    return False


def mkdir(path, *, parents=True, force=True):
    """Create target directory.

    This function is safe for use in concurrent environments, where multiple
    actors try to simultaneously create the same directory.

    :param str path:
        directory to be created
    :param bool parents:
        if True, also create parent directories if necessary.
    :param bool force:
        if True, do nothing if <path> already exists.
    """
    respath = resolve_env(path)

    logging.info("Creating directory %s", path)
    try:
        if parents:
            os.makedirs(respath)
        else:
            os.mkdir(respath)
    except OSError:
        # Cannot rely on checking for EEXIST, since the operating system
        # could give priority to other errors like EACCES or EROFS
        if force and os.path.isdir(respath):
            logging.info("Directory %s already exists", path)
        else:
            raise


def owner(fname):
    """Return the username of the user owning a file.

    This function is not available on Windows.
    """
    _unix_only()

    # Unix-only module
    import pwd

    fname = resolve_env(fname)
    numeric_uid = os.stat(fname).st_uid
    return pwd.getpwuid(numeric_uid).pw_name
