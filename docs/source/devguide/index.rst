##############################
Developing an EC-Earth Project
##############################

Autosubmit is used at BSC to run EC-Earth. To do that, a git repository has been created that contains the model source
code and the scripts used to run the tasks.

.. figure:: fig3.png
   :width: 70%
   :align: center
   :alt: EC-Earth experiment

   Example of monitoring plot for EC-Earth run with Autosubmit for 1 start date, 1 member and 3 chunks.

The workflow is defined using seven job types, as shown in the figure above. These job types are:

- Local_setup: prepares a patch for model changes and copies it to HPC.
- Remote_setup: creates a model copy and applies the patch to it.
- Ini: prepares model to start the simulation of one member.
- Sim: runs a simulation chunk (usually 1 to 3 months).
- Post: post-process outputs for one simulation chunk.
- Clean: removes unnecessary outputs from the simulated chunk.
- Transfer: transfers post-processed outputs to definitive storage.

Autosubmit can download the project from git, svn and local repositories via the parameter  `PROJECT.PROJECT_TYPE`. When the source is a git one, the user can specify the submodules, commit, branch, and tag.

In addition, the user can also alter the git behaviour and specify  other optimization parameters such as:
 - Fetching one single branch
 - Depth of the submodules.


The different projects contain the shell script to run, for each job type (local setup, remote setup, ini, sim, post, clean and transfer) that are platform independent.
Additionally the user can modify the sources under proj folder.
The executable scripts are created at runtime so the modifications on the sources can be done on the fly.

.. warning:: Autosubmit automatically adds small shell script code blocks in the header and the tailer of your scripts, to control the workflow.
    Please, remove any exit command in the end of your scripts, e.g. ``exit 0``.

.. important:: For a complete reference on how to develop an EC-Earth project, please have a look in the following wiki page: https://earth.bsc.es/wiki/doku.php?id=models:models