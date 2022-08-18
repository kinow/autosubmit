How to rerun a part of the experiment
=====================================

This procedure allows you to create automatically a new pickle with a list of jobs of the experiment to rerun.

Using the ``expdef_<expid>.conf`` the ``create`` command will generate the rerun if the variable RERUN is set to TRUE and a RERUN_JOBLIST is provided.

Additionally, you can have re-run only jobs that won't be include in the default job_list. In order to do that, you have to set RERUN_ONLY in the jobs conf of the corresponding job.

::

    autosubmit create cxxx

It will read the list of jobs specified in the RERUN_JOBLIST and will generate a new plot.

Example:
::

    vi <experiments_directory>/cxxx/conf/expdef_cxxx.conf

.. code-block:: ini

    ...

    [rerun]
    RERUN = TRUE
    RERUN_JOBLIST = RERUN_TEST_INI;SIM[19600101[C:3]],RERUN_TEST_INI_chunks[19600101[C:3]]
    ...

    vi <experiments_directory>/cxxx/conf/jobs_cxxx.conf

.. code-block:: ini

    [PREPROCVAR]
    FILE = templates/04_preproc_var.sh
    RUNNING = chunk
    PROCESSORS = 8

    [RERUN_TEST_INI_chunks]
    FILE = templates/05b_sim.sh
    RUNNING = chunk
    RERUN_ONLY = true

    [RERUN_TEST_INI]
    FILE = templates/05b_sim.sh
    RUNNING = once
    RERUN_ONLY = true

    [SIM]
    DEPENDENCIES = RERUN_TEST_INI RERUN_TEST_INI_chunks PREPROCVAR SIM-1
    RUNNING = chunk
    PROCESSORS = 10

    .. figure:: fig/rerun.png
       :name: rerun_result
       :align: center
       :alt: rerun_result


::

    nohup autosubmit run cxxx &
