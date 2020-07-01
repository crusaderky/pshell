.. _installing:

Installation
============

Required dependencies
---------------------

- Python 3.6 or later
- `psutil <https://github.com/giampaolo/psutil>`_ 5.3 or later
- Only on Python 3.6:
  `contextvars backport <https://github.com/MagicStack/contextvars>`_ 2.0 or later

Deployment
----------

- With pip: :command:`pip install pshell`
- With `anaconda <https://www.anaconda.com/>`_:
  :command:`conda install -c conda-forge pshell`

Testing
-------

To run the test suite after installing pshell, first install (via pip or conda)
`py.test <https://pytest.org>`_ and then run :command:`py.test`.
