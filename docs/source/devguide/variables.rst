###################
Variables reference
###################

Autosubmit uses a variable substitution system to facilitate the development of the templates. This variables can be
used on the template in the form %VARIABLE_NAME%.

All configuration variables non related to current_job or platform are accesible by calling first to their parents. ex: %PROJECT.PROJECT_TYPE% or %DEFAULT.EXPID%

You can review all variables at any given time by using the command :ref:`report`:

    $ autosubmit report expid -all


Job variables
=============

This variables are relatives to the current job.

- **TASKTYPE**: type of the job, as given on job configuration file.
- **JOBNAME**: current job full name.
- **FAIL_COUNT**: number of failed attempts to run this job.
- **SDATE**: current startdate.
- **MEMBER**: current member.
- **CHUNK**: current chunk.
- **SPLIT**: current split.
- **DELAY**: current delay.
- **DAY_BEFORE**: day before the startdate
- **Chunk_End_IN_DAYS**: chunk's length in days
- **Chunk_START_DATE**: chunk's start date
- **Chunk_START_YEAR**: chunk's start year
- **Chunk_START_MONTH**: chunk's start month
- **Chunk_START_DAY**: chunk's start day
- **Chunk_START_HOUR**: chunk's start hout
- **Chunk_END_DATE**: chunk's end date
- **Chunk_END_YEAR**: chunk's end year
- **Chunk_END_MONTH**: chunk's end month
- **Chunk_END_DAY**: chunk's end day
- **Chunk_END_HOUR**: chunk's end hour
- **PREV**: days since startdate at the chunk's start
- **Chunk_FIRST**: True if the current chunk is the first, false otherwise.
- **Chunk_LAST**: True if the current chunk is the last, false otherwise.
- **NUMPROC**: Number of processors that the job will use.
- **NUMTHREADS**: Number of threads that the job will use.
- **NUMTASKS**: Number of tasks that the job will use.
- **NODES**: Number of nodes that the job will use.
- **HYPERTHREADING**: Detects if hyperthreading is enabled or not.
- **WALLCLOCK**: Number of processors that the job will use.
- **SCRATCH_FREE_SPACE**: Percentage of free space required on the ``scratch``.
- **NOTIFY_ON**: Determine the job statuses you want to be notified.

Platform variables
==================

This variables are relative to the platforms defined on the jobs conf. A full set of the next variables are defined for
each platform defined on the platforms configuration file, substituting {PLATFORM_NAME} for each platform's name. Also, a
suite of variables is defined for the current platform where {PLATFORM_NAME} is substituted by CURRENT.

- **{PLATFORM_NAME}_ARCH**: Platform name
- **{PLATFORM_NAME}_HOST**: Platform url
- **{PLATFORM_NAME}_USER**: Platform user
- **{PLATFORM_NAME}_PROJ**: Platform project
- **{PLATFORM_NAME}_BUDG**: Platform budget
- **{PLATFORM_NAME}_RESERVATION**: You can configure your reservation id for the given platform.
- **{PLATFORM_NAME}_EXCLUSIVITY**: True if you want to request exclusivity nodes.
- **{PLATFORM_NAME}_TYPE**: Platform scheduler type
- **{PLATFORM_NAME}_VERSION**: Platform scheduler version
- **{PLATFORM_NAME}_SCRATCH_DIR**: Platform's scratch folder path
- **{PLATFORM_NAME}_ROOTDIR**: Platform's experiment folder path
- **{PLATFORM_NAME}_CUSTOM_DIRECTIVES**: Platform's custom directives for the resource manager.

.. hint::
    The variables ``_USER``, ``_PROJ`` and ``_BUDG`` has no value on the LOCAL platform.

.. hint::
    Until now, the variables ``_RESERVATION`` and ``_EXCLUSIVITY`` are only available for MN.

It is also defined a suite of variables for the experiment's default platform:

- **HPCARCH**: Default HPC platform name
- **HPCHOST**: Default HPC platform url
- **HPCUSER**: Default HPC platform user
- **HPCPROJ**: Default HPC platform project
- **HPCBUDG**: Default HPC platform budget
- **HPCTYPE**: Default HPC platform scheduler type
- **HPCVERSION**: Default HPC platform scheduler version
- **SCRATCH_DIR**: Default HPC platform scratch folder path
- **HPCROOTDIR**: Default HPC platform experiment's folder path


Project variables
=================

- **NUMMEMBERS**: number of members of the experiment
- **NUMCHUNKS**: number of chunks of the experiment
- **CHUNKSIZE**: size of each chunk
- **CHUNKSIZEUNIT**: unit of the chuk size. Can be hour, day, month or year.
- **CALENDAR**: calendar used for the experiment. Can be standard or noleap.
- **ROOTDIR**: local path to experiment's folder
- **PROJDIR**: local path to experiment's proj folder

Performance Metrics
===================

Currently, these variables apply only to the report function of Autosubmit. See :ref:`report`.

- **SYPD**: Simulated years per day.
- **ASYPD**: Actual simulated years per day.
- **RSYPD**: Raw simulated years per day.
- **CHSY**: Core hours per simulated year.
- **JPSY**: Joules per simulated year.
- **Parallelization**: Number of cores requested for the simulation job.

For more information about these metrics please visit: 

https://earth.bsc.es/gitlab/wuruchi/autosubmitreact/-/wikis/Performance-Metrics.

