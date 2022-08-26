How to run the experiment
=========================

.. toctree::
    :hidden:

    run
    restart_exp
    set_status
    stop_experiment
    run_members
    rerun_partially
    start_time
    start_after
    remote_dependencies
    run_two_step

Launch Autosubmit with the command:
::

    autosubmit run EXPID

*EXPID* is the experiment identifier.

Options:
::

    usage: autosubmit run [-h] expid

      expid       experiment identifier
      -nt                   --notransitive
                                prevents doing the transitive reduction when plotting the workflow
      -v                    --update_version
                                update the experiment version to match the actual autosubmit version
      -st                   --start_time
                                Sets the starting time for the experiment. Accepted format: 'yyyy-mm-dd HH:MM:SS' or 'HH:MM:SS' (defaults to current day).
      -sa                   --start_after 
                                Sets a experiment expid that will be tracked for completion. When this experiment is completed, the current instance of Autosubmit run will start.
      -rm                   --run_members
                                Sets a list of members allowed to run. The list must have the format '### ###' where '###' represents the name of the member as set in the conf files.
      -h, --help  show this help message and exit

Example:
::

    autosubmit run cxxx
.. important:: If the autosubmit version is set on autosubmit.conf it must match the actual autosubmit version
.. hint:: It is recommended to launch it in background and with ``nohup`` (continue running although the user who launched the process logs out).

Example:
::

    nohup autosubmit run cxxx &

.. important:: Before launching Autosubmit check password-less ssh is feasible (*HPCName* is the hostname):

.. important:: The host machine has to be able to access HPC's/Clusters via password-less ssh. Make sure that the ssh key is in PEM format `ssh-keygen -t rsa -b 4096 -C "email@email.com" -m PEM`.

    ``ssh HPCName``

More info on password-less ssh can be found at: http://www.linuxproblem.org/art_9.html

.. caution:: After launching Autosubmit, one must be aware of login expiry limit and policy (if applicable for any HPC) and renew the login access accordingly (by using token/key etc) before expiry.

How to run an experiment that was created with another version
--------------------------------------------------------------

.. important:: First of all you have to stop your Autosubmit instance related with the experiment

Once you've already loaded / installed the Autosubmit version do you want:
::

    autosubmit create EXPID
    autosubmit recovery EXPID -s -all
    autosubmit run EXPID -v
    or
    autosubmit updateversion EXPID
    autosubmit run EXPID -v
*EXPID* is the experiment identifier.
The most common problem when you change your Autosubmit version is the apparition of several Python errors.
This is due to how Autosubmit saves internally the data, which can be incompatible between versions.
The steps above represent the process to re-create (1) these internal data structures and to recover (2) the previous status of your experiment.
