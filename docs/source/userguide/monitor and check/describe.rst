How to get details about the experiment
=========================================
To get details about the experiment, use the command:
::

    autosubmit describe EXPID

*EXPID* is the experiment identifier.

It displays information about the experiment. Currently it describes owner,description_date,model,branch and hpc

Options:
::

    usage: autosubmit describe [-h ] expid

      expid                 experiment identifier
      -h, --help            show this help message and exit

Example:
::

    autosubmit describe cxxx
