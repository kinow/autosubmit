.. _treeRepresentation:

Tree Representation
===================

The Tree Representation offers a structured view of the experiment.

.. figure:: fig_tree_2.png
   :name: experiment_tree
   :width: 100%
   :align: center
   :alt: Experiment Tree 1

   Experiment Tree Representation

The view is organized in groups by date, and data-member. Each group has a folder icon, and next to the icon you can find the progress of the group as completed jobs / total jobs (when all the jobs in a group have been completed, a check symbol will appear), then, an indicator of how many jobs inside that group are **RUNNING**, **QUEUING**, or have **FAILED**. Furthermore, if wrappers exist in the experiment, independent groups will be added for each wrapper that will contain the list of jobs included in the corresponding wrapper, this implies that a job can be repeated: once inside its date-member group and once in its wrapper group.

Inside each group you will find the list of jobs that belong to that group. The jobs are shown followin this format: *job name* + # *job status* + ( + *queuing time* + ) + *running time*. Jobs that belong to a wrapper have also a badge with the code of the wrapper.

When you click on a Job, you can see on the right panel the following information:

- *Initial*: Initial date as in the one used for grouping.
- *Real*: Real date after adding to the initial date the number of chunk units depending on chunk size.
- *Section*: Also known as job type.
- *Member*
- *Chunk*
- *Platform*: HPC Platform.
- *Processord*: Number of processors required by the job.
- *Wallclock*: Time requested by the job.
- *Queue*: Time spent in queue, in minutes.
- *Run*: Time spent running, in minutes.
- *Status*: Job status.
- *Out*: Button that opens a list of jobs that depend on the one selected.
- *In*: Button that opens a list of jobs on which the selected job depends.
- *Wrapper*: If the job belongs to a wrapper, the name of the wrapper will be shown.
- *Code*: Code of the wrapper the job belongs to, for easy searching.
- *out path*: Path to the .out log file.
- *err path*: Path to the .err log file.

If the experiment status is **RUNNING**, you will see a button called **Refresh** at the top right corner. This button will refresh the information of the jobs in the tree if they have changed.

The button **Clear Tree View** will clear the Tree Representation. It is also a good way to refresh the Tree Representation.

At the top left you can find the **Filter text** input box, insert any string and the list will show only those jobs whose description coincides with that string. For example "#COMPLETED" will show only completed jobs, "Wrapped" will show only those jobs that belong to a wrapper, "_fc0_" will show only those jobs that belong to the fc0 member. Press **Clear** to reset the filter. On the right side of this bar, you will see the total number of jobs, and the chunk unit used in the experiment.

