How to add a new platform
=========================

.. hint::
    If you are interested in changing the communications library, go to the section below.

To add a new platform, open the <experiments_directory>/cxxx/conf/platforms_cxxx.conf file where cxxx is the experiment
identifier and add this text:

.. code-block:: ini

    [new_platform]
    TYPE = <platform_type>
    HOST = <host_name>
    PROJECT = <project>
    USER = <user>
    SCRATCH = <scratch_dir>


This will create a platform named "new_platform". The options specified are all mandatory:

* TYPE: queue type for the platform. Options supported are PBS, SGE, PS, LSF, ecaccess and SLURM.

* HOST: hostname of the platform

* PROJECT: project for the machine scheduler

* USER: user for the machine scheduler

* SCRATCH_DIR: path to the scratch directory of the machine

* VERSION: determines de version of the platform type

.. warning:: With some platform types, Autosubmit may also need the version, forcing you to add the parameter
    VERSION. These platforms are PBS (options: 10, 11, 12) and ecaccess (options: pbs, loadleveler).


Some platforms may require to run serial jobs in a different queue or platform. To avoid changing the job
configuration, you can specify what platform or queue to use to run serial jobs assigned to this platform:

* SERIAL_PLATFORM: if specified, Autosubmit will run jobs with only one processor in the specified platform.

* SERIAL_QUEUE: if specified, Autosubmit will run jobs with only one processor in the specified queue. Autosubmit
  will ignore this configuration if SERIAL_PLATFORM is provided

There are some other parameters that you may need to specify:

* BUDGET: budget account for the machine scheduler. If omitted, takes the value defined in PROJECT

* ADD_PROJECT_TO_HOST = option to add project name to host. This is required for some HPCs

* QUEUE: if given, Autosubmit will add jobs to the given queue instead of platform's default queue

* TEST_SUITE: if true, autosubmit test command can use this queue as a main queue. Defaults to false

* MAX_WAITING_JOBS: Maximum number of jobs to be queuing or submitted  in this platform.

* TOTAL_JOBS: Maximum number of jobs to be queuing, running or submitted at the same time in this platform.

* CUSTOM_DIRECTIVES: Custom directives for the resource manager of this platform.

Example:

.. code-block:: ini

    [platform]
    TYPE = SGE
    HOST = hostname
    PROJECT = my_project
    ADD_PROJECT_TO_HOST = true
    USER = my_user
    SCRATCH_DIR = /scratch
    TEST_SUITE = True
    CUSTOM_DIRECTIVES = [ "my_directive" ]