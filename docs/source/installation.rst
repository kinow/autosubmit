############
Installation
############

How to install
===============

The AUTOSUBMIT code is maintained in PyPi, the main source for python packages.

To install autosubmit just execute

::

	pip install autosubmit


Building from source
====================


How to configure
================

After that, execute
::

    autosubmit configure -h

    usage: autosubmit configure [-h] [-db DATABASEPATH] [-lr LOCALROOTPATH]
                                [-qc QUEUESCONFPATH] [-jc JOBSCONFPATH] [-u | -l]

    configure database and path for autosubmit. It can be done at machine, user or
    local level (by default at machine level)

    optional arguments:
      -h, --help            show this help message and exit
      -db DATABASEPATH, --databasepath DATABASEPATH
                            path to database. If not supplied, it will prompt for
                            it
      -lr LOCALROOTPATH, --localrootpath LOCALROOTPATH
                            path to store experiments. If not supplied, it will
                            prompt for it
      -qc QUEUESCONFPATH, --queuesconfpath QUEUESCONFPATH
                            path to queues.conf file to use by default. If not
                            supplied, it will not prompt for it
      -jc JOBSCONFPATH, --jobsconfpath JOBSCONFPATH
                            path to jobs.conf file to use by default. If not
                            supplied, it will not prompt for it
      -u, --user            configure only for this user
      -l, --local           configure only for using Autosubmit from this path

    autosubmit configure -u

and introduce path to experiment storage and database. Folders must exit.

If not database is created on the given path, execute
::

    autosubmit install -h
    usage: autosubmit install [-h]

    install database for autosubmit on the configured folder

    optional arguments:
      -h, --help  show this help message and exit

    autosubmit install

Now you are ready to use autosubmit