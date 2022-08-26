.. _configuration:

.. toctree::
    :hidden:

    defining_workflows
    develop_a_project
    new_job
    configure_email
    exclusivity_reservation
    new_platform
    wrappers
    update_description
    communication_library
    custom_interpreter
    refresh
    create_members
    check_experiment
    workflow_examples

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

