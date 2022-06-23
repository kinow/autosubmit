How to migrate an experiment
============================
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
