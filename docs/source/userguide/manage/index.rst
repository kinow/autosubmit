Manage Experiments
===================

How to clean the experiment
---------------------------

This procedure allows you to save space after finalising an experiment.
You must execute:
::

    autosubmit clean EXPID


Options:
::

    usage: autosubmit clean [-h] [-pr] [-p] [-s] expid

      expid           experiment identifier

      -h, --help      show this help message and exit
      -pr, --project  clean project
      -p, --plot      clean plot, only 2 last will remain
      -s, --stats     clean stats, only last will remain

* The -p and -s flag are used to clean our experiment ``plot`` folder to save disk space. Only the two latest plots will be kept. Older plots will be removed.

Example:
::

    autosubmit clean cxxx -p

* The -pr flag is used to clean our experiment ``proj`` locally in order to save space (it could be particularly big).

.. caution:: Bear in mind that if you have not synchronized your experiment project folder with the information available on the remote repository (i.e.: commit and push any changes we may have), or in case new files are found, the clean procedure will be failing although you specify the -pr option.

Example:
::

    autosubmit clean cxxx -pr

A bare copy (which occupies less space on disk) will be automatically made.

.. hint:: That bare clone can be always reconverted in a working clone if we want to run again the experiment by using ``git clone bare_clone original_clone``.

.. note:: In addition, every time you run this command with -pr option, it will check the commit unique identifier for local working tree existing on the ``proj`` directory.
    In case that commit identifier exists, clean will register it to the ``expdef_cxxx.yml`` file.

.. _archive:

How to archive an experiment
----------------------------

To archive the experiment, use the command:
::

    autosubmit archive EXPID

*EXPID* is the experiment identifier.

.. warning:: this command calls implicitly the clean command. Check clean command documentation.

.. warning:: experiment will be unusable after archiving. If you want to use it, you will need to call first the
    unarchive command


Options:
::

    usage: autosubmit archive [-h] expid

      expid                 experiment identifier

      -h, --help            show this help message and exit


Example:
::

    autosubmit archive cxxx

.. hint:: Archived experiment will be stored as a tar.gz file on a folder named after the year of the last
    COMPLETED file date. If not COMPLETED file is present, it will be stored in the folder matching the
    date at the time the archive command was run.

How to unarchive an experiment
------------------------------

To unarchive an experiment, use the command:
::

    autosubmit unarchive EXPID

*EXPID* is the experiment identifier.

Options:
::

    usage: autosubmit unarchive [-h] expid

      expid                 experiment identifier

      -h, --help            show this help message and exit


Example:
::

    autosubmit unarchive cxxx

How to delete the experiment
----------------------------

To delete the experiment, use the command:
::

    autosubmit delete EXPID

*EXPID* is the experiment identifier.

.. warning:: DO NOT USE THIS COMMAND IF YOU ARE NOT SURE !
    It deletes the experiment from database and experiment’s folder.

Options:
::

    usage: autosubmit delete [-h] [-f] expid

      expid                 experiment identifier

      -h, --help            show this help message and exit
      -f, --force  deletes experiment without confirmation


Example:
::

    autosubmit delete cxxx

.. warning:: Be careful ! force option does not ask for your confirmation.

How to migrate an experiment
----------------------------

To migrate an experiment from one user to another, you need to add two parameters for each platform in the platforms configuration file:

 * USER_TO: <target_user> # Mandatory
 * TEMP_DIR: <hpc_temporary_directory> # Mandatory, can be left empty if there are no files on that platform
 * SAME_USER: false|true # Default False

 * PROJECT_TO: <project> # Optional, if not specified project will remain the same
 * HOST_TO: <cluster_ip> # Optional, avoid alias if possible, try use direct ip.


.. warning:: The USER_TO must be a different user , in case you want to maintain the same user, put SAME_USER: True.

.. warning:: The temporary directory must be readable by both users (old owner and new owner)
    Example for a RES account to BSC account the tmp folder must have rwx|rwx|--- permissions.
    The temporary directory must be in the same filesystem.

User A, To offer the experiment:
::

    autosubmit migrate --offer expid

Local files will be archived and remote files put in the HPC temporary directory.

User A To only offer the remote files
::

    autosubmit migrate expid --offer --onlyremote

Only remote files will be put in the HPC temporary directory.

.. warning:: Be sure that there is no folder named as the expid before do the pick.
    The old owner might need to remove temporal files and archive.
    To Run the experiment the queue may need to be change.

.. warning:: If onlyremote option is selected, the pickup must maintain the flag otherwise the command will fail.

Now to pick the experiment, the user B, must do
::

    autosubmit migrate --pickup expid

Local files will be unarchived and remote files copied from the temporal location.

To only pick the remote files, the user B, must do
::

    autosubmit migrate --pickup expid --onlyremote

How to refresh the experiment project
-------------------------------------

To refresh the project directory of the experiment, use the command:
::

    autosubmit refresh EXPID

*EXPID* is the experiment identifier.

It checks experiment configuration and copy code from original repository to project directory.

.. warning:: DO NOT USE THIS COMMAND IF YOU ARE NOT SURE !
    Project directory ( <expid>/proj will be overwritten and you may loose local changes.


Options:
::

    usage: autosubmit refresh [-h] expid

      expid                 experiment identifier

      -h, --help            show this help message and exit
      -mc, --model_conf     overwrite model conf file
      -jc, --jobs_conf      overwrite jobs conf file

Example:
::

    autosubmit refresh cxxx

.. _updateDescrip:

How to update the description of your experiment
------------------------------------------------

Use the command:
::

    autosubmit updatedescrip EXPID DESCRIPTION

*EXPID* is the experiment identifier.

*DESCRIPTION* is the new description of your experiment.

Autosubmit will validate the provided data and print the results in the command line.

Example:
::

    autosubmit a29z "Updated using Autosubmit updatedescrip"

.. _setstatus:

How to change the job status
----------------------------

This procedure allows you to modify the status of your jobs.

.. warning:: Beware that Autosubmit must be stopped to use ``setstatus``.
    Otherwise a running instance of Autosubmit, at some point, will overwrite any change you may have done.

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

* The -fl variable receives a list of job names separated by blank spaces: e.g.:
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
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

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

.. note:: A running instance of Autosubmit will check the existence of adobe file after checking already submitted jobs.
    It may take some time, depending on the setting ``SAFETYSLEEPTIME``.



.. warning:: Keep in mind that autosubmit reads the file automatically so it is suggested to create the file in another location like ``/tmp`` or ``/var/tmp`` and then copy/move it to the ``pkl`` folder. Alternatively you can create the file with a different name an rename it when you have finished.