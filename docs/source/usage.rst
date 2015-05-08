*****
Usage
*****

Command list
============


-expid  Create a new experiment
-create  Create specified experiment workflow
-check  Check configuration for specified experiment
-run  Run specified experiment
-test  Test experiment
-monitor  Plot specified experiment
-stats  Plot statistics for specified experiment
-setstatus  Sets job status for an experiment
-recovery  Recover specified experiment
-clean  Clean specified experiment
-refresh  Refresh project directory for an experiment
-delete  Delete specified experiment
-configure  Configure database and path for autosubmit
-install  Install database for Autosubmit on the configured folder


How to create an experiment
===========================
To create a new experiment, just run the command:
::

	autosubmit expid –H HPCname –d Description

*HPCname* is the name of the main HPC platform for the experiment: it will be the default platform for the tasks.
*Description* is a brief experiment description.

Options:
::

	usage: autosubmit expid [-h] [-y COPY | -dm] -H HPC -d DESCRIPTION

	  -h, --help            show this help message and exit
	  -y COPY, --copy COPY  makes a copy of the specified experiment
	  -dm, --dummy          creates a new experiment with default values, usually for testing
	  -H HPC, --HPC HPC     specifies the HPC to use for the experiment
	  -d DESCRIPTION, --description DESCRIPTION
	                        sets a description for the experiment to store in the database.

Example:
::

	autosubmit expid --HPC ithaca --description "experiment is about..."

How to create a copy of an experiment
=====================================
This option makes a copy of an existing experiment.
It registrates a new unique identifier and copies all configuration files in the new experiment folder:
::

	autosubmit expid –H HPCname -y COPY –d Description

*HPCname* is the name of the main HPC platform for the experiment: it will be the default platform for the tasks.
*COPY* is the experiment identifier to copy from.
*Description* is a brief experiment description.

Example:
::

	autosubmit expid -H ithaca -y cxxx -d "experiment is about..."

.. warning:: You can only copy experiments created with Autosubmit 3.0 or above.

How to create a dummy experiment
================================
This command creates a new experiment with default values, useful for testing:
::

	autosubmit expid –H HPCname -dm –d Description

*HPCname* is the name of the main HPC platform for the experiment: it will be the default platform for the tasks.
*Description* is a brief experiment description.

Example:
::

	autosubmit expid -H ithaca -dm "experiment is about..."

How to configure the experiment
===============================

Edit ``expdef_cxxx.conf``, ``jobs_cxxx.conf`` and ``platforms_cxxx.conf`` in the ``conf`` folder of the experiment.

*expdef_cxxx.conf* contains:
    - Start dates, members and chunks (number and length).
    - Experiment project source: origin (version control system or path)
    - Project configuration file path.

*jobs_cxxx.conf* contains the workflow to be run:
    - Scripts to execute.
    - Dependencies between tasks.
    - Task requirements (processors, wallclock time...).
    - Platform to use.

*platforms_cxxx.conf* contains:
    - HPC, fat-nodes and supporting computers configuration.

.. note:: *platforms_cxxx.conf* is usually provided by technicians, users will only have to change login and accounting options for HPCs.

You may want to configure Autosubmit parameters for the experiment. Just edit ``autosubmit_cxxx.conf``.

*autosubmit_cxxx.conf* contains:
    - Maximum number of jobs to be running at the same time at the HPC.
    - Time (seconds) between connections to the HPC queue scheduler to poll already submitted jobs status.
    - Number of retrials if a job fails.

Then, Autosubmit *create* command uses the ``expdef_cxxx.conf`` and generates the experiment:
After editing the files you can proceed to the experiment workflow creation.
Experiment workflow, which contains all the jobs and its dependencies, will be saved as a *pkl* file:
::

	autosubmit create EXPID

*EXPID* is the experiment identifier.

Options:
::

	usage: autosubmit create [-h] [-np] expid

	  expid          experiment identifier

	  -h, --help     show this help message and exit
	  -np, --noplot  omit plot

Example:
::

	autosubmit create cxxx

More info on pickle can be found at http://docs.python.org/library/pickle.html

How to check the experiment configuration
=========================================
To check the configuration of the experiment, use the command:
::

	autosubmit check EXPID

*EXPID* is the experiment identifier.

It checks experiment configuration and warns about any detected error or inconsistency.

Options:
::

	usage: autosubmit check [-h] expid

	  expid                 experiment identifier

	  -h, --help            show this help message and exit

Example:
::

	autosubmit check cxxx


How to run the experiment
=========================
Launch Autosubmit with the command:
::

	autosubmit run EXPID

*EXPID* is the experiment identifier.

Options:
::

	usage: autosubmit run [-h] expid

	  expid       experiment identifier

	  -h, --help  show this help message and exit

Example:
::

	autosubmit run cxxx

.. hint:: It is recommended to launch it in background and with ``nohup`` (continue running although the user who launched the process logs out).

Example:
::

	nohup autosubmit run cxxx &

.. important:: Before launching Autosubmit check password-less ssh is feasible (*HPCName* is the hostname):

    ``ssh HPCName``

More info on password-less ssh can be found at: http://www.linuxproblem.org/art_9.html

.. caution:: After launching Autosubmit, one must be aware of login expiry limit and policy (if applicable for any HPC) and renew the login access accordingly (by using token/key etc) before expiry.

How to test the experiment
==========================
This method is to conduct a test for a given experiment. It creates a new experiment for a given experiment with a
given number of chunks with a random start date and a random member to be run on a random HPC.

To test the experiment, use the command:
::

	autosubmit test CHUNKS EXPID

*EXPID* is the experiment identifier.
*CHUNKS* is the number of chunks to run in the test.



Options:
::

	usage: autosubmit test [-h] -c CHUNKS [-m MEMBER] [-s STARDATE] [-H HPC] [-b BRANCH] expid

        expid                 experiment identifier

         -h, --help            show this help message and exit
         -c CHUNKS, --chunks CHUNKS
                               chunks to run
         -m MEMBER, --member MEMBER
                               member to run
         -s STARDATE, --stardate STARDATE
                               stardate to run
         -H HPC, --HPC HPC     HPC to run experiment on it
         -b BRANCH, --branch BRANCH
                               branch from git to run (or revision from subversion)

Example:
::

	autosubmit test -c 1 -s 19801101 -m fc0 -H ithaca -b develop cxxx


How to monitor the experiment
=============================
To monitor the status of the experiment, use the command:
::

	autosubmit monitor EXPID

*EXPID* is the experiment identifier.

Options:
::

	usage: autosubmit monitor [-h] [-o {pdf,png,ps,svg}] expid

	  expid                 experiment identifier

	  -h, --help            show this help message and exit
	  -o {pdf,png,ps,svg}, --output {pdf,png,ps,svg}
	                        type of output for generated plot

Example:
::

	autosubmit monitor cxxx

The location where user can find the generated plots with date and timestamp can be found below:

::

	<experiments_directory>/cxxx/plot/cxxx_<date>_<time>.pdf

How to monitor job statistics
=============================
The following command could be adopted to generate the plots for visualizing the jobs statistics of the experiment at any instance:
::

	autosubmit stats EXPID

*EXPID* is the experiment identifier.

Options:
::

	usage: autosubmit stats [-h] [-o {pdf,png,ps,svg}] expid

	  expid                 experiment identifier

	  -h, --help            show this help message and exit
	  -o {pdf,png,ps,svg}, --output {pdf,png,ps,svg}
	                        type of output for generated plot

Example:
::

	autosubmit stats cxxx

The location where user can find the generated plots with date and timestamp can be found below:

::

	<experiments_directory>/cxxx/plot/cxxx_statistics_<date>_<time>.pdf


How to stop the experiment
==========================

You can stop Autosubmit by sending a signal to the process.
To get the process identifier (PID) you can use the ps command on a shell interpreter/terminal.
::

	ps -ef | grep autosubmit
	dmanubens  22835     1  1 May04 ?        00:45:35 autosubmit run cxxy
	dmanubens  25783     1  1 May04 ?        00:42:25 autosubmit run cxxx

To send a signal to a process you can use kill also on a terminal.

To stop immediately experiment cxxx:
::

	kill –9 22835

.. important:: In case you want to restart the experiment, you must follow the
    :ref:`restexp` procedure, explained below, in order to properly resynchronize all completed jobs.

.. _restexp:

How to restart the experiment
=============================

This procedure allows you to restart an experiment.

You must execute:
::

	autosubmit recovery EXPID

*EXPID* is the experiment identifier.

Options:
::

    usage: autosubmit recovery [-h] [-all] [-s] expid

        expid       experiment identifier

        -h, --help  show this help message and exit
        -all        Get all completed files to synchronize pkl
        -s, --save  Save changes to disk

Example:
::

    autosubmit recovery cxxx -s

.. hint:: When we are satisfied with the results we can use the parameter -s, which will save the change to the pkl file and rename the update file.

The -all flag is used to synchronize all jobs of our experiment locally with the information available on the remote platform
(i.e.: download the COMPLETED files we may not have). In case new files are found, the ``pkl`` will be updated.

Example:
::

    autosubmit recovery cxxx -all -s


How to rerun a part of the experiment
=====================================

This procedure allows you to create automatically a new pickle with a list of jobs of the experiment to rerun.

Using the ``expdef_<expid>.conf`` the ``create`` command will generate the rerun if the variable RERUN is set to TRUE and a CHUNKLIST is provided.

::

	autosubmit create cxxx

It will read the list of chunks specified in the CHUNKLIST and will generate a new plot.

.. note:: The results are saved in the new pkl ``rerun_job_list.pkl``.

Example:
::

	vi <experiments_directory>/cxxx/conf/expdef_cxxx.conf

.. code-block:: ini

    [...]

    [rerun]
    # Is a rerun or not? [Default: Do set FALSE]. BOOLEAN = TRUE, FALSE
    RERUN = TRUE
    # If RERUN = TRUE then supply the list of chunks to rerun
    # LIST = "[ 19601101 [ fc0 [1 2 3 4] fc1 [1] ] 19651101 [ fc0 [16-30] ] ]"
    CHUNKLIST = [ 19601101 [ fc1 [1] ]

    [...]

Then you are able to start again Autosubmit for the rerun of cxxx 19601101, chunk 1, member 1:

::

	nohup autosubmit run cxxx &


How to clean the experiment
===========================

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

* The -pr flag is used to clean our experiment ``proj`` locally in order to save space (it could be particullary big).

.. caution:: Bear in mind that if you have not synchronized your experiment project folder with the information available on the remote repository (i.e.: commit and push any changes we may have), or in case new files are found, the clean procedure will be failing although you specify the -pr option.

Example:
::

    autosubmit clean cxxx -pr

A bare copy (which occupies less space on disk) will be automatically made.

.. hint:: That bare clone can be always reconverted in a working clone if we want to run again the experiment by using ``git clone bare_clone original_clone``.

.. note:: In addition, every time you run this command with -pr option, it will check the commit unique identifier for local working tree existing on the ``proj`` directory.
    In case that commit identifier exists, clean will register it to the ``expdef_cxxx.conf`` file.


How to refresh the experiment project
=====================================

To refresh the project directory of the experiment, use the command:
::

	autosubmit refresh EXPID

*EXPID* is the experiment identifier.

It checks experiment configuration and copy code from original repository to project directory.

.. warning:: DO NOT USE THIS COMMAND IF YOU ARE NOT SURE !
    Project directory will be overwritten and you may loose local changes.


Options:
::

	usage: autosubmit refresh [-h] expid

	  expid                 experiment identifier

	  -h, --help            show this help message and exit

Example:
::

	autosubmit refresh cxxx



How to delete the experiment
============================

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