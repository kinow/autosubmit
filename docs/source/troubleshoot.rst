###############
Troubleshooting
###############

How to change the job status stopping autosubmit
================================================

This procedure allows you to modify the status of your jobs.

.. warning:: Beware that Autosubmit must be stopped to use ``setstatus``.

You must execute:
::

	autosubmit setstatus EXPID -f fs STATUS_ORIGINAL -t STATUS_FINAL -s

*EXPID* is the experiment identifier.
*STATUS_ORIGINAL* is the original status to filter the list of jobs.
*STATUS_FINAL* the desired target status.

Options:
::

    usage: autosubmit setstatus [-h] [-s] -t
        {READY,COMPLETED,WAITING,SUSPENDED,FAILED,UNKNOWN,QUEUING,RUNNING}
        (-l LIST
        | -fc FILTER_CHUNKS
        | -fs {Any,READY,COMPLETED,WAITING,SUSPENDED,FAILED,UNKNOWN}
        | -ft FILTER_TYPE)
        expid

    expid                 experiment identifier
    -h, --help            show this help message and exit
    -s, --save            Save changes to disk
    -t {READY,COMPLETED,WAITING,SUSPENDED,FAILED,UNKNOWN},
                --status_final {READY,COMPLETED,WAITING,SUSPENDED,FAILED,UNKNOWN}
                            Supply the target status
        -l LIST, --list LIST  Supply the list of job names to be changed. Default =
                            "Any". LIST = "b037_20101101_fc3_21_sim
                            b037_20111101_fc4_26_sim"
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

    autosubmit setstatus i05m -f -fs UNKNOWN -t READY -s
    autosubmit setstatus i05m -f -fs FAILED -t READY -s

This script has three mandatory arguments.

The first with which we must specify the experiment id,
the -t with which we must specify the target status of the jobs we want to change to
::

    {READY,COMPLETED,WAITING,SUSPENDED,FAILED,UNKNOWN}


The third argument has two alternatives, the -l and -f with which we can apply a filter for the jobs we want to change.

The -l flag recieves a list of jobnames separated by blank spaces: i.e.:
::

     "b037_20101101_fc3_21_sim b037_20111101_fc4_26_sim"

same as in the previous ``updated_list_<expid>.txt``.
If we supply the key word "Any", all jobs will be changed to the target status.

The -f flag can be used in three modes: the chunk filter, the status filter or the type filter.

* The variable -fc should be a list of individual chunks or ranges of chunks in the following format:

::

    [ 19601101 [ fc0 [1 2 3 4] fc1 [1] ] 19651101 [ fc0 [16-30] ] ]

* The variable -fs can be one of the following status for job:

::

    {Any,READY,COMPLETED,WAITING,SUSPENDED,FAILED,UNKNOWN}

* The variable -ft can be one of the defined types of job.

When we are satisfied with the results we can use the parameter -s, which will save the change to the pkl file.

How to change the job status without stopping autosubmit
========================================================

Create a file in ``<experiments_directory>/<expid>/pkl/`` named ``updated_list_<expid>.txt``.

This file should have two columns: the first one has to be the job_name and the second one the status
::

    (READY,COMPLETED,WAITING,SUSPENDED,FAILED,UNKNOWN).

.. hint:: Keep in mind that autosubmit reads the file automatically so it is suggested to create the file in another location like ``/tmp`` or ``/var/tmp`` and then copy/move it to the ``pkl`` folder. Alternativelly you can create the file with a different name an rename it when you have finished.