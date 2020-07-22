############
Installation
############

How to install
==============

The Autosubmit code is maintained in *PyPi*, the main source for python packages.

- Pre-requisties: These packages (bash, python2, sqlite3, git-scm > 1.8.2, subversion, dialog and GraphViz) must be available at local host machine.

These packages (argparse, python-dateutil, pyparsing, numpy, pydotplus, matplotlib, paramiko,python2-pythondialog and portalocker) must be available for python runtime.

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
In order to use the default settings, just create a directory called `autosubmit` in your home directory before running the configure command.
The experiments will be created in this folder, and the database named `autosubmit.db` in your home directory.

::

    autosubmit configure




For advanced options you can add `--advanced` to the configure command. It will allow you to choose different directories (they must exist) for the experiments and database,
as well as configure SMTP server and an email account in order to use the email notifications feature.


::

    autosubmit configure --advanced


.. hint::
    The ``dialog`` (GUI) library is optional. Otherwise the configuration parameters
    will be prompted (CLI). Use ``autosubmit configure -h`` to see all the allowed options.


For installing the database for Autosubmit on the configured folder, when no database is created on the given path, execute:
::

    autosubmit install

.. danger:: Be careful ! autosubmit install will create a blank database.

Now you are ready to use Autosubmit !
