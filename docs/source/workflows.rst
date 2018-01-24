#####################
Defining the workflow
#####################

One of the most important step that you have to do when planning to use autosubmit for an experiment is the definition
of the workflow the experiment will use. In this section you will learn about the workflow definition syntax so you will
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


The resulting workflow can be seen in Figure :numref:`simple`

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

To set at what level a job has to run you have to use the RUNNING attribute. It has four possible values: once, date,
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


The resulting workflow can be seen in Figure :numref:`running` for a experiment with 2 startdates, 2 members and 2 chunks.

.. figure:: workflows/running.png
   :name: running
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
example will show how to make a simulation job wait for the previous chunk of the simulation. To do that, we add
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


The resulting workflow can be seen in Figure :numref:`dprevious`

.. warning::

   Autosubmit simplifies the dependencies, so the final graph usually does not show all the lines that you may expect to
   see. In this example you can see that there are no lines between the ini and the sim jobs for chunks 2 to 5 because
   that dependency is redundant with the one on the previous sim


.. figure:: workflows/dependencies_previous.png
   :name: dprevious
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


The resulting workflow can be seen in Figure :numref:`dependencies`

.. figure:: workflows/dependencies_running.png
   :name: dependencies
   :width: 100%
   :align: center
   :alt: simple workflow plot

   Example showing dependencies between jobs running at different levels.


Job frequency
-------------

Some times you just don't need a job to be run on every chunk or member. For example, you may want to launch the postprocessing
job after various chunks have completed. This behaviour can be achieved using the FREQUENCY attribute. You can specify
an integer I for this attribute and the job will run only once for each I iterations on the running level.

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


The resulting workflow can be seen in Figure :numref:`frequency`

.. figure:: workflows/frequency.png
   :name: frequency
   :width: 100%
   :align: center
   :alt: simple workflow plot

   Example showing dependencies between jobs running at different frequencies.


Job synchronize
-------------

For jobs running at chunk level, and this job has dependencies, you could want
not to run a job for each experiment chunk, but to run once for all member/date dependencies, maintaining
the chunk granularity. In this cases you can use the SYNCHRONIZE job parameter to determine which kind
of synchronization do you want. See the below examples with and without this parameter.

.. hint::
   This job parameter works with jobs with RUNNING parameter equals to 'chunk'.

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

The resulting workflow can be seen in Figure :numref:`nosync`

.. figure:: workflows/no-synchronize.png
   :name: nosync
   :width: 100%
   :align: center
   :alt: simple workflow plot

   Example showing dependencies between chunk jobs running without synchronize.

.. code-block:: ini

    [ASIM]
    SYNCHRONIZE = member

The resulting workflow of setting SYNCHRONIZE parameter to 'member' can be seen in Figure :numref:`msynchronize`

.. figure:: workflows/member-synchronize.png
   :name: msynchronize
   :width: 100%
   :align: center
   :alt: simple workflow plot

   Example showing dependencies between chunk jobs running with member synchronize.

.. code-block:: ini

    [ASIM]
    SYNCHRONIZE = date

The resulting workflow of setting SYNCHRONIZE parameter to 'date' can be seen in Figure :numref:`dsynchronize`

.. figure:: workflows/date-synchronize.png
   :name: dsynchronize
   :width: 100%
   :align: center
   :alt: simple workflow plot

   Example showing dependencies between chunk jobs running with date synchronize.

Job split
------------------
For jobs running at chunk level, it may be useful to split each chunk into different parts.
This behaviour can be achieved using the SPLITS attribute to specify the number of parts.
It is possible to define dependencies to specific splits within [], as well as to a list/range of splits,
in the format [1:3,7,10] or [1,2,3]


.. hint::
   This job parameter works with jobs with RUNNING parameter equals to 'chunk'.

.. code-block:: ini

    [ini]
    FILE = ini.sh
    RUNNING = member

    [sim]
    FILE = sim.sh
    DEPENDENCIES = ini sim-1
    RUNNING = chunk

    [asim]
    FILE = asim.sh
    DEPENDENCIES = sim
    RUNNING = chunk
    SPLITS = 3

    [post]
    FILE = post.sh
    RUNNING = chunk
    DEPENDENCIES = asim[1] asim[1]+1

The resulting workflow can be seen in Figure :numref:`split`

.. figure:: workflows/split.png
   :name: split
   :width: 100%
   :align: center
   :alt: simple workflow plot

   Example showing the job ASIM divided into 3 parts for each chunk.


Job delay
------------------

Some times you need a job to be run after a certain number of chunks. For example, you may want to launch the asim
job after various chunks have completed. This behaviour can be achieved using the DELAY attribute. You can specify
an integer N for this attribute and the job will run only after N chunks.

.. hint::
   This job parameter works with jobs with RUNNING parameter equals to 'chunk'.

.. code-block:: ini

    [ini]
    FILE = ini.sh
    RUNNING = member

    [sim]
    FILE = sim.sh
    DEPENDENCIES = ini sim-1
    RUNNING = chunk

    [asim]
    FILE = asim.sh
    DEPENDENCIES = sim asim-1
    RUNNING = chunk
    DELAY = 2

    [post]
    FILE = post.sh
    DEPENDENCIES = sim asim
    RUNNING = chunk

The resulting workflow can be seen in Figure :numref:`delay`

.. figure:: workflows/experiment_delay_doc.png
   :name: delay
   :width: 100%
   :align: center
   :alt: simple workflow with delay option

   Example showing the asim job starting only from chunk 3.

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

The resulting workflow can be seen in Figure :numref:`rerun` for a rerun of chunks 2 and 3 of member 2.

.. figure:: workflows/rerun.png
   :name: rerun
   :width: 100%
   :align: center
   :alt: simple workflow plot

   Example showing a rerun workflow for chunks 2 and 3.