############
Installation
############

How to install
==============

The Autosubmit code is maintained in *PyPi*, the main source for python packages.

- Pre-requisties: These packages (bash, python2, sqlite3, git-scm > 1.8.2, subversion) must be available at local host machine. These packages (argparse, dateutil, pyparsing, numpy, pydotplus, matplotlib, paramiko) must be available for python runtime.

.. important:: The host machine has to be able to access HPC's/Clusters via password-less ssh.

To install autosubmit just execute:
::

    pip install autosubmit

or download, unpack and:
::

    python setup.py install

.. hint::
    To check if autosubmit has been installed run ``autosubmit -v.`` This command will print autosubmit's current
    version
.. hint::
    To read autosubmit's readme file, run ``autosubmit readme``
.. hint::
    To see the changelog, use ``autosubmit changelog``
How to configure
================

After installation, you have to configure database and path for Autosubmit.
It can be done at host, user or local level (by default at host level).
If it does not exist, create a repository for experiments: Say for example ``/cfu/autosubmit``

Then follow the confiugre instructions after executing:
::

    autosubmit configure

and introduce path to experiment storage and database. Folders must exit.


For installing the database for Autosubmit on the configured folder, when no database is created on the given path, execute:
::

    autosubmit install

.. danger:: Be careful ! autosubmit install will create a blank database.

Now you are ready to use Autosubmit !
