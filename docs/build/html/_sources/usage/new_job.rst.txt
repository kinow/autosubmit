How to add a new job
====================

To add a new job, open the <experiments_directory>/cxxx/conf/jobs_cxxx.conf file where cxxx is the experiment
identifier and add this text:

.. code-block:: ini

    [new_job]
    FILE = <new_job_template>

This will create a new job named "new_job" that will be executed once at the default platform. This job will user the
template located at <new_job_template> (path is relative to project folder).

This is the minimun job definition and usually is not enough. You usually will need to add some others parameters:

* PLATFORM: allows you to execute the job in a platform of yout choice. It must be defined in the experiment's
  platforms.conf file or to have the value 'LOCAL' that always refer to the machine running Autosubmit

* RUNNING: defines if jobs runs only once or once per stardate, member or chunk. Options are: once, date,
  member, chunk

* DEPENDENCIES: defines dependencies from job as a list of parents jobs separed by spaces. For example, if
  'new_job' has to wait for "old_job" to finish, you must add the line "DEPENDENCIES = old_job". For dependencies to
  jobs running in previous chunks, members or startdates, use -(DISTANCE). For example, for a job "SIM" waiting for
  the previous "SIM" job to finish, you have to add "DEPENDENCIES = SIM-1"

For jobs running in HPC platforms, usually you have to provide information about processors, wallclock times and more
. To do this use:

* WALLCLOCK: wallclock time to be submitted to the HPC queue in format HH:MM

* PROCESSORS: processors number to be submitted to the HPC. If not specified, defaults to 1.

* THREADS:  threads number to be submitted to the HPC. If not specified, defaults to 1.

* TASKS: tasks number to be submitted to the HPC. If not specified, defaults to 1.

* QUEUE: queue to add the job to. If not specificied, uses PLATFORM default.

There are also other, less used features that you can use:

* FREQUENCY: specifies that a job has only to be run after X dates, members or chunk. A job will always be created for
  the last one. If not specified, defaults to 1

* SYNCHRONIZE: specifies that a job with RUNNING=chunk, has to synchronize its dependencies chunks at a 'date' or
  'member' level, which means that the jobs will be unified: one per chunk for all members or dates.
  If not specified, the synchronization is for each chunk of all the experiment.

* RERUN_ONLY: determines if a job is only to be executed in reruns. If not specified, defaults to false.

* RERUN_DEPENDENCIES: defines the jobs to be rerun if this job is going to be rerunned. Syntax is identical to
  the used in DEPENDENCIES

* CUSTOM_DIRECTIVES: Custom directives for the HPC resource manager headers of the platform used for that job.

Example:

.. code-block:: ini

    [SIM]
    FILE = templates/ecearth3/ecearth3.sim
    DEPENDENCIES = INI SIM-1 CLEAN-2
    RUNNING = chunk
    WALLCLOCK = 04:00
    PROCESSORS = 1616
    THREADS = 1
    TASKS = 1