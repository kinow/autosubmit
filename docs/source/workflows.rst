#####################
Defining the workflow
#####################

One of the most important step that you have to do when planning to use autosubmit for an experiment is the definition
of the workflow the experiment will use. On this section you will learn about the workflow definition syntax so you will
be able to exploit autosubmit's full potential

.. warning::
   This section is NOT intended to show how to define your jobs. Please go to :doc:`tutorial` section for a comprehensive
   list of job options.


Simple workflow
---------------

The simplest workflow that can be defined it is a sequence of two jobs, with the second one triggering at the end of
the first. To define it, we define the two jobs and then add a DEPENDECIES attribute on the second job referring to the
first one.

It is important to remember when defining workflows that DEPENDENCIES on autosubmit always refer to jobs that should
be finished before launching the job that has the DEPENDENCIES attribute.


.. code-block:: ini

   [One]
   FILE = one.sh

   [Two]
   FILE = two.sh
   DEPENDENCIES = One


The resulting workflow can be seen on figure 5.1

.. figure:: workflows/simple.png
   :name: simple
   :width: 100%
   :align: center
   :alt: simple workflow plot

   Example showing a simple workflow with two sequential jobs


Running jobs once per startdate, member or chunk
------------------------------------------------

Autosubmit is capable of running ensembles made of various startdates and members. It also has the capability to
divide member execution on different chunks.

To set at what level a job has to run you have to use the RUNNING attribute. It has four posible values: once, date,
member and chunk corresponding to running once, once per startdate, once per member or once per chunk respectively.

.. code-block:: ini

    [once]
    FILE = Once.sh

    [date]
    FILE = date.sh
    DEPENDENCIES = once
    RUNNING = date

    [member]
    FILE = Member.sh
    DEPENDENCIES = date
    RUNNING = member

    [chunk]
    FILE = Chunk.sh
    DEPENDENCIES = member
    RUNNING = chunk


The resulting workflow can be seen on figure 5.2 for a experiment with 2 startdates, 2 members and 2 chunks.

.. figure:: workflows/running.png
   :width: 100%
   :align: center
   :alt: simple workflow plot

   Example showing how to run jobs once per startdate, member or chunk.


Dependencies
------------

Dependencies on autosubmit were introduced on the first example, but in this section you will learn about some special
cases that will be very useful on your workflows.

Dependencies with previous jobs
_______________________________

Autosubmit can manage dependencies between jobs that are part of different chunks, members or startdates. The next
example will show how to make wait a simulation job for the previous chunk of the simulation. To do that, we add
sim-1 on the DEPENDENCIES attribute. As you can see, you can add as much dependencies as you like separated by spaces

.. code-block:: ini

   [ini]
   FILE = ini.sh
   RUNNING = member

   [sim]
   FILE = sim.sh
   DEPENDENCIES = ini sim-1
   RUNNING = chunk

   [postprocess]
   FILE = postprocess.sh
   DEPENDENCIES = sim
   RUNNING = chunk


The resulting workflow can be seen on figure 5.3

.. warning::

   Autosubmit simplifies the dependencies, so the final graph usually does not show all the lines that you may expect to
   see. In this example you can see that there are no lines between the ini and the sim jobs for chunks 2 to 5 because
   that dependency is redundant with the one on the previous sim


.. figure:: workflows/dependencies_previous.png
   :width: 100%
   :align: center
   :alt: simple workflow plot

   Example showing dependencies between sim jobs on different chunks.



Dependencies between running levels
___________________________________

On the previous examples we have seen that when a job depends on a job on a higher level (a running chunk job depending
on a member running job) all jobs wait for the higher running level job to be finished. That is the case on the ini sim dependency
on the next example.

In the other case, a job depending on a lower running level job, the higher level job will wait for ALL the lower level
jobs to be finished. That is the case of the postprocess combine dependency on the next example.

.. code-block:: ini

    [ini]
    FILE = ini.sh
    RUNNING = member

    [sim]
    FILE = sim.sh
    DEPENDENCIES = ini sim-1
    RUNNING = chunk

    [postprocess]
    FILE = postprocess.sh
    DEPENDENCIES = sim
    RUNNING = chunk

    [combine]
    FILE = combine.sh
    DEPENDENCIES = postprocess
    RUNNING = member


The resulting workflow can be seen on figure 5.4

.. figure:: workflows/dependencies_running.png
   :width: 100%
   :align: center
   :alt: simple workflow plot

   Example showing dependencies between jobs running at different levels.


Job frequency
-------------

Some times you just don't need a job to be run on every chunk or member. For example, you may want to launch the postprocessing
job after various chunks have completed. This behaviour can be achieved by using the FREQUENCY attribute. You can specify
an integer I on this attribute and the job will run only once for each I iterations on the running level.

.. hint::
   You don't need to adjust the frequency to be a divisor of the total jobs. A job will always execute at the last
   iteration of its running level

.. code-block:: ini

    [ini]
    FILE = ini.sh
    RUNNING = member

    [sim]
    FILE = sim.sh
    DEPENDENCIES = ini sim-1
    RUNNING = chunk

    [postprocess]
    FILE = postprocess.sh
    DEPENDENCIES = sim
    RUNNING = chunk
    FREQUENCY = 3

    [combine]
    FILE = combine.sh
    DEPENDENCIES = postprocess
    RUNNING = member


The resulting workflow can be seen on figure 5.5

.. figure:: workflows/frequency.png
   :width: 100%
   :align: center
   :alt: simple workflow plot

   Example showing dependencies between jobs running at different frequencies.


Job synchronize
-------------

Some times you just don't need a job to be run on every chunk or member. For example, you may want to launch the postprocessing
job after various chunks have completed. This behaviour can be achieved by using the FREQUENCY attribute. You can specify
an integer I on this attribute and the job will run only once for each I iterations on the running level.

.. hint::
   This job parameter was thought to work with jobs with RUNNING parameter equals to 'chunk'.

.. code-block:: ini

    [ini]
    FILE = ini.sh
    RUNNING = member

    [sim]
    FILE = sim.sh
    DEPENDENCIES = INI SIM-1
    RUNNING = chunk

    [ASIM]
    FILE = asim.sh
    DEPENDENCIES = SIM
    RUNNING = chunk

The resulting workflow can be seen on figure 5.6

.. figure:: workflows/no-synchronize.png
   :width: 100%
   :align: center
   :alt: simple workflow plot

   Example showing dependencies between chunk jobs running without synchronize.

.. code-block:: ini

    [ASIM]
    SYNCHRONIZE = member

The resulting workflow of setting SYNCHRONIZE parameter to 'member' can be seen on figure 5.7

.. figure:: workflows/member-synchronize.png
   :width: 100%
   :align: center
   :alt: simple workflow plot

   Example showing dependencies between chunk jobs running with member synchronize.

.. code-block:: ini

    [ASIM]
    SYNCHRONIZE = date

The resulting workflow of setting SYNCHRONIZE parameter to 'date' can be seen on figure 5.8

.. figure:: workflows/date-synchronize.png
   :width: 100%
   :align: center
   :alt: simple workflow plot

   Example showing dependencies between chunk jobs running with date synchronize.

Rerun dependencies
------------------

Autosubmit has the possibility to rerun some chunks of the experiment without affecting everything else. In this case,
autosubmit will automatically rerun all jobs of that chunk. If some of this jobs need another one on the workflow you
have to add the RERUN_DEPENDENCIES attribute and specify which jobs to rerun.

It is also usual that you will have some code that it is needed only in the case of a rerun. You can add this jobs to
the workflow as usual and set the attribute RERUN_ONLY to true. This jobs will be omitted from the workflow in the normal
case, but will appear on the reruns.

.. code-block:: ini

    [prepare_rerun]
    FILE = prepare_rerun.sh
    RERUN_ONLY = true
    RUNNING = member

    [ini]
    FILE = ini.sh
    RUNNING = member

    [sim]
    FILE = sim.sh
    DEPENDENCIES = ini combine prepare_rerun
    RERUN_DEPENDENCIES = combine prepare_rerun
    RUNNING = chunk

    [postprocess]
    FILE = postprocess.sh
    DEPENDENCIES = sim
    RUNNING = chunk

    [combine]
    FILE = combine.sh
    DEPENDENCIES = postprocess
    RUNNING = member

The resulting workflow can be seen on figure 5.9 for a rerun of chunks 2 and 3 of member 2.

.. figure:: workflows/rerun.png
   :width: 100%
   :align: center
   :alt: simple workflow plot

   Example showing a rerun workflow for chunks 2 and 3.