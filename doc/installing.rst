.. _installing:

Installation
============

Required dependencies
---------------------

- Python 3.5 or later
- `psutil <https://github.com/giampaolo/psutil>`_ 3.2 or later

Additional dependencies for Windows
-----------------------------------

Most of the module is OS-agnostic. However, pshell uses bash to as
its preferential scripting language. In order to execute :func:`~pshell.call`,
:func:`~pshell.check_call` or :func:`~pshell.check_output` with the
``shell=True`` parameter, as well as :func:`~pshell.source`, one needs to have
first installed bash in his %PATH%.

Deployment
----------

- With pip: :command:`pip install pshell`
- With `anaconda <https://www.anaconda.com/>`_:
  :command:`conda install -c conda-forge pshell`

Testing
-------

To run the test suite after installing pshell, first install (via pip or conda)
`py.test <https://pytest.org>`_ and then run :command:`py.test`.
