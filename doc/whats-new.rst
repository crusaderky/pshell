.. currentmodule:: pshell

What's New
==========

.. _whats-new.1.1.0:

v1.1.0 (Unreleased)
-------------------


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