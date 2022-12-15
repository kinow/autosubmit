############
Introduction
############

What is Autosubmit ?
====================



Autosubmit is a lightweight workflow manager designed to meet climate research necessities. Unlike other workflow solutions in the domain, it integrates the capabilities of an experiment manager, workflow orchestrator and monitor in a self-contained application. The experiment manager allows for defining and configuring experiments, supported by a hierarchical database that ensures reproducibility and traceability. The orchestrator is designed to run complex workflows in research and operational mode by managing their dependencies and interfacing with local and remote hosts. These multi-scale workflows can involve from a few to thousands of steps and from one to multiple platforms.

Autosubmit facilitates easy and fast integration and relocation on new platforms. On the one hand, users can rapidly execute general scripts and progressively parametrize them by reading Autosubmit variables. On the other hand, it is a self-contained desktop application capable of submitting jobs to remote platforms without any external deployment.

Due to its robustness, it can handle different eventualities, such as networking or I/O errors. Finally, the monitoring capabilities extend beyond the desktop application through a REST API that allows communication with workflow monitoring tools such as the Autosubmit web GUI.

Autosubmit is a Python package provided in PyPI. Conda recipes can also be found on the website. A containerized version for testing purposes is also available but not public yet.

It has contributed to various European research projects and runs different operational systems. During the following years, it will support some of the Earth Digital Twins as the Digital Twin Ocean.

Concretely, it is currently used at Barcelona Supercomputing Centre (BSC) to run models (EC-Earth, MONARCH, NEMO, CALIOPE, HERMES…), operational toolchains (S2S4E), data-download workflows (ECMWF MARS), and many other. Autosubmit has run these workflows in different supercomputers in BSC, ECMWF, IC3, CESGA, EPCC, PDC, and OLCF.

Get involved or contact us:      
                                     
+----------------------------+-------------------------------------------+
| GitLab:                    | https://earth.bsc.es/gitlab/es/autosubmit |
+----------------------------+-------------------------------------------+
| Mail:                      | support-autosubmit@bsc.es                 |
+----------------------------+-------------------------------------------+

Why is Autosubmit needed ?
==========================

Autosubmit is the only existing tool that satisfies the following requirements from the weather and climate community:

- **Automatization** Job submission to machines and dependencies between jobs are managed by Autosubmit. No user intervention is needed.
- **Data provenance** Assigns unique identifiers for each experiment and stores information about model version, experiment configuration and computing facilities used in the whole process.
- **Failure tolerance** Automatic retrials and ability to rerun chunks in case of corrupted or missing data.
- **Resource management** Autosubmit manages supercomputer particularities, allowing users to run their experiments in the available machine without having to adapt the code. Autosubmit also allows to submit tasks from the same experiment to different platforms.




How does Autosubmit work ?
==========================

You can find help about how to use autosubmit and a list of available commands, just executing:
::

    autosubmit -h

Execute autosubmit <command> -h for detailed help for each command:
::

    autosubmit expid -h

Experiment creation
-------------------

To create a new experiment, run the command:
::

    autosubmit expid -H "HPCname" -d "Description"

*HPCname* is the name of the main HPC platform for the experiment: it will be the default platform for the tasks.
*Description* is a brief experiment description.

This command assigns to the experiment a unique four alphanumerical characters identifier, where the first has reserved letters *a* and
*t*. It then creates a new folder in experiments repository with structure shown in Figure :numref:`exp_folder`.


.. figure:: fig1.png
   :name: exp_folder
   :width: 33%
   :align: center
   :alt: experiment folder

   Example of an experiment directory tree.

Experiment configuration
------------------------

To configure the experiment, edit ``expdef_xxxx.yml``, ``jobs_xxxx.yml`` and ``platforms_xxxx.yml`` in the ``conf`` folder of the experiment (see contents in Figure :numref:`exp_config`).

.. figure:: fig2.png
   :name: exp_config
   :width: 50%
   :align: center
   :alt: configuration files

   Configuration files content

After that, you are expected to run the command:
::

    autosubmit create xxxx

This command creates the experiment project in the ``proj`` folder. The experiment project contains the scripts specified in ``jobs_xxxx.yml`` and a copy of model source code and data specified in ``expdef_xxxx.yml``.

Experiment run
--------------

To run the experiment, just execute the command:

    .. code-block:: bash

        # Add your key to ssh agent ( if encrypted )
        ssh-add ~/.ssh/id_rsa
        autosubmit run a000

Autosubmit will start submitting jobs to the relevant platforms (both HPC and supporting computers) by using the scripts specified in ``jobs_xxxx.yml``. Autosubmit will substitute variables present on scripts where handlers appear in *%variable_name%* format. Autosubmit provides variables for *current chunk*, *start date*, *member*, *computer configuration* and more, and also will replace variables form ``proj_xxxx.yml``.

To monitor the status of the experiment, issue the command:

::

    autosubmit monitor xxxx

This will plot the workflow of the experiment and the current status.

.. figure:: fig3.png
   :width: 70%
   :align: center
   :alt: experiment plot

   Example of monitoring plot for EC-Earth run with Autosubmit for 1 start date, 1 member and 3 chunks.

