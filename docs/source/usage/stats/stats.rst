.. _autoStatistics:

How to monitor job statistics
=============================
The following command could be adopted to generate the plots for visualizing the jobs statistics of the experiment at any instance:
::

    autosubmit stats EXPID

*EXPID* is the experiment identifier.

Options:
::

    usage: autosubmit stats [-h] [-ft] [-fp] [-o {pdf,png,ps,svg}] expid

      expid                 experiment identifier

      -h, --help            show this help message and exit
      -ft FILTER_TYPE, --filter_type FILTER_TYPE
                            Select the job type to filter the list of jobs
      -fp FILTER_PERIOD, --filter_period FILTER_PERIOD
                            Select the period of time to filter the jobs
                            from current time to the past in number of hours back
      -o {pdf,png,ps,svg}, --output {pdf,png,ps,svg}
                            type of output for generated plot
      --hide,               hide the plot
      -nt                   --notransitive
                                prevents doing the transitive reduction when plotting the workflow

Example:
::

    autosubmit stats cxxx

The location where user can find the generated plots with date and timestamp can be found below:

::

    <experiments_directory>/cxxx/plot/cxxx_statistics_<date>_<time>.pdf


How to add your particular statistics
=====================================
Although Autosubmit saves several statistics about your experiment, as the queueing time for each job, how many failures per job, etc.
The user also might be interested in adding his particular statistics to the Autosubmit stats report (```autosubmit stats EXPID```).
The allowed format for this feature is the same as the Autosubmit configuration files: INI style. For example:
::

    [COUPLING]
    LOAD_BALANCE = 0.44
    RECOMMEDED_PROCS_MODEL_A = 522
    RECOMMEDED_PROCS_MODEL_B = 418

The location where user can put this stats is in the file:
::

    <experiments_directory>/cxxx/tmp/cxxx_GENERAL_STATS

.. hint:: If it is not yet created, you can manually create the file: ```expid_GENERAL_STATS``` inside the ```tmp``` folder.

Console output description
==========================

Example:
::

    Period: 2021-04-25 06:43:00 ~ 2021-05-07 18:43:00
    Submitted (#): 37
    Run  (#): 37
    Failed  (#): 3
    Completed (#): 34
    Queueing time (h): 1.61
    Expected consumption real (h): 2.75
    Expected consumption CPU time (h): 3.33
    Consumption real (h): 0.05
    Consumption CPU time (h): 0.06
    Consumption (%): 1.75    

Where:

- Period: Requested time frame
- Submitted: Total number of attempts that reached the SUBMITTED status.
- Run: Total number of attempts that reached the RUNNING status.
- Failed: Total number of FAILED attempts of running a job.
- Completed: Total number of attempts that reached the COMPLETED status.
- Queueing time (h): Sum of the time spent queuing by attempts that reached the COMPLETED status, in hours.
- Expected consumption real (h): Sum of wallclock values for all jobs, in hours.
- Expected consumption CPU time (h): Sum of the products of wallclock value and number of requested processors for each job, in hours.
- Consumption real (h): Sum of the time spent running by all attempts of jobs, in hours.
- Consumption CPU time (h): Sum of the products of the time spent running and number of requested of processors for each job, in hours.
- Consumption (%): Percentage of `Consumption CPU time` relative to `Expected consumption CPU time`.

Diagram output description
==========================

The main `stats` output is a bar diagram. On this diagram, each job presents these values:

- Queued (h): Sum of time spent queuing for COMPLETED attempts, in hours.
- Run (h): Sum of time spent running for COMPLETED attempts, in hours.
- Failed jobs (#): Total number of FAILED attempts.
- Fail Queued (h): Sum of time spent queuing for FAILED attempts, in hours.
- Fail Run (h): Sum of time spent running for FAILED attempts, in hours.
- Max wallclock (h): Maximum wallclock value for all jobs in the plot.

Notice that the left scale of the diagram measures the time in hours, and the right scale measures the number of attempts.