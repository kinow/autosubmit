How to create an experiment
===========================
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
It registrates a new unique identifier and copies all configuration files in the new experiment folder:
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

    usage: autosubmit create [-group_by {date,member,chunk,split} -expand -expand_status] [-h] [-np] [-cw] expid

      expid          experiment identifier

      -h, --help     show this help message and exit
      -np, --noplot  omit plot creation
      --hide,        hide the plot
      -group_by {date,member,chunk,split,automatic}
                            criteria to use for grouping jobs
      -expand,              list of dates/members/chunks to expand
      -expand_status,       status(es) to expand
      -nt                   --notransitive
                                prevents doing the transitive reduction when plotting the workflow
      -cw                   --check_wrapper
                                Generate the wrapper in the current workflow
      -d                    --detail
                                Shows Job List view in terminal
      
Example:
::

    autosubmit create cxxx

In order to understand more the grouping options, which are used for visualization purposes, please check :ref:`grouping`.

More info on pickle can be found at http://docs.python.org/library/pickle.html