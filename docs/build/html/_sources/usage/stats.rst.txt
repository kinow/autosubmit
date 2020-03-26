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
