#########################
Autosubmit databases
#########################

Introduction
------------

Autosubmit stores information about its experiments and workflows in SQLite databases and as serialized Python objects (pickle files). These are distributed through the local filesystem, where Autosubmit is installed and runs.

There is one central database that supports the core functionality of experiments in Autosubmit. There are other auxiliary databases consumed by Autosubmit and the Autosubmit API, that store finer-grained experiment information.

The name and location of the central database are defined in the .autosubmitrc config file while the other auxiliary DBs have a predefined name. There are also log files with important information about experiment execution and some other relevant information such as experiment job statuses, timestamps, error messages among other things inside these files.

.. figure:: fig/dbs-highlevel.png
   :name: simple
   :width: 100%
   :align: center
   :alt: High level view of the Autosubmit storage system

Core databases
---------------

* Autosubmit's main database: The default name is autosubmit.db, but the name and location can be customized in ``.autosubmitrc``. Written and read by Autosubmit.
* as_times.db: Used by the Autosubmit API. This database is deprecated since Autosubmit version ``3.x``. It is currently being kept for backward compatibility. Written and read by worker running periodically.

Auxiliary databases
--------------------

These databases complement the Core database previously described for different purposes, some of them are centralized in the ``$AS_METADATA_FOLDER`` directory (defined in the ``.autosubmitrc`` config file) while others are present inside each experiment folder:
Databases present in ``$AS_METADATA_FOLDER``:

* ``/graph/graph_data_xxxx.db``: used by the GUI to optimize the generation of the graph visualization. Populated by a worker running periodically.
* ``/structures/structure_xxxx.db``: experiment dependencies stored as an edge list. Used in the GUI and populated by a worker running periodically.
* ``/data/job_data_xxxx.db``: Stores incremental historical job data information for a given experiment and also some other metrics, filled by Autosubmit during the job handling, there is one per experiment.
* ``/test/status.db``: Stores status of the partition where all Autosubmit DBs and experiment files are stored, populated by a worker running periodically.

Note that ``xxxx`` is the ID of a given experiment, and also that the root path (``$AS_METADATA_FOLDER``) is determined by the configuration defined in ``.autosubmitrc`` config file, under the path defined there, the folder mentioned above will be created.
Databases in each experiment folder:

* ``job_packages_xxxx.db``: Stores the wrappers defined in the experiment, if no wrapper is defined then it may not exist or be empty.
* ``structure_xxxx.db``: Now deprecated, present in older experiments, same structure and purpose as the one described in the previous section.

Other files
-----------

Python Pickle files (.pkl): it has the defined job list of the experiment with state information of all of them. So in the event of a crash or the user stops the experiment, Autosubmit can resume from the last valid state stored in this file.
Update lists: to change the status of experiment jobs without stopping Autosubmit, it is a text file.

These files are present in the experiment folder.