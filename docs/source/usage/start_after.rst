How to start an experiment after another experiment is finished
===============================================================

To start an experiment after another experiment is finished, use the command:
::

    autosubmit run EXPID -sa EXPIDB
  
*EXPID* is the experiment identifier, the experiment you want to start.

*EXPIDB* is the experiment identifier of the experiment you are waiting for before your experiment starts.

.. warning:: Both experiments must be using Autosubmit version `3.13.0b` or later.

Then, your terminal will show the current status of the experiment you are waiting for. The status format is `COMPLETED/QUEUING/RUNNING/SUSPENDED/FAILED`.

This functionality can be used together with other options supplied by the `run` command.

The `-sa` command has a long version `--start_after`.

