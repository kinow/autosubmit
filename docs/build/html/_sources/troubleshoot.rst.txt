###############
Troubleshooting
###############

How to change the job status stopping autosubmit
================================================

This procedure allows you to modify the status of your jobs.

.. warning:: Beware that Autosubmit must be stopped to use ``setstatus``.
    Otherwise a running instance of Autosubmit, at some point, will overwritte any change you may have done.

You must execute:
::

    autosubmit setstatus EXPID -fs STATUS_ORIGINAL -t STATUS_FINAL -s

*EXPID* is the experiment identifier.
*STATUS_ORIGINAL* is the original status to filter by the list of jobs.
*STATUS_FINAL* the desired target status.

Options:
::

    usage: autosubmit setstatus [-h] [-np] [-s] -t
        {READY,COMPLETED,WAITING,SUSPENDED,FAILED,UNKNOWN,QUEUING,RUNNING}
        (-fl LIST
        | -fc FILTER_CHUNKS
        | -fs {Any,READY,COMPLETED,WAITING,SUSPENDED,FAILED,UNKNOWN}
        | -ft FILTER_TYPE)
        [--hide]
        expid

    expid                 experiment identifier
    -h, --help            show this help message and exit
    -np, --noplot         omit plot
    -s, --save            Save changes to disk
    -t {READY,COMPLETED,WAITING,SUSPENDED,FAILED,UNKNOWN},
                --status_final {READY,COMPLETED,WAITING,SUSPENDED,FAILED,UNKNOWN}
                            Supply the target status
        -fl LIST, --list LIST  Supply the list of job names to be changed. Default =
                            "Any". LIST = "cxxx_20101101_fc3_21_sim
                            cxxx_20111101_fc4_26_sim"
        -fc FILTER_CHUNKS, --filter_chunks FILTER_CHUNKS
                            Supply the list of chunks to change the status.
                            Default = "Any". LIST = "[ 19601101 [ fc0 [1 2 3 4]
                            fc1 [1] ] 19651101 [ fc0 [16-30] ] ]"
        -fs {Any,READY,COMPLETED,WAITING,SUSPENDED,FAILED,UNKNOWN},
                --filter_status {Any,READY,COMPLETED,WAITING,SUSPENDED,FAILED,UNKNOWN}
                            Select the original status to filter the list of jobs
        -ft FILTER_TYPE, --filter_type FILTER_TYPE
                            Select the job type to filter the list of jobs

Examples:
::

    autosubmit setstatus cxxx -fl "cxxx_20101101_fc3_21_sim cxxx_20111101_fc4_26_sim" -t READY -s
    autosubmit setstatus cxxx -fc "[ 19601101 [ fc1 [1] ] ]" -t READY -s
    autosubmit setstatus cxxx -fs FAILED -t READY -s
    autosubmit setstatus cxxx -ft TRANSFER -t SUSPENDED -s

This script has two mandatory arguments.

The -t where you must specify the target status of the jobs you want to change to:
::

    {READY,COMPLETED,WAITING,SUSPENDED,FAILED,UNKNOWN}


The second argument has four alternatives, the -fl, -fc, -fs and -ft; with those we can apply a filter for the jobs we want to change:

* The -fl variable recieves a list of jobnames separated by blank spaces: e.g.:
    ::

     "cxxx_20101101_fc3_21_sim cxxx_20111101_fc4_26_sim"

If we supply the key word "Any", all jobs will be changed to the target status.

* The variable -fc should be a list of individual chunks or ranges of chunks in the following format:
    ::

        [ 19601101 [ fc0 [1 2 3 4] fc1 [1] ] 19651101 [ fc0 [16-30] ] ]

* The variable -fs can be the following status for job:
    ::

        {Any,READY,COMPLETED,WAITING,SUSPENDED,FAILED,UNKNOWN}

* The variable -ft can be one of the defined types of job.

.. hint:: When we are satisfied with the results we can use the parameter -s, which will save the change to the pkl file.

How to change the job status without stopping autosubmit
========================================================

    This procedure allows you to modify the status of your jobs without having to stop Autosubmit.

You must create a file in ``<experiments_directory>/<expid>/pkl/`` named:
::

    updated_list_<expid>.txt

Format:

This file should have two columns: the first one has to be the job_name and the second one the status.

Options:
::

    READY,COMPLETED,WAITING,SUSPENDED,FAILED,UNKNOWN

Example:
::

    vi updated_list_cxxx.txt

.. code-block:: ini

    cxxx_20101101_fc3_21_sim    READY
    cxxx_20111101_fc4_26_sim    READY

If Autosubmit finds the above file, it will process it. You can check that the processing was OK at a given date and time,
if you see that the file name has changed to:
::

    update_list_<expid>_<date>_<time>.txt

.. note:: A running instance of Autosubmit will check the existance of avobe file after checking already submitted jobs.
    It may take some time, depending on the setting ``SAFETYSLEEPTIME``.



.. warning:: Keep in mind that autosubmit reads the file automatically so it is suggested to create the file in another location like ``/tmp`` or ``/var/tmp`` and then copy/move it to the ``pkl`` folder. Alternativelly you can create the file with a different name an rename it when you have finished.