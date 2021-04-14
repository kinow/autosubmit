How to rerun a part of the experiment
=====================================

This procedure allows you to create automatically a new pickle with a list of jobs of the experiment to rerun.

Using the ``expdef_<expid>.conf`` the ``create`` command will generate the rerun if the variable RERUN is set to TRUE and a CHUNKLIST is provided.

::

    autosubmit create cxxx

It will read the list of chunks specified in the CHUNKLIST and will generate a new plot.

.. note:: The results are saved in the new pkl ``rerun_job_list.pkl``.

Example:
::

    vi <experiments_directory>/cxxx/conf/expdef_cxxx.conf

.. code-block:: ini

    [...]

    [rerun]
    # Is a rerun or not? [Default: Do set FALSE]. BOOLEAN = TRUE, FALSE
    RERUN = TRUE
    # If RERUN = TRUE then supply the list of chunks to rerun
    # LIST = "[ 19601101 [ fc0 [1 2 3 4] fc1 [1] ] 19651101 [ fc0 [16-30] ] ]"
    CHUNKLIST = [ 19601101 [ fc1 [1] ]

    [...]

Then you are able to start again Autosubmit for the rerun of cxxx 19601101, chunk 1, member 1:

::

    nohup autosubmit run cxxx &