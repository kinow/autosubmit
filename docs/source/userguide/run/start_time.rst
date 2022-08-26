How to start an experiment at a given time
==========================================

To start an experiment at a given time, use the command:
::

    autosubmit run EXPID -st INPUT
  
*EXPID* is the experiment identifier

*INPUT* is the time when your experiment will start. You can provide two formats:
  * `H:M:S`: For example `15:30:00` will start your experiment at 15:30 in the afternoon of the present day.
  * `yyyy-mm-dd H:M:S`: For example `2021-02-15 15:30:00` will start your experiment at 15:30 in the afternoon on February 15th.

Then, your terminal will show a countdown for your experiment start.

This functionality can be used together with other options supplied by the `run` command.

The `-st` command has a long version `--start_time`.
