.. _setstatus:

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
    usage: autosubmit setstatus [-h] [-np] [-s] [-t] [-o {pdf,png,ps,svg}] [-fl] [-fc] [-fs] [-ft] [-group_by {date,member,chunk,split} -expand -expand_status] [-cw] expid

        expid                 experiment identifier

        -h, --help            show this help message and exit
        -o {pdf,png,ps,svg}, --output {pdf,png,ps,svg}
                            type of output for generated plot
        -np, --noplot         omit plot
        -s, --save            Save changes to disk
        -t, --status_final    Target status
        -fl FILTER_LIST, --list
                            List of job names to be changed
        -fc FILTER_CHUNK, --filter_chunk
                            List of chunks to be changed
        -fs FILTER_STATUS, --filter_status
                            List of status to be changed
        -ft FILTER_TYPE, --filter_type
                            List of types to be changed
        -ftc FILTER_TYPE_CHUNK --filter_type_chunk
                            Accepts a string with the formula: "[ 19601101 [ fc0 [1 2 3 4] Any [1] ] 19651101 [ fc0 [16 30] ] ],SIM,SIM2"
                            Where SIM, SIM2 are section (job types) names that also accept the keyword "Any" so the changes apply to all sections.
                            Starting Date (19601101) does not accept the keyword "Any", so you must specify the starting dates to be changed.
                            You can also specify date ranges to apply the change to a range on dates.
                            Member names (fc0) accept the keyword "Any", so the chunks ([1 2 3 4]) given will be updated for all members.
                            Chunks must be in the format "[1 2 3 4]" where "1 2 3 4" represent the numbers of the chunks in the member,
                            no range format is allowed.
        -d                    When using the option -ftc and sending this flag, a tree view of the experiment with markers indicating which jobs
                            have been changed will be generated.
        --hide,               hide the plot
        -group_by {date,member,chunk,split,automatic}
                            criteria to use for grouping jobs
        -expand,              list of dates/members/chunks to expand
        -expand_status,       status(es) to expand
        -nt                   --notransitive
                                prevents doing the transitive reduction when plotting the workflow
        -cw                   --check_wrapper
                                Generate the wrapper in the current workflow

Examples:
::

    autosubmit setstatus cxxx -fl "cxxx_20101101_fc3_21_sim cxxx_20111101_fc4_26_sim" -t READY -s
    autosubmit setstatus cxxx -fc "[ 19601101 [ fc1 [1] ] ]" -t READY -s
    autosubmit setstatus cxxx -fs FAILED -t READY -s
    autosubmit setstatus cxxx -ft TRANSFER -t SUSPENDED -s
    autosubmit setstatus cxxx -ftc "[ 19601101 [ fc1 [1] ], SIM" -t SUSPENDED -s

Date (month) range example:
::
    
    autosubmit setstatus cxxx -ftc "[ 1960(1101-1201) [ fc1 [1] ], SIM" -t SUSPENDED -s

This example will result changing the following jobs:
::

    cxxx_19601101_fc1_1_SIM
    cxxx_19601201_fc1_1_SIM

Date (day) range example:
::

    autosubmit setstatus cxxx -ftc "[ 1960(1101-1105) [ fc1 [1] ], SIM" -t SUSPENDED -s

Result:
::
    cxxx_19601101_fc1_1_SIM
    cxxx_19601102_fc1_1_SIM
    cxxx_19601103_fc1_1_SIM
    cxxx_19601104_fc1_1_SIM
    cxxx_19601105_fc1_1_SIM

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

The variable -ftc acts similar to -fc but also accepts the job types. It does not accept chunk ranges e.g. "1-10", but accepts the wildcard "Any" for members and job types. Let's look at some examples.

* Using -ftc to change the chunks "1 2 3 4" of member "fc0" and chunk "1" of member "fc1" for the starting date "19601101", where these changes apply only for the "SIM" jobs:
    ::

        [ 19601101 [ fc0 [1 2 3 4] fc1 [1] ] ],SIM

* Using -ftc to change the chunks "1 2 3 4" of all members for the starting date "19601101", where these changes apply only for the "SIM" jobs:
    ::

        [ 19601101 [ Any [1 2 3 4] ] ],SIM

* Using -ftc to change the chunks "1 2 3 4" of "fc0" members for the starting date "19601101", where these changes apply to all jobs:
    ::

        [ 19601101 [ fc0 [1 2 3 4] ] ],Any

Try the combinations you come up with. Autosubmit will supply with proper feedback when a wrong combination is supplied.

.. hint:: When we are satisfied with the results we can use the parameter -s, which will save the change to the pkl file. In order to understand more the grouping options, which are used for visualization purposes, please check :ref:`grouping`.

.. _setstatusno:

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