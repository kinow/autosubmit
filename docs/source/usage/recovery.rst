.. _restart:

How to restart the experiment
=============================

This procedure allows you to restart an experiment.

You must execute:
::

    autosubmit recovery EXPID

*EXPID* is the experiment identifier.

Options:
::

    usage: autosubmit recovery [-h] [-np] [-all] [-s] [-group_by {date,member,chunk,split} -expand -expand_status] expid

        expid       experiment identifier

        -h, --help  show this help message and exit
        -np, --noplot  omit plot
        -all        Get all completed files to synchronize pkl
        -s, --save  Save changes to disk
        -group_by {date,member,chunk,split,automatic}
                            criteria to use for grouping jobs
        -expand,              list of dates/members/chunks to expand
        -expand_status,       status(es) to expand

Example:
::

    autosubmit recovery cxxx -s

In order to understand more the grouping options, which are used for visualization purposes, please check :ref:`grouping`.


.. hint:: When we are satisfied with the results we can use the parameter -s, which will save the change to the pkl file and rename the update file.

The -all flag is used to synchronize all jobs of our experiment locally with the information available on the remote platform
(i.e.: download the COMPLETED files we may not have). In case new files are found, the ``pkl`` will be updated.

Example:
::

    autosubmit recovery cxxx -all -s