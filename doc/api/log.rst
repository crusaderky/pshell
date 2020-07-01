Logging
=======
pshell uses :mod:`logging` to record all commands to the stderr or log file.
By default, it uses the **pshell** logger; it can however be set to use an alternative,
possibly context-local, logger.


Setting and retrieving the pshell logger
----------------------------------------
.. autofunction:: pshell.set_global_logger

.. autodata:: pshell.context_logger

:class:`~contextvars.ContextVar`. Context-local logger, for use in multithreaded and
asynchronous code. This is not inherited when creating a new thread.
See :mod:`contextvars` for more information on how context variables propagate.
Set to None to use the global logger instead.

.. autofunction:: pshell.get_logger

Using the pshell logger
-----------------------
.. autofunction:: pshell.log.debug
.. autofunction:: pshell.log.info
.. autofunction:: pshell.log.warning
.. autofunction:: pshell.log.error
.. autofunction:: pshell.log.critical
