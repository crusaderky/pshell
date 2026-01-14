.. currentmodule:: pshell

What's New
==========

v1.6.0 (2026-01-14)
-------------------
- All log messages are reported as coming from the user's frames instead of from pshell
- New function :func:`log.inc_stacklevel`


v1.5.0 (2025-12-28)
-------------------
- Audited thread safety of the whole codebase
- Fixed threading race conditions in :func:`source` and :func:`symlink`
- Fixed issue where :func:`remove` would fail to delete directories even with
  ``ignore_readonly=True``
- Added zstandard (zstd) compression support to :func:`open`
  (requires either Python 3.14+ or the ``backports.zstd`` package)
- Added formal support for Python 3.13 and 3.14 (the previous version works fine though)
- Bumped minimum version of psutil from 5.6 to 5.7
- Handle deprecation in psutil 6


v1.4.0 (2024-03-15)
-------------------
- Added formal support for Python 3.11 and 3.12 (the previous version works fine though)
- Bumped minimum version of psutil from 5.4 to 5.6


v1.3.0 (2022-03-26)
-------------------
- Dropped support for Python 3.6 and 3.7
- Added support for Python 3.9 and 3.10
- Bumped minimum version of psutil from 5.3 to 5.4
- Added pre-commit hooks


v1.2.0 (2020-07-01)
-------------------

Code changes
^^^^^^^^^^^^
- Type annotations
- :mod:`pathlib` support
- :doc:`api/log`: Use a custom global or context-local logger.
  The default logger has been changed from the root logger to **pshell**.
- New function :func:`wait_for_server`
- Add unit tests for kill() around SIGTERM handling (thanks `Jacob Lin`_)

Packaging changes
^^^^^^^^^^^^^^^^^
- Added support for Python 3.8; dropped support for Python 3.5
- Increased minimum required version of psutil to 5.3
- Use setuptools-scm for versioning

CI changes
^^^^^^^^^^
- Migrated from conda to pip
- Migrated from Travis+AppVeyor to GitHub Workflows
- Integrated with codecov.io
- Run test suite on MacOS
- Run test suite on Windows with Python 3.6 and 3.7
- Mandatory flake8, black, isort, and mypy


v1.1.0 (2018-11-19)
-------------------

- Many bugfixes for Windows. Removed bash dependency in Windows;
  commands run in cmd by default.
- Breaking API change: changed ``kill_procs(procs)`` to ``kill(*procs)``
- :func:`kill` now accepts integer PIDs in addition to
  :class:`psutil.Process` objects
- New function :func:`killall`
- New ``ignore_readonly`` parameter for :func:`remove`


v1.0.0 (2018-10-11)
-------------------

Fork from Legal & General's landg.bash.

- Broken down module and unit tests into smaller bits
- Replaced nosetests with py.test
- Added support for Ubuntu and Windows
- CI tests for Linux (Python 3.5, 3.6, 3.7) and Windows (Python 3.6)

API changes:

- Merged ``gzip_open`` into :func:`open`.
  Added support for bzip2 and lzma compression.
- Changed parameters of :func:`concatenate`.
  By default, the output file is deleted if it already exists.


.. _`Jacob Lin`: https://github.com/jcclin
