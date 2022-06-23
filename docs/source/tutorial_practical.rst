########
Tutorial
########

Quick start guide
=================

First Step: Experiment creation
-------------------------------

To create a new experiment, run the command:
::

    autosubmit expid -dm -H HPCname -d Description

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

