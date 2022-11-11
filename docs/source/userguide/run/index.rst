Running Experiments
===================

Run an experiment
-------------------

Launch Autosubmit with the command:
::

    autosubmit run EXPID

*EXPID* is the experiment identifier.

Options:
::

    usage: autosubmit run [-h] expid

      expid       experiment identifier
      -nt                   --notransitive
                                prevents doing the transitive reduction when plotting the workflow
      -v                    --update_version
                                update the experiment version to match the actual autosubmit version
      -st                   --start_time
                                Sets the starting time for the experiment. Accepted format: 'yyyy-mm-dd HH:MM:SS' or 'HH:MM:SS' (defaults to current day).
      -sa                   --start_after 
                                Sets a experiment expid that will be tracked for completion. When this experiment is completed, the current instance of Autosubmit run will start.
      -rm                   --run_members
                                Sets a list of members allowed to run. The list must have the format '### ###' where '###' represents the name of the member as set in the conf files.
      -h, --help  show this help message and exit

Example:
::

    autosubmit run cxxx
.. important:: If the autosubmit version is set on autosubmit.conf it must match the actual autosubmit version
.. hint:: It is recommended to launch it in background and with ``nohup`` (continue running although the user who launched the process logs out).

Example:
::

    nohup autosubmit run cxxx &

.. important:: Before launching Autosubmit check password-less ssh is feasible (*HPCName* is the hostname):

.. important:: The host machine has to be able to access HPC's/Clusters via password-less ssh. Make sure that the ssh key is in PEM format `ssh-keygen -t rsa -b 4096 -C "email@email.com" -m PEM`.

    ``ssh HPCName``

More info on password-less ssh can be found at: http://www.linuxproblem.org/art_9.html

.. caution:: After launching Autosubmit, one must be aware of login expiry limit and policy (if applicable for any HPC) and renew the login access accordingly (by using token/key etc) before expiry.

How to run an experiment that was created with another version
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. important:: First of all you have to stop your Autosubmit instance related with the experiment

Once you've already loaded / installed the Autosubmit version do you want:
::

    autosubmit create EXPID
    autosubmit recovery EXPID -s -all
    autosubmit run EXPID -v
    or
    autosubmit updateversion EXPID
    autosubmit run EXPID -v
*EXPID* is the experiment identifier.
The most common problem when you change your Autosubmit version is the apparition of several Python errors.
This is due to how Autosubmit saves internally the data, which can be incompatible between versions.
The steps above represent the process to re-create (1) these internal data structures and to recover (2) the previous status of your experiment.

How to run only selected members
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To run only a subset of selected members you can execute the command:
::

    autosubmit run EXPID -rm MEMBERS

*EXPID* is the experiment identifier, the experiment you want to run.

*MEMBERS* is the selected subset of members. Format `"member1 member2 member2"`, example: `"fc0 fc1 fc2"`.

Then, your experiment will start running jobs belonging to those members only. If the experiment was previously running and autosubmit was stopped when some jobs belonging to other members (not the ones from your input) where running, those jobs will be tracked and finished in the new exclusive run.

Furthermore, if you wish to run a sequence of only members execution; then, instead of running `autosubmit run -rm "member_1"` ... `autosubmit run -rm "member_n"`, you can make a bash file with that sequence and run the bash file. Example:
::

    #!/bin/bash
    autosubmit run EXPID -rm MEMBER_1
    autosubmit run EXPID -rm MEMBER_2
    autosubmit run EXPID -rm MEMBER_3
    ...
    autosubmit run EXPID -rm MEMBER_N

How to start an experiment at a given time
------------------------------------------

To start an experiment at a given time, use the command:
::

    autosubmit run EXPID -st INPUT

*EXPID* is the experiment identifier

*INPUT* is the time when your experiment will start. You can provide two formats:
  * `H:M:S`: For example `15:30:00` will start your experiment at 15:30 in the afternoon of the present day.
  * `yyyy-mm-dd H:M:S`: For example `2021-02-15 15:30:00` will start your experiment at 15:30 in the afternoon on February 15th.

Then, your terminal will show a countdown for your experiment start.

This functionality can be used together with other options supplied by the `run` command.

The `-st` command has a long version `--start_time`.


How to start an experiment after another experiment is finished
---------------------------------------------------------------

To start an experiment after another experiment is finished, use the command:
::

    autosubmit run EXPID -sa EXPIDB

*EXPID* is the experiment identifier, the experiment you want to start.

*EXPIDB* is the experiment identifier of the experiment you are waiting for before your experiment starts.

.. warning:: Both experiments must be using Autosubmit version `3.13.0b` or later.

Then, your terminal will show the current status of the experiment you are waiting for. The status format is `COMPLETED/QUEUING/RUNNING/SUSPENDED/FAILED`.

This functionality can be used together with other options supplied by the `run` command.

The `-sa` command has a long version `--start_after`.

How to prepare an experiment to run in two independent job_list. (Priority jobs, Two-step-run)
----------------------------------------------------------------------------------------------

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

Example
~~~~~~~

Guess the expdef configuration as follow:

.. code-block:: ini

    [experiment]
    DATELIST = 20120101
    MEMBERS = 00[0-1]
    CHUNKSIZEUNIT = day
    CHUNKSIZE = 1
    NUMCHUNKS = 2
    TWO_STEP_START = a02n_20120101_000_1_REDUCE&COMPILE_DA,SIM;20120101;c[1]

Given this job_list ( jobs_conf has REMOTE_COMPILE(once),DA,SIM,REDUCE)

['a02n_REMOTE_COMPILE', 'a02n_20120101_000_1_SIM', 'a02n_20120101_000_2_SIM', 'a02n_20120101_001_1_SIM', 'a02n_20120101_001_2_SIM', 'a02n_COMPILE_DA', 'a02n_20120101_1_DA', 'a02n_20120101_2_DA', 'a02n_20120101_000_1_REDUCE', 'a02n_20120101_000_2_REDUCE', 'a02n_20120101_001_1_REDUCE', 'a02n_20120101_001_2_REDUCE']

The priority jobs will be ( check TWO_STEP_START from expdef conf):

['a02n_20120101_000_1_SIM', 'a02n_20120101_001_1_SIM', 'a02n_COMPILE_DA', 'a02n_20120101_000_1_REDUCE']



Finally, you can launch Autosubmit *run* in background and with ``nohup`` (continue running although the user who launched the process logs out).
::

    nohup autosubmit run cxxx &

How to stop the experiment
--------------------------

You can stop Autosubmit by sending a signal to the process.
To get the process identifier (PID) you can use the ps command on a shell interpreter/terminal.
::

    ps -ef | grep autosubmit
    dbeltran  22835     1  1 May04 ?        00:45:35 autosubmit run cxxy
    dbeltran  25783     1  1 May04 ?        00:42:25 autosubmit run cxxx

To send a signal to a process you can use kill also on a terminal.

To stop immediately experiment cxxx:
::

    kill -9 22835

.. important:: In case you want to restart the experiment, you must follow the
    :ref:`restart` procedure, explained below, in order to properly resynchronize all completed jobs.