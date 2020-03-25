How to archive an experiment
============================

To archive the experiment, use the command:
::

    autosubmit archive EXPID

*EXPID* is the experiment identifier.

.. warning:: this command calls implicitly the clean command. Check clean command documentation.

.. warning:: experiment will be unusable after archiving. If you want to use it, you will need to call first the
    unarchive command


Options:
::

    usage: autosubmit archive [-h] expid

      expid                 experiment identifier

      -h, --help            show this help message and exit


Example:
::

    autosubmit archive cxxx

.. hint:: Archived experiment will be stored as a tar.gz file on a folder named after the year of the last
    COMPLETED file date. If not COMPLETED file is present, it will be stored in the folder matching the
    date at the time the archive command was run.