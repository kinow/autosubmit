How to migrate an experiment
============================
To migrate an experiment from one user to another, you need to add two parameters for each platform in the platforms configuration file:

 * USER_TO = <user>
 * TEMP_DIR = <hpc_temporary_directory>
 * PROJECT_TO = <project>
 * HOST_TO = <cluster_ip> (optional)

Then, just run the command:
::

    autosubmit migrate --offer expid


Local files will be archived and remote files put in the HPC temporary directory.

.. warning:: The temporary directory must be readable by both users (old owner and new owner)
    Example for a RES account to BSC account the tmp folder must have rwx|rwx|--- permisions.
    The temporary directory must be in the same filesystem.

Then the new owner will have to run the command:
::

    autosubmit migrate --pickup expid

Local files will be unarchived and remote files copied from the temporal location.

.. warning:: Be sure that there is no folder named as the expid before do the pick.
    The old owner might need to remove temporal files and archive.
    To Run the experiment the queue may need to be change.