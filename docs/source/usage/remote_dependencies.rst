############
Remote Dependencies
############

There is also the possibility of setting the option **DEPENDENCIES** to True in the config directive.

This allows more than one package containing simple or wrapped jobs to be submitted at the same time, even when the dependencies between jobs aren't yet satisfied. This is only useful for cases when the job scheduler considers the time a job has been queuing to determine the job's priority (and the scheduler understands the dependencies set between the submitted packages). New packages can be created as long as the total number of jobs are below than the number defined in the **TOTALJOBS** variable.

How to configure
========================

In ``autosubmit_cxxx.conf``, regardless of the how your workflow is configured.

For example:

.. code-block:: ini

    [config]
    EXPID = ....
    AUTOSUBMIT_VERSION = 3.12.1b
    ...
    DEPENDENCIES = TRUE
    MAXWAITINGJOBS = 100
    TOTALJOBS = 100
    ...
