############
Wrappers
############

In order to understand the goal of this feature, please take a look at: https://earth.bsc.es/wiki/lib/exe/fetch.php?media=library:seminars:techniques_to_improve_the_throughput.pptx

At the moment there are 4 types of wrappers that can be used depending on the experiment's workflow:

* Vertical
* Vertical mixed
* Horizontal
* Hybrid (horizontal-vertical and vertical-horizontal approaches)

How to configure
========================

In ``autosubmit_cxxx.conf``, regardless of the wrapper type, you need to make sure that the values of the variables **MAXWAITINGJOBS** and **TOTALJOBS** are increased according to the number of jobs expected to be waiting/running at the same time in your experiment.

For example:

.. code-block:: ini

    [config]
    EXPID = ....
    AUTOSUBMIT_VERSION = 3.12.0b
    ...

    MAXWAITINGJOBS = 100
    TOTALJOBS = 100
    ...

and below the [config] block, add the wrapper directive, indicating the wrapper type:

.. code-block:: ini

    [wrapper]
    TYPE =

You can also specify which job types should be wrapped. This can be done using the **JOBS_IN_WRAPPER** parameter.
It is only required for the vertical-mixed type (in which the specified job types will be wrapped together), so if nothing is specified, all jobs will be wrapped.
By default, jobs of the same type will be wrapped together, as long as the constraints are satisfied.

Number of jobs in a package
**********************

.. code-block:: ini

    [wrapper]
    TYPE = <ANY>
    MIN_WRAPPED = 2
    MAX_WRAPPED = 999


- **MAX_WRAPPED** can be defined in ``jobs_cxxx.conf`` in order to limit the number of jobs wrapped for the corresponding job section
    - If not defined, it considers the **MAX_WRAPPED** defined under [wrapper] in ``autosubmit_cxxx.conf``
        - If **MAX_WRAPPED** is not defined, then **TOTALJOBS** is used by default





Wrapper check time
**********************

It is possible to override the **SAFETYSLEEPTIME** for the wrapper, by using **CHECK_TIME_WRAPPER** and defining a time interval (in seconds) in which the wrapper internal jobs should be checked.

.. important::  Note that the **numbers** shown in this documentation are examples. The actual values must be set according to the specific workflow, as well as the platform configurations.

Vertical wrapper
=======================

The vertical wrapper is more appropriate when there are many sequential jobs. To use it, set TYPE = vertical:

.. code-block:: ini

    [wrapper]
    TYPE = vertical

In order to be able to use the vertical wrapper, in ``platforms_cxxx.conf`` set the maximum wallclock allowed by the platform in use:

.. code-block:: ini

    [marenostrum4]
    ...
    MAX_WALLCLOCK = 72:00

Remember to add to each job the corresponding WALLCLOCK time.

Vertical-mixed wrapper
=======================

This is a version of the vertical wrapper that allows jobs of different types to be wrapped together.
Note that the solution considers the order of the sections defined in the ``jobs_cxxx.conf`` file, so the order of the sections given in **JOBS_IN_WRAPPER** is irrelevant.
Additionally, jobs are grouped within the corresponding date, member and chunk hierarchy.

.. code-block:: ini

    [wrapper]
    TYPE = vertical-mixed
    JOBS_IN_WRAPPER = <JOB_SECTION1 JOB_SECTION2> # REQUIRED


Horizontal wrapper
==========================

The horizontal wrapper is more appropriate when there are multiple ensemble members that can be run in parallel.

If the wrapped jobs have an mpirun call, they will need machine files to specify in which nodes each job will run.
Different cases may need specific approaches when creating the machine files. For auto-ecearth use COMPONENTS instead of STANDARD.

.. code-block:: ini

    [wrapper]
    TYPE = horizontal
    MACHINEFILES = STANDARD

In order to be able to use the horizontal wrapper, in ``platforms_cxxx.conf`` set the maximum number of processors allowed by the platform in use:

.. code-block:: ini

    [marenostrum4]
    ...
    MAX_PROCESSORS = 2400

Shared-memory Experiments
**********************

There is also the possibility of setting the option **METHOD** to SRUN in the wrapper directive (**ONLY** for vertical and vertical-horizontal wrappers).

This allows to use SRUN instead of rely in machinefiles to work in parallel.

.. code-block:: ini

    [wrapper]
    TYPE = vertical
    METHOD = srun

Hybrid wrapper
==========================

The hybrid wrapper is a wrapper that works both vertically and horizontally at the same time, meaning that members and chunks can be wrapped in one single job.
Mixed approach using a combination of horizontal and vertical wrappers and the list of jobs is a list of lists.

Horizontal-vertical
===========================

- There is a dependency between lists. Each list runs after the previous one finishes; the jobs within the list run in parallel at the same time
- It is particularly suitable if there are jobs of different types in the list with different wall clocks, but dependencies between jobs of different lists; it waits for all the jobs in the list to finish before starting the next list


.. code-block:: ini

    [wrapper]
    TYPE = horizontal-vertical
    MACHINEFILES = STANDARD
    JOBS_IN_WRAPPER = SIM POST

.. figure:: ../workflows/horizontal-vertical.png
   :name: wrapper_horizontal_vertical
   :width: 80%
   :align: center
   :alt: hybrid wrapper


Vertical-horizontal
===========================

- In this approach, each list is independent of each other and run in parallel; jobs within the list run one after the other
- It is particularly suitable for running many sequential ensembles


.. code-block:: ini

    [wrapper]
    TYPE = vertical-horizontal
    MACHINEFILES = STANDARD
    JOBS_IN_WRAPPER = SIM POST

.. figure:: ../workflows/vertical-horizontal.png
   :name: wrapper_vertical_horizontal
   :width: 80%
   :align: center
   :alt: hybrid wrapper

Summary
==========================

In `autosubmit_cxxx.conf`:

.. code-block:: ini

    # Basic Configuration of wrapper
    #TYPE = {vertical,vertical-mixed,horizontal,horizontal-vertical,vertical-horizontal} # REQUIRED
    # JOBS_IN_WRAPPER = Sections that should be wrapped together ex SIM
    # MIN_WRAPPED set the minim  number of jobs that should be included in the wrapper. DEFAULT = 2
    # MAX_WRAPPED set the maxim  number of jobs that should be included in the wrapper. DEFAULT = TOTALJOBS

    [wrapper]
    TYPE = Vertical #REQUIRED
    JOBS_IN_WRAPPER = SIM # Job types (as defined in jobs_cxxx.conf) separated by space. REQUIRED only if vertical-mixed
    DEPENDENCIES = {True,False} # OPTIONAL. False if not specified
    MIN_WRAPPED = 2
    MAX_WRAPPED = 9999 # OPTIONAL. Integer value, overrides TOTALJOBS
    CHECK_TIME_WRAPPER = # OPTIONAL. Time in seconds, overrides SAFETYSLEEPTIME

In `platforms_cxxx.conf`:

.. code-block:: ini

    [marenostrum4]
    ...
    MAX_WALLCLOCK =
    MAX_PROCESSORS =
    PROCESSORS_PER_NODE = 48


Visualization examples
===============================

When using the wrapper, it is useful to be able to visualize which packages are being created.
So, when executing *autosubmit monitor cxxx*, a dashed box indicates the jobs that are wrapped together in the same job package.


Vertical-mixed wrapper
**********************

Considering a very simple workflow with the configurations as follows:

.. code-block:: ini

    [wrapper]
    TYPE = vertical-mixed
    JOBS_IN_WRAPPER = SIM POST


.. figure:: ../workflows/wrapper.png
   :name: wrapper
   :width: 100%
   :align: center
   :alt: wrapped jobs

Horizontal wrapper with remote dependencies
**********************

.. code-block:: ini

   [wrapper]
   TYPE = horizontal
   JOBS_IN_WRAPPER = SIM POST

.. figure:: ../workflows/horizontal_remote.png
   :name: horizontal_remote
   :width: 60%
   :align: center
   :alt: horizontally wrapped jobs
