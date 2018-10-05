pshell: API to get rid of all bash scripts
==========================================
Facilities for faster bash interaction, aimed to replace
bash scripts. They are mostly wrapped around functions from
os, shutil, and subprocess. The main differences are:

1. All actions are logged using the logging library
2. All paths can contain environment variables
3. All child shell commands are run with errexit, pipefail, and nounset


.. toctree::

   installing
   whats-new

API Reference
-------------

.. toctree::

   api/call
   api/env
   api/file
   api/manipulate
   api/open
   api/procs
   api/search

License
-------

pshell is available under the open source `LGPL License`__.

__ https://www.gnu.org/licenses/lgpl-3.0.en.html
