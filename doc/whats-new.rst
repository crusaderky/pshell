.. currentmodule:: pshell

What's New
==========

.. _whats-new.1.2.0:

v1.2.0 (Unreleased)
-------------------

- Mandatory flake8 in CI `Guido Imperiale`_
- Add unitests for kill() around SIGTERM handling (#6) `Jacob Lin`_


.. _whats-new.1.1.0:

v1.1.0 (2018-11-19)
-------------------

- Many bugfixes for Windows. Removed bash dependency in Windows;
  commands run in cmd by default. `Guido Imperiale`_
- Breaking API change: changed ``kill_procs(procs)`` to ``kill(*procs)``
  `Guido Imperiale`_
- :func:`~pshell.kill` now accepts integer PIDs in addition to
  :class:`psutil.Process` objects `Guido Imperiale`_
- New function :func:`~pshell.killall` `Guido Imperiale`_
- New ``ignore_readonly`` parameter for :func:`~pshell.remove`
  `Guido Imperiale`_


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


.. _`Guido Imperiale`: https://github.com/crusaderky
.. _`Jacob Lin`: https://github.com/jcclin