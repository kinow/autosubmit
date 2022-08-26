Manage the experiment
=====================

How to clean the experiment
---------------------------

This procedure allows you to save space after finalising an experiment.
You must execute:
::

    autosubmit clean EXPID


Options:
::

    usage: autosubmit clean [-h] [-pr] [-p] [-s] expid

      expid           experiment identifier

      -h, --help      show this help message and exit
      -pr, --project  clean project
      -p, --plot      clean plot, only 2 last will remain
      -s, --stats     clean stats, only last will remain

* The -p and -s flag are used to clean our experiment ``plot`` folder to save disk space. Only the two latest plots will be kept. Older plots will be removed.

Example:
::

    autosubmit clean cxxx -p

* The -pr flag is used to clean our experiment ``proj`` locally in order to save space (it could be particularly big).

.. caution:: Bear in mind that if you have not synchronized your experiment project folder with the information available on the remote repository (i.e.: commit and push any changes we may have), or in case new files are found, the clean procedure will be failing although you specify the -pr option.

Example:
::

    autosubmit clean cxxx -pr

A bare copy (which occupies less space on disk) will be automatically made.

.. hint:: That bare clone can be always reconverted in a working clone if we want to run again the experiment by using ``git clone bare_clone original_clone``.

.. note:: In addition, every time you run this command with -pr option, it will check the commit unique identifier for local working tree existing on the ``proj`` directory.
    In case that commit identifier exists, clean will register it to the ``expdef_cxxx.conf`` file.

How to archive an experiment
----------------------------

To archive the experiment, use the command:
::

    autosubmit archive EXPID

*EXPID* is the experiment identifier.

.. warning:: this command calls implicitly the clean command. Check clean command documentation.

.. warning:: experiment will be unusable after archiving. If you want to use it, you will need to call first the
    unarchive command


Options:
::

    usage: autosubmit archive [-h] expid

      expid                 experiment identifier

      -h, --help            show this help message and exit


Example:
::

    autosubmit archive cxxx

.. hint:: Archived experiment will be stored as a tar.gz file on a folder named after the year of the last
    COMPLETED file date. If not COMPLETED file is present, it will be stored in the folder matching the
    date at the time the archive command was run.

How to unarchive an experiment
------------------------------

To unarchive an experiment, use the command:
::

    autosubmit unarchive EXPID

*EXPID* is the experiment identifier.

Options:
::

    usage: autosubmit unarchive [-h] expid

      expid                 experiment identifier

      -h, --help            show this help message and exit


Example:
::

    autosubmit unarchive cxxx

How to delete the experiment
----------------------------

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

How to migrate an experiment
----------------------------

To migrate an experiment from one user to another, you need to add two parameters for each platform in the platforms configuration file:

 * USER_TO = <target_user> # Mandatory
 * TEMP_DIR = <hpc_temporary_directory> # Mandatory, can be left empty if there are no files on that platform
 * SAME_USER = false|true # Default False

 * PROJECT_TO = <project> # Optional, if not specified project will remain the same
 * HOST_TO = <cluster_ip> # Optional, avoid alias if possible, try use direct ip.


.. warning:: The USER_TO must be a different user , in case you want to maintain the same user, put SAME_USER = True.

.. warning:: The temporary directory must be readable by both users (old owner and new owner)
    Example for a RES account to BSC account the tmp folder must have rwx|rwx|--- permissions.
    The temporary directory must be in the same filesystem.

User A, To offer the experiment:
::

    autosubmit migrate --offer expid

Local files will be archived and remote files put in the HPC temporary directory.

User A To only offer the remote files
::

    autosubmit migrate expid --offer --onlyremote

Only remote files will be put in the HPC temporary directory.

.. warning:: Be sure that there is no folder named as the expid before do the pick.
    The old owner might need to remove temporal files and archive.
    To Run the experiment the queue may need to be change.

.. warning:: If onlyremote option is selected, the pickup must maintain the flag otherwise the command will fail.

Now to pick the experiment, the user B, must do
::

    autosubmit migrate --pickup expid

Local files will be unarchived and remote files copied from the temporal location.

To only pick the remote files, the user B, must do
::

    autosubmit migrate --pickup expid --onlyremote
