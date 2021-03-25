########
Prepare an experiment to run in two independent job_list. (Prioritary jobs, Two-step-run)
########

Feature overview and configuration
-----------------

This feature allows to run an experiment in two separated steps without the need of do anything manually.

To achieve this, you will have to use an special parameter called TWO_STEP_START in which you will put the list of the jobs that you want to run in an exclusive mode. These jobs will run until all of them finishes and once it finishes, the rest of the jobs will begun the execution.

It can be activated through TWO_STEP_START and it is set on expdef_a02n.conf, under the [experiment] section.

.. code-block:: ini

    [experiment]
    DATELIST = 20120101 20120201
    MEMBERS = fc00[0-3]
    CHUNKSIZEUNIT = day
    CHUNKSIZE = 1
    NUMCHUNKS = 10
    CHUNKINI =
    CALENDAR = standard
    # To run before the rest of experiment:
    TWO_STEP_START = <job_names&section,dates,member_or_chunk(M/C),chunk_or_member(C/M)>

In order to be easier to use, there are Three  modes for use this feature: job_names and section,dates,member_or_chunk(M/C),chunk_or_member(C/M).

* By using job_names alone, you will need to put all jobs names one by one divided by the char , .
* By using section,dates,member_or_chunk(M/C),chunk_or_member(C/M). You will be able to select multiple jobs at once combining these filters.
* Use both options, job_names and section,dates,member_or_chunk(M/C),chunk_or_member(C/M). You will have to put & between the two modes.

There are 5 fields on TWO_STEP_START, all of them are optional but there are certain limitations:

* **Job_name**: [Independent] List of job names, separated by ',' char. Optional, doesn't depend on any field. Separated from the rest of fields by '&' must be the first field if specified
* **Section**:  [Independent] List of sections, separated by  ',' char. Optional, can be used alone. Separated from the rest of fields by ';'
* **Dates**: [Depends on section] List of dates, separated by ',' char. Optional, but depends on Section field. Separated from the rest of fields by ';'
* **member_or_chunk**: [Depends on Dates(OR)]  List of chunk or member, must start with C or M to indicate the filter type. Jobs are selected by [1,2,3..] or by a range [0-9] Optional, but depends on Dates field. Separated from the rest of fields by ';'
* **chunk_or_member**: [Depends on Dates(OR)]  List of member or chunk, must start with M or C to indicate the filter type. Jobs are selected by [1,2,3..] or by a range [0-9] Optional, but depends on Dates field. Separated from the rest of fields by ';'

Example:
::

    vi <experiments_directory>/cxxx/conf/expdef_cxxx.conf

.. code-block:: ini

    [experiment]
    DATELIST = 20120101 20120201
    MEMBERS = 00[0-3]
    CHUNKSIZEUNIT = day
    CHUNKSIZE = 1
    NUMCHUNKS = 10
    CHUNKINI =
    CALENDAR = standard
    # To run before the rest of experiment:
    TWO_STEP_START = LOCAL_SEND_INITIAL_DA,COMPILE_DA,LOCAL_SETUP,LOCAL_SEND,REMOTE_COMPILE,SIM;20120101;c[1]



Finally, you can launch Autosubmit *run* in background and with ``nohup`` (continue running although the user who launched the process logs out).
::

    nohup autosubmit run cxxx &
