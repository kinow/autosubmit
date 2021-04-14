How to delete the experiment
============================

To delete the experiment, use the command:
::

    autosubmit delete EXPID

*EXPID* is the experiment identifier.

.. warning:: DO NOT USE THIS COMMAND IF YOU ARE NOT SURE !
    It deletes the experiment from database and experiment’s folder.

Options:
::

    usage: autosubmit delete [-h] [-f] expid

      expid                 experiment identifier

      -h, --help            show this help message and exit
      -f, --force  deletes experiment without confirmation


Example:
::

    autosubmit delete cxxx

.. warning:: Be careful ! force option does not ask for your confirmation.
