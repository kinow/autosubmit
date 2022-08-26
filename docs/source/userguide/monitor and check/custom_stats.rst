How to add your particular statistics
=====================================
Although Autosubmit saves several statistics about your experiment, as the queueing time for each job, how many failures per job, etc.
The user also might be interested in adding his particular statistics to the Autosubmit stats report (```autosubmit stats EXPID```).
The allowed format for this feature is the same as the Autosubmit configuration files: INI style. For example:
::

    [COUPLING]
    LOAD_BALANCE = 0.44
    RECOMMENDED_PROCS_MODEL_A = 522
    RECOMMENDED_PROCS_MODEL_B = 418

The location where user can put this stats is in the file:
::

    <experiments_directory>/cxxx/tmp/cxxx_GENERAL_STATS

.. hint:: If it is not yet created, you can manually create the file: ```expid_GENERAL_STATS``` inside the ```tmp``` folder.