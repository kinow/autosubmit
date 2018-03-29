How to migrate an experiment
============================
To migrate an experiment from one user to another, you need to add two parameters for each platform in the platforms configuration file:

 * USER_TO = <user>
 * TEMP_DIR = <hpc_temporary_directory>

Then, just run the command:
::

    autosubmit migrate --offer expid


Local files will be archived and remote files put in the HPC temporary directory.

.. warning:: The temporary directory must be readable by both users (old owner and new owner).

Then the new owner will have to run the command:
::

    autosubmit migrate --pickup expid



Local files will be unarchived and remote files copied from the temporal loaction.

.. warning:: The old owner might need to remove temporal files and archive.