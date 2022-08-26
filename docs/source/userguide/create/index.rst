How to create an experiment
===========================

.. toctree::
    :hidden:
    :titlesonly:

    create_testcase
    test_experiment

To create a new experiment, just run the command:
::

    autosubmit expid -H HPCname -d Description

*HPCname* is the name of the main HPC platform for the experiment: it will be the default platform for the tasks.
*Description* is a brief experiment description.

Options:
::

    usage: autosubmit expid [-h] [-y COPY | -dm] [-p PATH] -H HPC -d DESCRIPTION

        -h, --help            show this help message and exit
        -y COPY, --copy COPY  makes a copy of the specified experiment
        -dm, --dummy          creates a new experiment with default values, usually for testing
        -H HPC, --HPC HPC     specifies the HPC to use for the experiment
        -d DESCRIPTION, --description DESCRIPTION
            sets a description for the experiment to store in the database.
        -c PATH, --config PATH
            if specified, copies config files from a folder
Example:
::

    autosubmit expid --HPC ithaca --description "experiment is about..."

If there is an autosubmitrc or .autosubmitrc file in your home directory (cd ~), you can setup a default file from where the contents of platforms_expid.conf should be copied.

In this autosubmitrc or .autosubmitrc file, include the configuration setting custom_platforms:

Example:
::
    [conf]
    custom_platforms=/home/Earth/user/custom.conf

Where the specified path should be complete, as something you would get when executing pwd, and also include the filename of your custom platforms content.

How to create a copy of an experiment
=====================================
This option makes a copy of an existing experiment.
It registers a new unique identifier and copies all configuration files in the new experiment folder:
::

    autosubmit expid -y COPY -H HPCname -d Description
    autosubmit expid -y COPY -c PATH -H HPCname -d Description

*HPCname* is the name of the main HPC platform for the experiment: it will be the default platform for the tasks.
*COPY* is the experiment identifier to copy from.
*Description* is a brief experiment description.
*CONFIG* is a folder that exists.
Example:
::

    autosubmit expid -y cxxx -H ithaca -d "experiment is about..."
    autosubmit expid -y cxxx -p "/esarchive/autosubmit/genericFiles/conf" -H marenostrum4 -d "experiment is about..."
.. warning:: You can only copy experiments created with Autosubmit 3.0 or above.

If there is an autosubmitrc or .autosubmitrc file in your home directory (cd ~), you can setup a default file from where the contents of platforms_expid.conf should be copied.

In this autosubmitrc or .autosubmitrc file, include the configuration setting custom_platforms:

Example:
::
    [conf]
    custom_platforms=/home/Earth/user/custom.conf

Where the specified path should be complete, as something you would get when executing pwd, and also include the filename of your custom platforms content.

How to create a dummy experiment
================================
This command creates a new experiment with default values, useful for testing:
::

    autosubmit expid -H HPCname -dm -d Description

*HPCname* is the name of the main HPC platform for the experiment: it will be the default platform for the tasks.
*Description* is a brief experiment description.

Example:
::

    autosubmit expid -H ithaca -dm "experiment is about..."