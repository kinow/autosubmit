How to check the experiment configuration
=========================================
To check the configuration of the experiment, use the command:
::

    autosubmit check EXPID

*EXPID* is the experiment identifier.

It checks experiment configuration and warns about any detected error or inconsistency.

Options:
::

    usage: autosubmit check [-h -nt] expid

      expid                 experiment identifier
      -nt                   --notransitive
                                prevents doing the transitive reduction when plotting the workflow
      -h, --help            show this help message and exit

Example:
::

    autosubmit check cxxx
