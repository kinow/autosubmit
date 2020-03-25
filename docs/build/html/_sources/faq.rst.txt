############
FAQ - Frequently Asked Questions
############

[CRITICAL] Unhandled exception on Autosubmit: [Errno 11] Resource temporarily unavailable
====================

.. code-block:: python

    [CRITICAL] Unhandled exception on Autosubmit: [Errno 11] Resource temporarily unavailable
    Traceback (most recent call last):
    File "/shared/earth/software/autosubmit/3.11.0b-foss-2015a-Python-2.7.9/lib/python2.7/site-packages/autosubmit-3.10.0-py2.7.egg/autosubmit/autosubmit.py", line 402, in parse_args
    args.group_by, args.expand, args.expand_status)
    File "/shared/earth/software/autosubmit/3.11.0b-foss-2015a-Python-2.7.9/lib/python2.7/site-packages/autosubmit-3.10.0-py2.7.egg/autosubmit/autosubmit.py", line 2093, in set_status
    with portalocker.Lock(os.path.join(tmp_path, 'autosubmit.lock'), timeout=1):
    File "/shared/earth/software/autosubmit/3.11.0b-foss-2015a-Python-2.7.9/lib/python2.7/site-packages/portalocker-1.2.0-py2.7.egg/portalocker/utils.py", line 195, in __enter__
    return self.acquire()
    File "/shared/earth/software/autosubmit/3.11.0b-foss-2015a-Python-2.7.9/lib/python2.7/site-packages/portalocker-1.2.0-py2.7.egg/portalocker/utils.py", line 155, in acquire
    raise exceptions.LockException(exception)
    LockException: [Errno 11] Resource temporarily unavailable


Solution
---------------
Make sure the experiment is not still running. If it's not, delete the autosubmit.lock in the /tmp folder inside your experiment directory.

----

[CRITICAL] Unhandled exception on Autosubmit: attempt to write a readonly database
====================

.. code-block:: python

    [CRITICAL] Unhandled exception on Autosubmit: attempt to write a readonly database
    Traceback (most recent call last):
     File "/shared/earth/software/autosubmit/3.11.0b-foss-2015a-Python-2.7.9/lib/python2.7/site-packages/autosubmit-3.10.0-py2.7.egg/autosubmit/autosubmit
    .py", line 389, in parse_args
       return Autosubmit.create(args.expid, args.noplot, args.hide, args.output, args.group_by, args.expand, args.expand_status)
     File "/shared/earth/software/autosubmit/3.11.0b-foss-2015a-Python-2.7.9/lib/python2.7/site-packages/autosubmit-3.10.0-py2.7.egg/autosubmit/autosubmit
    .py", line 1953, in create
       "job_packages_" + expid).reset_table()
     File "/shared/earth/software/autosubmit/3.11.0b-foss-2015a-Python-2.7.9/lib/python2.7/site-packages/autosubmit-3.10.0-py2.7.egg/autosubmit/job/job_pa
    ckage_persistence.py", line 65, in reset_table
       self.db_manager.drop_table(self.JOB_PACKAGES_TABLE)
     File "/shared/earth/software/autosubmit/3.11.0b-foss-2015a-Python-2.7.9/lib/python2.7/site-packages/autosubmit-3.10.0-py2.7.egg/autosubmit/database/d
    b_manager.py", line 65, in drop_table
       cursor.execute(drop_command)
    OperationalError: attempt to write a readonly database

Solution
---------------
This usually happens when trying to run `autosubmit create` with an expid of another user, please double check the expid you are using.

----

[ERROR] Command sbatch -D ... failed with error message: sbatch: error: Batch job submission failed: Invalid account or account/partition combination specified
====================

Solution
---------------
This can be due to an invalid configuration in your ~/.ssh/config file, so check if you are able to run a ssh command using the account displayed in the error message.
If so, once you are in the remote platform, type bsc_acct and see if the information for your username/account is displayed:

.. code-block:: ini

    USER CONSUMED CPU:

    User:                                             Machine:          Used [khours]:

If not, contact support referring to the problem and specifying your account.

----

[ERROR] Cannot send file to remote platform
===================================

.. code-block:: python

    [ERROR] marenostrum4 submission failed
    [CRITICAL] Unhandled exception on Autosubmit: size mismatch in put!  0 != 38998
    Traceback (most recent call last):
      File "/shared/earth/software/autosubmit/3.11.0b-foss-2015a-Python-2.7.9/lib/python2.7/site-packages/autosubmit-3.10.0-py2.7.egg/autosubmit/autosubmit.py", line 368, in parse_args
        return Autosubmit.run_experiment(args.expid)
      File "/shared/earth/software/autosubmit/3.11.0b-foss-2015a-Python-2.7.9/lib/python2.7/site-packages/autosubmit-3.10.0-py2.7.egg/autosubmit/autosubmit.py", line 776, in run_experiment
        if Autosubmit.submit_ready_jobs(as_conf, job_list, platforms_to_test, packages_persistence):
      File "/shared/earth/software/autosubmit/3.11.0b-foss-2015a-Python-2.7.9/lib/python2.7/site-packages/autosubmit-3.10.0-py2.7.egg/autosubmit/autosubmit.py", line 819, in submit_ready_jobs
        package.submit(as_conf, job_list.parameters)
      File "/shared/earth/software/autosubmit/3.11.0b-foss-2015a-Python-2.7.9/lib/python2.7/site-packages/autosubmit-3.10.0-py2.7.egg/autosubmit/job/job_packages.py", line 87, in submit
        self._send_files()
      File "/shared/earth/software/autosubmit/3.11.0b-foss-2015a-Python-2.7.9/lib/python2.7/site-packages/autosubmit-3.10.0-py2.7.egg/autosubmit/job/job_packages.py", line 115, in _send_files
        self.platform.send_file(self._job_scripts[job.name])
      File "/shared/earth/software/autosubmit/3.11.0b-foss-2015a-Python-2.7.9/lib/python2.7/site-packages/autosubmit-3.10.0-py2.7.egg/autosubmit/platforms/paramiko_platform.py", line 129, in send_file
        ftp.put(os.path.join(self.tmp_path, filename), os.path.join(self.get_files_path(), filename))
      File "/shared/earth/software/autosubmit/3.11.0b-foss-2015a-Python-2.7.9/lib/python2.7/site-packages/paramiko-1.15.0-py2.7.egg/paramiko/sftp_client.py", line 669, in put
        return self.putfo(fl, remotepath, file_size, callback, confirm)
      File "/shared/earth/software/autosubmit/3.11.0b-foss-2015a-Python-2.7.9/lib/python2.7/site-packages/paramiko-1.15.0-py2.7.egg/paramiko/sftp_client.py", line 635, in putfo
        raise IOError('size mismatch in put!  %d != %d' % (s.st_size, size))
     IOError: size mismatch in put!  0 != 38998

This happens when the quota has been reached and the machine is full

----

[CRITICAL] Unhandled exception on Autosubmit: database is locked
===================================

.. code-block:: python

    [CRITICAL] Unhandled exception on Autosubmit: database is locked
    Traceback (most recent call last):
      File "/shared/earth/software/autosubmit/3.11.0b-foss-2015a-Python-2.7.9/lib/python2.7/site-packages/autosubmit-3.10.0-py2.7.egg/autosubmit/autosubmit.py", line 377, in parse_args
        args.operational) != ''
      File "/shared/earth/software/autosubmit/3.11.0b-foss-2015a-Python-2.7.9/lib/python2.7/site-packages/autosubmit-3.10.0-py2.7.egg/autosubmit/autosubmit.py", line 532, in expid
        exp_id = copy_experiment(copy_id, description, Autosubmit.autosubmit_version, test, operational)
      File "/shared/earth/software/autosubmit/3.11.0b-foss-2015a-Python-2.7.9/lib/python2.7/site-packages/autosubmit-3.10.0-py2.7.egg/autosubmit/experiment/experiment_common.py", line 93, in copy_experiment
        new_name = new_experiment(description, version, test, operational)
      File "/shared/earth/software/autosubmit/3.11.0b-foss-2015a-Python-2.7.9/lib/python2.7/site-packages/autosubmit-3.10.0-py2.7.egg/autosubmit/experiment/experiment_common.py", line 68, in new_experiment
        if not db_common.save_experiment(new_name, description, version):
      File "/shared/earth/software/autosubmit/3.11.0b-foss-2015a-Python-2.7.9/lib/python2.7/site-packages/autosubmit-3.10.0-py2.7.egg/autosubmit/database/db_common.py", line 151, in save_experiment
        {'name': name, 'description': description, 'version': version})
    OperationalError: database is locked

Solution
---------------
If you were trying to copy an experiment, make sure you put the -y immediately after expid: `autosubmit expid -y`

----

bash: sbatch: command not found
===================================

Solution
---------------
First, check your jobs_expid.conf and platforms_expid.conf files and make sure the platform assigned to the running job is defined correctly and is a SLURM platform.
If this is ok, check that the hostname of the platform you are using is also correctly defined in your ~/.ssh/config file.
