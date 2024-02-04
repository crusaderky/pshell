Development Guidelines
======================

Install
-------

1. Clone this repository with git:

   .. code-block:: bash

      git clone git@github.com:crusaderky/pshell.git
      cd pshell

2. Install Python (OS-dependent)
3. .. code-block:: bash
   
      pip install -r requirements.txt

To keep a fork in sync with the upstream source:

.. code-block:: bash

   cd pshell
   git fetch -a upstream
   git checkout main
   git pull upstream main
   git push origin main

Test
----

Test using ``py.test``:

.. code-block:: bash

   py.test pshell

Code Formatting
---------------

pshell uses several code linters (ruff, black, mypy), which are enforced by CI.
Developers should run them locally before they submit a PR, through the single command

.. code-block:: bash

    pre-commit run --all-files

This makes sure that linter versions and options are aligned for all developers.

Optionally, you may wish to setup the `pre-commit hooks <https://pre-commit.com/>`_ to
run automatically when you make a git commit. This can be done by running:

.. code-block:: bash

   pre-commit install

from the root of the pshell repository. Now the code linters will be run each time
you commit changes. You can skip these checks with ``git commit --no-verify`` or with
the short version ``git commit -n``.
