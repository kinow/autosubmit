########
Tutorial
########

Quick start guide
=================

First Step: Experiment creation
-------------------------------

To create a new experiment, run the command:
::

	autosubmit expid –H HPCname –d Description

*HPCname* is the name of the main HPC platform for the experiment: it will be the default platform for the tasks.
*Description* is a brief experiment description.

This command assigns a unique four character identifier (``xxxx``, names starting from a letter, the other three characters) to the experiment and creates a new folder in experiments repository.

Examples:
::

	autosubmit expid --HPC ithaca --description "experiment is about..."

.. caution:: The *HPCname*, e.g. ithaca, must be defined in the platforms configuration.
    See next section :ref:`confexp`.

::

	autosubmit expid --copy a000 --HPC ithaca -d "experiment is about..."

.. warning:: You can only copy experiments created with Autosubmit 3.0 or above.

.. _confexp:

Second Step: Experiment configuration
-------------------------------------

To configure the experiment, edit ``expdef_cxxx.conf``, ``jobs_cxxx.conf`` and ``platforms_cxxx.conf`` in the ``conf`` folder of the experiment.

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

Examples:
::

	vi <experiments_directory>/cxxx/conf/expdef_cxxx.conf

		# Supply the list of members. LIST = fc0 fc1 fc2 fc3 fc4
		MEMBERS = fc0 fc1 fc2

::

	vi <experiments_directory>/cxxx/conf/jobs_cxxx.conf

		[JOBNAME]
		# Script to execute. If not specified, job will be omited from workflow.
		# Path relative to the project directory
		FILE = scripts/run.sh

You may want to configure Autosubmit parameters for the experiment. Just edit ``autosubmit_cxxx.conf``.

*expdef_cxxx.conf* contains:
    - Maximum number of jobs to be waiting in the HPC queue.
    - Maximum number of jobs to be running at the same time at the HPC.
    - Time (seconds) between connections to the HPC queue scheduler to poll already submitted jobs status.
    - Number of retrials if a job fails.

Example:
::

    vi <experiments_directory>/cxxx/conf/autosubmit_cxxx.conf

        # Maximum number of jobs to be running at the same time at the HPC
        # Default = 6
        TOTALJOBS = 10

Then, Autosubmit *create* command uses the ``expdef_cxxx.conf`` and generates the experiment:
::

	autosubmit create cxxx

*cxxx* is the name of the experiment.

In the process of creating the new experiment a plot has been created.

It can be found in ``<experiments_directory>/cxxx/plot/``

Third Step: Experiment run
--------------------------

After filling the experiment configuration and create, user can go into ``proj`` which has a copy of the model.

A short reference on how to prepare the experiment project is detailed in the following section of this documentation:

:doc:`project`

The experiment project contains the scripts specified in ``jobs_xxxx.conf`` and a copy of model source code and data specified in ``expdef_xxxx.conf``.

To configure experiment project parameters for the experiment, edit ``proj_cxxx.conf``.

*proj_cxxx.conf* contains:
    - The project dependant experiment variables that Autosubmit will substitute in the scripts to be run.

Example:
::

	vi <experiments_directory>/cxxx/conf/prof_cxxx.conf

		# Number of scales for SPPT [Default: set 3]. NUMERIC = 1, 2, 3
		NS_SPPT = 2

Launch Autosubmit *run* in background and with ``nohup`` (continue running although the user who launched the process logs out).
::

	nohup autosubmit run cxxx &

Fourth Step: Experiment monitor
-------------------------------

The following procedure could be adopted to generate the plots for visualizing the status of the experiment at any instance.
With this command we can generate new plots to check which is the status of the experiment. Different job status are represented with different colors.

::

	autosubmit monitor  cxxx

The location where user can find the generated plots with date and timestamp can be found below:

::

	<experiments_directory>/cxxx/plot/cxxx_<date>_<time>.pdf
