How to restart the experiment
=============================

This procedure allows you to restart an experiment. Autosubmit looks for the COMPLETED file for jobs that are considered active (SUBMITTED, QUEUING, RUNNING), UNKNOWN or READY.

.. warning:: You can only restart the experiment if there are not active jobs. You can use -f flag to cancel running jobs automatically.

You must execute:
::

    autosubmit recovery EXPID

*EXPID* is the experiment identifier.

Options:
::

    usage: autosubmit recovery [-h] [-np] [--all] [-s] [-group_by {date,member,chunk,split} -expand -expand_status] expid

        expid       experiment identifier

        -h, --help  show this help message and exit
        -np, --noplot  omit plot
        -f             Allows to perform the recovery even if there are active jobs
        --all        Get all completed files to synchronize pkl
        -s, --save  Save changes to disk
        -group_by {date,member,chunk,split,automatic}
                            criteria to use for grouping jobs
        -expand,              list of dates/members/chunks to expand
        -expand_status,       status(es) to expand
        -nt                   --notransitive
                                        prevents doing the transitive reduction when plotting the workflow
        -nl                   --no_recover_logs
                                        prevents the recovering of log files from remote platforms
        -d                    --detail
                                Shows Job List view in terminal

Example:
::

    autosubmit recovery cxxx -s

In order to understand more the grouping options, which are used for visualization purposes, please check :ref:`grouping`.


.. hint:: When we are satisfied with the results we can use the parameter -s, which will save the change to the pkl file and rename the update file.

The --all flag is used to synchronize all jobs of our experiment locally with the information available on the remote platform
(i.e.: download the COMPLETED files we may not have). In case new files are found, the ``pkl`` will be updated.

Example:
::

    autosubmit recovery cxxx --all -s

How to rerun a part of the experiment
-------------------------------------

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
