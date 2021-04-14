How to stop the experiment
==========================

You can stop Autosubmit by sending a signal to the process.
To get the process identifier (PID) you can use the ps command on a shell interpreter/terminal.
::

    ps -ef | grep autosubmit
    dmanubens  22835     1  1 May04 ?        00:45:35 autosubmit run cxxy
    dmanubens  25783     1  1 May04 ?        00:42:25 autosubmit run cxxx

To send a signal to a process you can use kill also on a terminal.

To stop immediately experiment cxxx:
::

    kill -9 22835

.. important:: In case you want to restart the experiment, you must follow the
    :ref:`restart` procedure, explained below, in order to properly resynchronize all completed jobs.

.. _restexp: