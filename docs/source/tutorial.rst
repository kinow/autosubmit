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

::

	autosubmit expid --copy i001 --HPC ithaca -d "experiment is about..."


Second Step: Experiment configuration
-------------------------------------

To configure the experiment, edit ``expdef_cxxx.conf``, ``jobs_cxxx.conf`` and ``platforms_cxxx.conf`` in the ``conf`` folder of the experiment.

To configure Autosubmit parameters for the experiment, edit ``autosubmit_cxxx.conf``.

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

Then, Autosubmit *create* command uses the ``expdef_cxxx.conf`` and generates the experiment:
::

	autosubmit create cxxx

*cxxx* is the name of the experiment.

In the process of creating the new experiment a plot has been created.

It can be found in ``<experiments_directory>/cxxx/plot/``

Third Step: Experiment run
--------------------------

After filling the experiment configuration and create, user can go into ``proj`` which has a copy of the model.

A complete reference on how to prepare the experiment project is detailed in the following section of this documentation:

:doc:`project`

The experiment project contains the scripts specified in ``jobs_xxxx.conf`` and a copy of model source code and data specified in ``expdef_xxxx.conf``.
To configure experiment project parameters for the experiment, edit ``proj_cxxx.conf``. The project dependant experiment variables, will be substituted in the scripts to be run.

Example:
::

	vi <experiments_directory>/cxxx/conf/prof_cxxx.conf

		# Number of scales for SPPT [Default: set 3]. NUMERIC = 1, 2, 3
		NS_SPPT = 2

Launch Autosubmit *run* in background and with ``nohup`` (continue running although the user who launched the process logs out).
::

	nohup autosubmit run cxxx

Fourth Step: Experiment monitor
-------------------------------

The following procedure could be adopted to generate the plots for visualizing the status of the experiment at any instance.
With this command we can generate new plots to check which is the status of the experiment. Different job status are represented with different colors.

::

	autosubmit monitor  cxxx

The location where user can find the generated plots with date and timestamp can be found below:

::

	<experiments_directory>/cxxx/plot/cxxx_<date>_<time>.pdf
