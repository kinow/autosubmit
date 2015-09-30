###################
Variables reference
###################

Autosubmit uses a variable substitution system to facilitate the development of the templates. This variables can be
used on the template in the form %VARIABLE_NAME%.

Job variables
=============

This variables are relatives to the current job.

- **TASKTYPE**: type of the job, as given on job configuration file.
- **JOBNAME**: current job full name.
- **FAIL_COUNT**: number of failed attempts to run this job.
- **SDATE**: current startdate.
- **MEMBER**: current member.
- **CHUNK**: current chunk.
- **DAY_BEFORE**:
- **Chunk_End_IN_DAYS**:
- **Chunk_START_DATE**:
- **Chunk_START_YEAR**:
- **Chunk_START_MONTH**:
- **Chunk_START_DAY**:
- **Chunk_START_HOUR**:
- **Chunk_END_DATE**:
- **Chunk_END_YEAR**:
- **Chunk_END_MONTH**:
- **Chunk_END_DAY**:
- **Chunk_END_HOUR**:
- **PREV**:
- **Chunk_FIRST**: True if the current chunk is the first, false otherwise.
- **Chunk_LAST**: True if the current chunk is the last, false otherwise.
- **NUMPROC**: Number of processors that the job will use.
- **NUMTHREADS**: Number of threads that the job will use.
- **NUMTASK**: Number of tasks that the job will use.
- **WALLCLOCK**: Number of processors that the job will use.


Platform variables
==================

This variables are relative to the platoforms defined on the jobs conf. A full set of the next variables are defined for
each platform defined on the platforms configuration file, substituting {PLATFORM_NAME} for each platform's name. Also, a
suite of varables is defined for the current platform where {PLATFORM_NAME} is substituted by CURRENT.

- **{PLATFORM_NAME}_ARCH**:
- **{PLATFORM_NAME}_HOST**:
- **{PLATFORM_NAME}_USER**:
- **{PLATFORM_NAME}_PROJ**:
- **{PLATFORM_NAME}_BUDG**:
- **{PLATFORM_NAME}_TYPE**:
- **{PLATFORM_NAME}_VERSION**:
- **{PLATFORM_NAME}_SCRATCH_DIR**:
- **{PLATFORM_NAME}_ROOTDIR**:

It is also defined a suite of variables for the experiment's default platform:

- **HPCARCH**:
- **HPCHOST**:
- **HPCUSER**:
- **HPCPROJ**:
- **HPCBUDG**:
- **HPCTYPE**:
- **HPCVERSION**:
- **SCRATCH_DIR**:
- **HPCROOTDIR**:


Project variables
=================

- **NUMCHUNKS**: number of chunks of the experiment
- **CHUNKSIZE**: size of each chunk
- **CHUNKSIZEUNIT**: unit of the chuk size. Can be hour, day, month or year.
- **CALENDAR**: calendar used for the experiment. Can be standard or noleap.
- **ROOTDIR**:
- **PROJDIR**:

