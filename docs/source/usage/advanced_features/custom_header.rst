How to set a custom interpreter for your job
============================================

If the remote platform does not implement the interpreter you need, you can customize the ``shebang`` of your job script so it points to the relative path of the interpreter you want.

In the file:

::

    vi <experiments_directory>/cxxx/conf/jobs_cxxx.conf

.. code-block:: ini

    # Example job with all options specified

    ## Job name
    # [JOBNAME]
    ## Script to execute. If not specified, job will be omited from workflow.
    ## Path relative to the project directory
    # FILE =
    ## Platform to execute the job. If not specificied, defaults to HPCARCH in expedf file.
    ## LOCAL is always defined and referes to current machine
    # PLATFORM =
    ## Queue to add the job to. If not specificied, uses PLATFORM default.
    # QUEUE =
    ## Defines dependencies from job as a list of parents jobs separed by spaces.
    ## Dependencies to jobs in previous chunk, member o startdate, use -(DISTANCE)
    # DEPENDENCIES = INI SIM-1 CLEAN-2
    ## Define if jobs runs once, once per stardate, once per member or once per chunk. Options: once, date, member, chunk.
    ## If not specified, defaults to once
    # RUNNING = once
    ## Specifies that job has only to be run after X dates, members or chunk. A job will always be created for the last
    ## If not specified, defaults to 1
    # FREQUENCY = 3
    ## On a job with FREQUENCY > 1, if True, the dependencies are evaluated against all
    ## jobs in the frequency interval, otherwise only evaluate dependencies against current
    ## iteration.
    ## If not specified, defaults to True
    # WAIT = False
    ## Defines if job is only to be executed in reruns. If not specified, defaults to false.
    # RERUN_ONLY = False
    ## Defines jobs needed to be rerun if this job is going to be rerun
    ## Wallclock to be submitted to the HPC queue in format HH:MM
    # WALLCLOCK = 00:05
    ## Processors number to be submitted to the HPC. If not specified, defaults to 1.
    ## Wallclock chunk increase (WALLCLOCK will be increased according to the formula WALLCLOCK + WCHUNKINC * (chunk - 1)). 
    ## Ideal for sequences of jobs that change their expected running time according to the current chunk.
    # WCHUNKINC = 00:01
    # PROCESSORS = 1
    ## Threads number to be submitted to the HPC. If not specified, defaults to 1.
    # THREADS = 1
    ## Tasks number to be submitted to the HPC. If not specified, defaults to empty.
    # TASKS =
    ## Memory requirements for the job in MB
    # MEMORY = 4096
    ##  Number of retrials if a job fails. If not specified, defaults to the value given on experiment's autosubmit.conf
    # RETRIALS = 4
    ##  Allows to put a delay between retries, of retrials if a job fails. If not specified, it will be static
    # The ideal is to use the +(number) approach or plain(number) in case that the hpc platform has little issues or the experiment will run for a short period of time
    # And *(10) in case that the filesystem is having large  delays or the experiment will run for a lot of time.
    # DELAY_RETRY_TIME = 11
    # DELAY_RETRY_TIME = +11 # will wait 11 + number specified
    # DELAY_RETRY_TIME = *11 # will wait 11,110,1110,11110...* by 10 to prevent a too big number
    ## Some jobs can not be checked before running previous jobs. Set this option to false if that is the case
    # CHECK = False
    ## Select the interpreter that will run the job. Options: bash, python, r Default: bash
    # TYPE = bash
    ## Specify the path to the interpreter. If empty, use system default based on job type  . Default: empty
    # EXECUTABLE = /my_python_env/python3

You can give a path to the ``EXECUTABLE`` setting of your job. Autosubmit will replace the ``shebang`` with the path you provided.

Example:

.. code-block:: ini

    [POST]
    FILE = POST.sh
    DEPENDENCIES = SIM
    RUNNING = chunk
    WALLCLOCK = 00:05
    EXECUTABLE = /my_python_env/python3

This job will use the python interpreter located in the relative path ``/my_python_env/python3/``

It is also possible to use variables in the ``EXECUTABLE`` path.

Example:

.. code-block:: ini

    [POST]
    FILE = POST.sh
    DEPENDENCIES = SIM
    RUNNING = chunk
    WALLCLOCK = 00:05
    EXECUTABLE = %PROJDIR%/my_python_env/python3

The result is a ``shebang`` line ``#!/esarchive/autosubmit/my_python_env/python3``.



