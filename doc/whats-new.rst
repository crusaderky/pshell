.. currentmodule:: pshell

What's New
==========

.. _whats-new.1.2.0:

v1.2.0 (Unreleased)
-------------------


.. _whats-new.1.1.0:

v1.1.0 (2018-11-19)
-------------------

- Many bugfixes for Windows. Removed bash dependency in Windows;
  commands run in cmd by default.
- Breaking API change: changed ``kill_procs(procs)`` to ``kill(*procs)``
- :func:`~pshell.kill` now accepts integer PIDs in addition to
  :class:`psutil.Process` objects
- New function :func:`~pshell.killall`
- New ``ignore_readonly`` parameter for :func:`~pshell.remove`


.. _whats-new.1.0.0:

v1.0.0 (2018-10-11)
-------------------

Fork from Legal & General's landg.bash.

- Broken down module and unit tests into smaller bits
- Replaced nosetests with py.test
- Added support for Ubuntu and Windows
- CI tests for Linux (Python 3.5, 3.6, 3.7) and Windows (Python 3.6)

API changes:

- Merged ``gzip.open`` into :func:`~pshell.open`.
  Added support for bzip2 and lzma compression.
- Changed parameters of :func:`~pshell.concatente`.
  By default, the output file is deleted if it already exists.