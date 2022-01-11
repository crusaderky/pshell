pshell: get rid of all bash scripts
===================================
Bash is widely regarded as a very poor choice to write any script longer than
a few lines. No auto-testing or auto-documentation support, bug-prone grammar,
and lack of debugging tools beyond ``echo`` make any substantial bash script
intrinsically fragile and hard to maintain.

Python on the other hand is a very robust language; however some operations
that could be performed in bash with a single line can take a disproportionate
amount of code when written in Python using :mod:`os`, :mod:`shutil`,
:mod:`subprocess`, etc.

**pshell** gets the best of both worlds by providing a unified, robust,
and compact Python API to perform all the tasks that would be traditionally
done through bash scripting.

To clarify: pshell is *not* an interactive shell; however nothing stops you
from using it from your favourite python/ipython/jupyter terminal!

Some of the core features:

- All actions are logged using the :mod:`logging` module. This is invaluable
  for auditing and debugging. It is strongly recommended to initialise the
  logging module and set the loglevel to INFO or DEBUG before invoking pshell.
- All file paths can contain bash-style environment variables, which are
  resolved on the fly. Failure to resolve and environment variable results in an
  :class:`EnvironmentError` being raised.
  You're safe from the dreaded ``rm -rf $MISSPELLED/*``!
- Functions from the core library are wrapped, hardened, polished, and
  occasionally changed to have a saner default behaviour.
- Full :mod:`pathlib` support, also when wrapping standard library functions
  that do not support it, such as :mod:`shutil` and :mod:`glob`.


Quick start
-----------
>>> import logging
>>> import pshell as sh
>>> logging.basicConfig(
...     level=logging.INFO,
...     format='%(asctime)s %(levelname)s [%(filename)s:%(lineno)d] %(message)s')
>>>
>>> with sh.open("hello.txt", "w") as fh:
...     fh.write("Hello world!")
2018-10-06 22:09:06,161 INFO [open.py:70] Opening 'hello.txt' for write
>>> sh.mkdir("somedir")
2018-10-06 22:10:28,969 INFO [file.py:298] Creating directory somedir
>>> sh.copy("hello.txt", "somedir/")
2018-10-06 22:10:37,354 INFO [file.py:152] Copying hello.txt to somedir/

Index
-----

.. toctree::

   installing
   develop
   whats-new


API Reference
-------------

.. toctree::

   api/call
   api/env
   api/file
   api/log
   api/manipulate
   api/open
   api/procs
   api/search


Credits
-------
pshell was initially developed internally since 2014 as ``landg.bash`` by
`Legal & General <http://www.landg.com>`_.
It was renamed and open-sourced in 2018.


License
-------

pshell is available under the open source `Apache License`__.

__ http://www.apache.org/licenses/LICENSE-2.0.html
