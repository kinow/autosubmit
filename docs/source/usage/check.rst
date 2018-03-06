How to check the experiment configuration
=========================================
To check the configuration of the experiment, use the command:
::

    autosubmit check EXPID

*EXPID* is the experiment identifier.

It checks experiment configuration and warns about any detected error or inconsistency.

Options:
::

    usage: autosubmit check [-h] expid

      expid                 experiment identifier

      -h, --help            show this help message and exit

Example:
::

    autosubmit check cxxx
