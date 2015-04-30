*****
Usage
*****

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

	autosubmit expid -H ithaca -y i001 -d "experiment is about..."

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

.. important:: Before launching Autosubmit check password-less ssh is feasible (*HPCName* is the hostname):

    ``ssh HPCName``

More info on password-less ssh can be found at: http://www.linuxproblem.org/art_9.html

.. caution:: After launching Autosubmit, one must be aware of login expiry limit and policy (if applicable for any HPC) and renew the login access accordingly (by using token/key etc) before expiry.

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


How to stop autosubmit
======================

There are currently two ways of stopping AUTOSUBMIT by sending signals to the processes.
To get the process identifier (PID) you can use the ps command on a shell interpreter/terminal.
To send a signal to a process you can use kill also on a terminal.

More info on signals:
http://en.wikipedia.org/wiki/Signal_(computing)

The two signals have their normal behaviour overwritten and new routines have been coded:

* SIGINT: When notified, AUTOSUBMIT will cancel all submitted (queing, running) jobs and stop.
* SIGQUIT: The routine implemented by this signal does a smart stop. This means that it will wait, to stop itself, until all current submitted jobs are finished. It is highly recommended to resynchronize COMPLETED files before relaunching the experiment.

::

	ps -ef |grep [a]utosubmit
	vguemas  22835     1  1 Sep09 ?        00:45:35 autosubmit run b02h
	vguemas  25783     1  1 Sep09 ?        00:42:25 autosubmit run b02i

To stop immediately experiment b02h:

::

	kill –SIGINT 22835

How to restart
==============

This procedure allows you to modify the job list.
You must execute 

::

	python recovery.py -h

to read help. This script has a mandatory argument  with which we can specify the experiment id.

The -g flag is used to synchronize our experiment locally with the information available on the remote platform (i.e.: download the COMPLETED files we may not have). In case new files are found, the pkl will be updated although we do not specify the -s options, as the information provided is reliable.

In addition, every time we run this script, it will check if ``updated_list_<expid>.txt`` exists on the ``pkl`` directory. In case that file exist, it will generate a new plot, without saving the results in the pkl, with the changes specified in the file. 

When we are satisfied with the results we can use the parameter -s, which will save the change to the pkl file and rename the update file.

How to rerun/extend experiment
==============================

This procedure allows you to create automatically a new pickle with a list of jobs to rerun or an extension of the experiment.
Using the ``expdef_<expid>.conf`` the "create_exp.py" command will generate the rerun if the variable RERUN is set to TRUE and a CHUNKLIST is provided. 

::

	autosubmit create cxxx

It will read the list of chunks specified in the CHUNKLIST and will generate a new plot, saving the results in the new pkl ``rerun_job_list.pkl``.

Then we are able to start again Autosubmit:

::

	nohup autosubmit run cxxx >& cxxx_02.log &


How to clean an experiment
==========================


This procedure allows you to save space after finalising an experiment.  
You must execute 

::

	autosubmit clean -h


to read help. 

This script has one mandatory argument with which we can specify the experiment id.

* The -p flag is used to clean our experiment ``plot`` folder to save disk space. Only the two latest plots will be kept. Older plots will be removed.
* The -g flag is used to clean our experiment ``git`` clone locally in order to save space (``model`` is particullary big). 

A bare copy (which occupies less space on disk) will be automatically made. That bare clone can be always reconverted in a working clone if we want to run again the experiment by using ``git clone bare_clone original_clone``.

Bear in mind that if we have not synchronized our experiment git folder with the information available on the remote repository (i.e.: commit and push any changes we may have), or in case new files are found, the clean procedure will be failing although we specify the -g option.

In addition, every time we run this script with -g option, it will check the commit SHA for local working tree of
``model``, ``template`` and ``ocean_diagnostics`` existing on the ``git`` directory. In case that commit SHA exist, finalise_exp will register it to the database along with the branch name.