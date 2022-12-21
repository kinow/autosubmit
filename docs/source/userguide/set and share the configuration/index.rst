Configuration details, setup and sharing
========================================

Experiment configuration
------------------------

Since the beginning, Autosubmit has always been composed of five files in the folder ``$expid/conf`` that define the experiment configuration.

However, from Autosubmit 4, the configuration is no longer bound to one specific location. And it is composed of YAML files.

This document will teach you how to set up an experiment configuration using the different available methods and what Autosubmit expects to find in the configuration.

Standard configuration structure
---------------------------------

The following table summarizes what configuration files Autosubmit expects and what parameters you can define.

.. list-table::
    :header-rows: 1
    :widths: 20 80

    * - File
      - Content
    * - ``expdef.yml``
      -
        * It contains the default platform, the one set with -H.
        * Allows changing the start dates, members and chunks.
        * Allows changing the experiment project source ( git, local, svn or dummy)
    * - ``platforms.yml``
      -
        * It contains the list of platforms to use in the experiment.
        * This file must be filled-up with the platform(s) configuration(s).
        * Several platforms can be defined and used in the same experiment.
    * - ``jobs.yml``
      -
        - It contains the tasks' definitions in sections.
        - This file must be filled-up with the tasks' definitions.
        - Several sections can be defined and used in the same experiment.
    * - ``autosubmit.yml``
      -
        - Parameters that control workflow behavior.
        - Parameters that activate extra functionalities.
    * - ``proj.yml``
      -
        - Project-dependent parameters.


It is worth mentioning that for Autosubmit 4, these files are seen as one.

Advanced configuration structure and restrictions
-------------------------------------------------

From Autosubmit4, the configuration structure can be split into multiple locations and different files. This advanced configuration has a priority system in which user-specific parameters override the project-specific parameters, and they overwrite the experiment-specific ones.

Also, this configuration is seen as one, meaning that the overwriting is per parameter, not file.

* You would define the experiment-specific parameters under `$expid/conf`.
* You would define the model-specific parameters inside your git or local repository. So when you push/pull the changes from git, they will be updated automatically.
* You would define your user-specific parameters, for example, platform user, in a different location.

There are a few restrictions:

* `$EXPID/conf/expdef.yml` and `$EXPID/conf/autosubmit.yml` files must exist. The reason is that some parameters need to exist as a pre-step for the merging.

* When the `CONFIG_DIR` parameter is not defined, the user must define it under the `DEFAULT` section, located in `$EXPID/conf/expdef.yml`.

How to create and share the configuration
-------------------------------------------

This section contains examples of creating a standard configuration and an advanced one from a newly made experiment.

Standard Configuration
~~~~~~~~~~~~~~~~~~~~~~

The expid command can generate a sample structure containing all the parameters that Autosubmit needs to work correctly.

.. code-block:: bash

   #Create a new experiment.
   autosubmit expid  -H "LOCAL" -d "Standard configuration."
   # Get the expid from the output. Ex. expid=a000
   cd $autosubmit_experiment_folder/a000
   ls conf
   autosubmit_a01y.yml  expdef_a01y.yml  platforms_a01y.yml
        jobs_a01y.yml    proj_a01y.yml

Sharing a standard Configuration
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The expid command can copy another user's existing expid to work correctly.

.. code-block:: bash

   #Create a new experiment.
   autosubmit expid  --copy a000 -H "LOCAL" -d "Standard configuration. --copy of a000"
   # Get the expid from the output. Ex. expid=a001
   cd $autosubmit_experiment_folder/a001
   ls conf
   autosubmit_a001.yml  expdef_a001.yml  platforms_a001.yml
    jobs_a001.yml    proj_a001.yml

.. warning:: You must share the same Autosubmit experiment database for this to work.

Advanced Configuration
~~~~~~~~~~~~~~~~~~~~~~

The expid command can generate a sample structure containing all the parameters that Autosubmit needs to work, but by default, it doesn't contemplate the advanced configuration.

The advanced configuration is activated when the user sets the `DEFAULT.CUSTOM_CONFIG` parameter inside the `expdef.yml` file.

.. warning: A new flag is in the works to simplify the setup.

.. code-block:: bash

   #Create a new experiment.
   autosubmit expid  -H "LOCAL" -d "Advanced configuration."
   # Get the expid from the output. Ex. expid=a002
   cd $autosubmit_experiment_folder/a002
   ls conf
   autosubmit_a002.yml  expdef_a002.yml    platforms_a002.yml
   jobs_a002.yml    proj_a002.yml

To give a practical example, we will show an example using git. However, using a non-git folder is also possible.

Edit `expdef_a002.yml` and change only the following parameters, leaving the rest untouched.

.. code-block:: yaml

    DEFAULT:
        #ADD, note that %ROOTDIR% is an special AS_PLACEHOLDER that points to the expid folder.
        #Syntax: <model-specific_configuration_folder_path>,<user-file>,<user-file2_path>
        CUSTOM_CONFIG: "%ROOTDIR%/proj/git_project/<path_to_as_conf>,<user_platforms_path>"
    PROJECT:
        #CHANGE
        PROJECT_TYPE: "git"
        #CHANGE  note that custom_config is pointing to the same name as this parameter
        PROJECT_DESTINATION: "git_project"
    GIT:
        #CHANGE
        PROJECT_ORIGIN: "TO_FILL"
        #CHANGE
        PROJECT_BRANCH: "TO_FILL"
        #CHANGE
        PROJECT_COMMIT: "TO_FILL"
        #CHANGE
        PROJECT_SUBMODULES: "TO_FILL"
        #CHANGE
        FETCH_SINGLE_BRANCH: True

.. code-block:: yaml

   # Download the git project
   autosubmit refresh a002

.. warning:: Keep in mind the parameter overwriting mechanism priority, CUSTOM_CONFIG_USER_FILES > CUSTOM_CONFIG_FOLDER > $EXPID/conf

.. warning:: Keep in mind that no parameters are disabled when custom_config is activated, including the jobs definitions.

Advanced configuration - Full dummy example (reproducible)
----------------------------------------------------------

.. code-block:: bash

   #Create a new experiment.
   autosubmit expid  -H "local" -d "Advanced configuration. Using a git project"
   # expid=a04b
   dbeltran@bsces107894: cd ~/autosubmit/a04b
   dbeltran@bsces107894:~/autosubmit/a04b$ ls conf
   autosubmit_a04b.yml  expdef_a04b.yml

.. code-block:: bash

    cat ~/autosubmit/conf/autosubmit_a04b.yml

.. code-block:: yaml

	CONFIG:
  		AUTOSUBMIT_VERSION: 4.0.0

.. code-block:: bash

    cat ~/autosubmit/conf/expdef_a04b.yml

.. code-block:: yaml

    DeFault:
      EXPID: a04b
      HPCARCH: local
      CUSTOM_CONFIG: "%ROOTDIR%/proj/git_project/as_conf,/home/dbeltran/as_user_conf/platforms.yml"
    project:
      PROJECT_TYPE: git
      PROJECT_DESTINATION: 'git_project'
    git:
      PROJECT_ORIGIN: 'https://earth.bsc.es/gitlab/ces/auto-advanced_config_example'
      PROJECT_BRANCH: 'main'
      PROJECT_COMMIT: ''
      PROJECT_SUBMODULES: ''
      FETCH_SINGLE_BRANCH: True

.. code-block:: bash

    # Download the git project to obtain the distributed configuration
    dbeltran@bsces107894: autosubmit refresh a04b
    # Check the downloaded model-configuration
    dbeltran@bsces107894:~/autosubmit/a04b$ ls proj/git_project/as_conf/
    autosubmit.yml  expdef.yml  jobs.yml  platforms.yml

Model configuration is distributed at `git. <https://earth.bsc.es/gitlab/ces/auto-advanced_config_example/-/tree/main/as_conf>`_

.. code-block:: bash

    dbeltran@bsces107894:~/autosubmit/a04b$ cat ~/as_user_conf/platforms.yml

.. code-block:: yaml

    Platforms:
      MARENOSTRUM4:
        USER: bsc32070
        QUEUE: debug
        MAX_WALLCLOCK: "02:00"
      marenostrum_archive:
        USER: bsc32070
      transfer_node:
        USER: bsc32070
      transfer_node_bscearth000:
        USER: dbeltran
      bscearth000:
        USER: dbeltran
      nord3:
        USER: bsc32070
      ecmwf-xc40:
        USER: c3d

.. Note:: The user configuration is not distributed, it is a local file that must be edited by the user.

.. code-block:: yaml

   # Create and run the experiment, since it contains all the info!
   autosubmit create a04b
   autosubmit run a04b

Sharing an advanced configuration
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The expid command can copy another user's existing expid to work correctly.

.. code-block:: bash

   #Create a new experiment.
   autosubmit expid  --copy a002 -H "LOCAL" -d "Advanced configuration. --copy of a002"
   # Get the expid from the output. Ex. expid=a004
   cd $autosubmit_experiment_folder/a004
   ls conf
   autosubmit_a004.yml  expdef_a004.yml  platforms_a004.yml
    jobs_a004.yml    proj_a004.yml

.. warning:: All users must share the same experiment autosubmit.db for this to work. More info at `shared-db <https://autosubmit.readthedocs.io/en/master/installation/index.html#production-environment-installation-shared-filesystem-database>`_

Sharing an experiment configuration across filesystems is possible only by including the same `DEFAULT.CUSTOM_CONFIG` and `GIT.PROJECT_ORIGIN`, `GIT.PROJECT_BRANCH` and `GIT.PROJECT_TAG` inside the expdef.yml file.
