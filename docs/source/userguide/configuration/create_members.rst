How to create and run only selected members
===========================================

Your experiment is defined and correctly configured, but you want to create it only considering some selected members, and also to avoid creating the whole experiment to run only the members you want. Then, you can do it by configuring the setting **RUN_ONLY_MEMBERS** in the file:

::

    vi <experiments_directory>/cxxx/conf/expdef_cxxx.conf

.. code-block:: ini

    [DEFAULT]
    # Experiment identifier
    # No need to change
    EXPID = cxxx
    # HPC name.
    # No need to change
    HPCARCH = ithaca

    [experiment]
    # Supply the list of start dates. Available formats: YYYYMMDD YYYYMMDDhh YYYYMMDDhhmm
    # Also you can use an abbreviated syntax for multiple dates with common parts:
    # 200001[01 15] <=> 20000101 20000115
    # DATELIST = 19600101 19650101 19700101
    # DATELIST = 1960[0101 0201 0301]
    DATELIST = 19900101
    # Supply the list of members. LIST = fc0 fc1 fc2 fc3 fc4
    MEMBERS = fc0
    # Chunk size unit. STRING = hour, day, month, year
    CHUNKSIZEUNIT = month
    # Chunk size. NUMERIC = 4, 6, 12
    CHUNKSIZE = 1
    # Total number of chunks in experiment. NUMERIC = 30, 15, 10
    NUMCHUNKS = 2
    # Calendar used. LIST: standard, noleap
    CALENDAR = standard
    # List of members that can be included in this run. Optional. 
    # RUN_ONLY_MEMBERS = fc0 fc1 fc2 fc3 fc4
    # RUN_ONLY_MEMBERS = fc[0-4]
    RUN_ONLY_MEMBERS = 


  
You can set the **RUN_ONLY_MEMBERS** value as shown in the format examples above it. Then, ``Job List`` generation is performed as usual. However, an extra step is performed that will filter the jobs according to **RUN_ONLY_MEMBERS**. It discards jobs belonging to members not considered in the value provided, and also we discard these jobs from the dependency tree (parents and children). The filtered ``Job List`` is returned. 

The necessary changes have been implemented in the API so you can correctly visualize experiments implementing this new setting in **Autosubmit GUI**.

.. important::
    Wrappers are correctly formed considering the resulting jobs.

