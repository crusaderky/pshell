"""Search and file system traversal functions
"""
from __future__ import annotations

import glob as _glob
from collections.abc import Iterator
from pathlib import Path
from typing import overload

from pshell import log
from pshell.env import resolve_env

__all__ = ("FileMatchError", "glob", "iglob")


class FileMatchError(Exception):
    """:func:`glob` or :func:`iglob` returned not enough or too many matches"""

    @property
    def pathname(self) -> str | Path:
        return self.args[0]

    @property
    def min_results(self) -> int:
        return self.args[1]

    @property
    def max_results(self) -> int | None:
        return self.args[2]

    @property
    def got_results(self) -> int:
        return self.args[3]

    @property
    def maybe_extra_results(self) -> bool:
        try:
            return self.args[4]
        except IndexError:
            return False

    def __str__(self) -> str:
        msg = f"File match '{self.pathname}' produced "
        if self.maybe_extra_results:
            msg += "at least "
        msg += f"{self.got_results} results; expected"

        if self.max_results is None:
            return f"{msg} at least {self.min_results}"
        elif self.max_results == self.min_results:
            return f"{msg} exactly {self.min_results}"
        elif self.min_results > 0:
            return f"{msg} between {self.min_results} and {self.max_results}"
        else:
            return f"{msg} up to {self.max_results}"


@overload
def glob(
    pathname: str, *, min_results: int = 0, max_results: int | None = None
) -> list[str]:
    ...


@overload
def glob(
    pathname: Path, *, min_results: int = 0, max_results: int | None = None
) -> list[Path]:
    ...


def glob(
    pathname: str | Path, *, min_results: int = 0, max_results: int | None = None
) -> list[str] | list[Path]:
    """Like :func:`glob.glob`, but in addition it supports environment
    variables in pathname, logs the number of results, and incorporates
    protection from non-existing paths.

    :param pathname:
        Bash-like wildcard expression. Can be a string or a :class:`pathlib.Path`.
    :param int min_results:
        Minimum number of expected results
    :param int max_results:
        Maximum number of expected results. Omit for no maximum.
    :raises FileMatchError:
        If found less results than min_results or more than max_results
    :returns:
        List of matching files or directories.
        The return type of the outputs matches the type of pathname.
    """
    if min_results < 0:
        raise ValueError("min_results must be greater than 0")
    if max_results is not None and max_results < min_results:
        raise ValueError("max_results must be greater or equal to min_results")

    results = _glob.glob(resolve_env(str(pathname)), recursive=True)
    if len(results) < min_results or (
        max_results is not None and len(results) > max_results
    ):
        raise FileMatchError(pathname, min_results, max_results, len(results))

    log.info("File match %s produced %d results", pathname, len(results))
    return [Path(r) for r in results] if isinstance(pathname, Path) else results


@overload
def iglob(
    pathname: str, *, min_results: int = 0, max_results: int | None = None
) -> Iterator[str]:
    ...  # pragma: nocover


@overload
def iglob(
    pathname: Path, *, min_results: int = 0, max_results: int | None = None
) -> Iterator[Path]:
    ...  # pragma: nocover


def iglob(
    pathname: str | Path, *, min_results: int = 0, max_results: int | None = None
) -> Iterator[str] | Iterator[Path]:
    """Like :func:`glob`, but returns an iterator instead.
    Notice that, unlike with glob, you may have time to process some of the
    results before :class:`FileMatchError` is raised.

    In case ``max_results`` is exceeded, the iteration will stop
    immediately - which will save time and memory.

    Example::

        >>> for fname in glob("test*.txt", max_results=2):
        >>>    print(fname)
        FileMatchError: File match test*.txt produced 4 results, expected up
                        to 2

        >>> for fname in iglob("test*.txt", max_results=2):
        >>>    print(fname)
        test1.txt
        test2.txt
        FileMatchError: File match test*.txt produced 3 or more results,
                        expected up to 2
    """
    if min_results < 0:
        raise ValueError("min_results must be greater than 0")
    if max_results is not None and max_results < min_results:
        raise ValueError("max_results must be greater or equal to min_results")

    count = 0
    for result in _glob.iglob(resolve_env(str(pathname)), recursive=True):
        count += 1
        if max_results is not None and count > max_results:
            raise FileMatchError(pathname, min_results, max_results, count, True)
        yield Path(result) if isinstance(pathname, Path) else result

    if count < min_results:
        raise FileMatchError(pathname, min_results, max_results, count)

    log.info("File match %s produced %d results", pathname, count)
