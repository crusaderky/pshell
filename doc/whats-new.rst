.. currentmodule:: pshell

What's New
==========

.. _whats-new.1.2.0:

v1.2.0 (Unreleased)
-------------------

- Added support for Python 3.8; dropped support for Python 3.5
- Increased minimum required version of psutil to 5.0
- Type annotations
- Mandatory flake8, black, isort, and mypy in CI
- Add unitests for kill() around SIGTERM handling (:pull:`6`) (thanks `Jacob Lin`_)
- Use setuptools-scm for versioning
- New function :func:`wait_for_server`


.. _whats-new.1.1.0:

v1.1.0 (2018-11-19)
-------------------

- Many bugfixes for Windows. Removed bash dependency in Windows;
  commands run in cmd by default.
- Breaking API change: changed ``kill_procs(procs)`` to ``kill(*procs)``
- :func:`kill` now accepts integer PIDs in addition to
  :class:`psutil.Process` objects
- New function :func:`killall`
- New ``ignore_readonly`` parameter for :func:`remove`


.. _whats-new.1.0.0:

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