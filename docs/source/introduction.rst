############
Introduction
############

What is Autosubmit ?
====================

Autosubmit is a python-based tool to create, manage and monitor experiments by using Computing Clusters, HPC's and
Supercomputers remotely via ssh. It has support for experiments running in more than one HPC and for different workflow
configurations.

Autosubmit is currently used at Barcelona Supercomputing Centre (BSC) to run EC-Earth, NEMO and  NMMB air quality model.

Autosubmit has been used to manage models running at supercomputers in IC3, BSC, ECMWF, EPCC, PDC and OLCF.

Autosubmit is now available via *PyPi* package under the terms of *GNU General Public License*.

+----------------------------------------------------------------------+
| Get involved or contact us:                                          |
+==========================+===========================================+
| Autosubmit GitLab:       | https://earth.bsc.es/gitlab/es/autosubmit |
+--------------------------+-------------------------------------------+
| Autosubmit Mailing List: | autosubmit@bsc.es                         |
+--------------------------+-------------------------------------------+

Why is Autosubmit needed ?
==========================

Autosubmit is the only existing tool that satisfies the following requirements from the weather and climate community:

- *Automatisation*: Job submission to machines and dependencies between jobs are managed by Autosubmit. No user intervention is needed.
- *Data provenance*: Assigns unique identifiers for each experiment and stores information about model version, experiment configuration and computing facilities used in the whole process.
- *Failure tolerance*: Automatic retrials and ability to rerun chunks in case of corrupted or missing data.
- *Resource management*: Autosubmit manages supercomputer particularities, allowing users to run their experiments in the available machine without having to adapt the code. Autosubmit also allows to submit tasks from the same experiment to different platforms.


How does Autosubmit work ?
==========================

You can find help about how to use autosubmit and a list of available commands, just executing:
::

    autosubmit -h

Execute autosubmit <command> -h for detailed help for each command:
::

    autosubmit expid -h

Experiment creation
-------------------

To create a new experiment, run the command:
::

    autosubmit expid -H HPCname -d Description

*HPCname* is the name of the main HPC platform for the experiment: it will be the default platform for the tasks.
*Description* is a brief experiment description.

This command assigns a unique four character identifier (``xxxx``, names starting from a letter, the other three characters) to the experiment and creates a new folder in experiments repository with structure shown in Figure :numref:`exp_folder`.

.. figure:: fig1.png
   :name: exp_folder
   :width: 33%
   :align: center
   :alt: experiment folder

   Example of an experiment directory tree.

Experiment configuration
------------------------

To configure the experiment, edit ``expdef_xxxx.conf``, ``jobs_xxxx.conf`` and ``platforms_xxxx.conf`` in the ``conf`` folder of the experiment (see contents in Figure :numref:`exp_config`).

.. figure:: fig2.png
   :name: exp_config
   :width: 50%
   :align: center
   :alt: configuration files

   Configuration files content

After that, you are expected to run the command:
::

    autosubmit create xxxx

This command creates the experiment project in the ``proj`` folder. The experiment project contains the scripts specified in ``jobs_xxxx.conf`` and a copy of model source code and data specified in ``expdef_xxxx.conf``.

Experiment run
--------------

To run the experiment, just execute the command:

::

    autosubmit run xxxx

Autosubmit will start submitting jobs to the relevant platforms (both HPC and supporting computers) by using the scripts specified in ``jobs_xxxx.conf``. Autosubmit will substitute variables present on scripts where handlers appear in *%variable_name%* format. Autosubmit provides variables for *current chunk*, *start date*, *member*, *computer configuration* and more, and also will replace variables form ``proj_xxxx.conf``.

To monitor the status of the experiment, the command:

::

    autosubmit monitor xxxx

is available. This will plot the workflow of the experiment and the current status.

.. figure:: fig3.png
   :width: 70%
   :align: center
   :alt: experiment plot

   Example of monitoring plot for EC-Earth run with Autosubmit for 1 start date, 1 member and 3 chunks.

