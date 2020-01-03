How to refresh the experiment project
=====================================

To refresh the project directory of the experiment, use the command:
::

    autosubmit refresh EXPID

*EXPID* is the experiment identifier.

It checks experiment configuration and copy code from original repository to project directory.

.. warning:: DO NOT USE THIS COMMAND IF YOU ARE NOT SURE !
    Project directory ( <expid>/proj will be overwritten and you may loose local changes.


Options:
::

    usage: autosubmit refresh [-h] expid

      expid                 experiment identifier

      -h, --help            show this help message and exit
      -mc, --model_conf     overwrite model conf file
      -jc, --jobs_conf      overwrite jobs conf file

Example:
::

    autosubmit refresh cxxx