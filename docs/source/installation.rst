############
Installation
############

How to install
===============

The Autosubmit code is maintained in *PyPi*, the main source for python packages.

To install autosubmit just execute:
::

	pip install autosubmit


How to configure
================

After installation, you have to configure database and path for Autosubmit.
It can be done at host, user or local level (by default at host level).
Just execute:
::

    autosubmit configure -u

and introduce path to experiment storage and database. Folders must exit.


For installing the database for Autosubmit on the configured folder, when no database is created on the given path, execute:
::

    autosubmit install

Now you are ready to use Autosubmit !
