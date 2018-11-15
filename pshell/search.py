"""Search and file system traversal functions
"""
import glob as _glob
import logging
from .env import resolve_env


__all__ = ('FileMatchError', 'glob', 'iglob')


class FileMatchError(Exception):
    """:func:`glob` or :func:`iglob` returned not enough or too many matches
    """
    @classmethod
    def build(cls, pathname, min_results, max_results, got_results,
              or_more=False):
        """Build the message string

        .. note::
           All Exceptions must support being rebuilt from str(self), in order
           to transit from a process pool executor back to the main process
           through pickle/unpickle. This is why we can't just define __init__
           with all these arguments.

        :returns:
            new FileMatchError object
        """
        msg = "File match '%s' produced %d%s results, expected " % (
            pathname, got_results, " or more" if or_more else "")
        if max_results is None:
            msg += "at least %d" % min_results
        elif max_results == min_results:
            msg += "exactly %d" % min_results
        elif min_results > 0:
            msg += "between %d and %d" % (min_results, max_results)
        else:
            msg += "up to %d" % max_results

        return cls(msg)


def glob(pathname, *, min_results=0, max_results=None):
    """Like :func:`glob.glob`, but in addition it supports environment
    variables in pathname, logs the number of results, and incorporates
    protection from non-existing paths.

    :param str pathname:
        bash-like wildcard expression
    :param int min_results:
        minimum number of expected results
    :param int max_results:
        maximum number of expected results. Omit for no maximum.
    :raises FileMatchError:
        if found less results than min_results or more than max_results
    """
    if min_results < 0:
        raise ValueError("min_results must be greater than 0")
    if max_results is not None and max_results < min_results:
        raise ValueError("max_results must be greater or equal to min_results")

    results = _glob.glob(resolve_env(pathname), recursive=True)
    if (len(results) < min_results
            or (max_results is not None and len(results) > max_results)):
        raise FileMatchError.build(pathname, min_results, max_results,
                                   len(results))

    logging.info("File match %s produced %d results", pathname, len(results))
    return results


def iglob(pathname, *, min_results=0, max_results=None):
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
    for result in _glob.iglob(resolve_env(pathname), recursive=True):
        count += 1
        if max_results is not None and count > max_results:
            raise FileMatchError.build(pathname, min_results, max_results,
                                       count, or_more=True)
        yield result

    if count < min_results:
        raise FileMatchError.build(pathname, min_results, max_results, count)

    logging.info("File match %s produced %d results", pathname, count)
