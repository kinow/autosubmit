###############
Troubleshooting
###############

How to change the job status stopping autosubmit
================================================

Review :ref:`setstatus`.

How to change the job status without stopping autosubmit
========================================================

Review :ref:`setstatusno`.

My project parameters are not being substituted in the templates.
========================================================

*Explanation*: If there is a duplicated section or option in any other side of autosubmit, including proj files It won't be able to recognize which option pertains to what section in which file.

*Solution*: Don't repeat section names and parameters names until Autosubmit 4.0 release.

Unable to recover remote logs files.
========================================================

*Explanation*: If there are limitations on the remote platform regarding multiple connections,
*Solution*:  You can try DISABLE_RECOVERY_THREADS = TRUE under the [platform_name] section in the platform.conf.

Other possible errors
=====================

I see the `database malformed` error on my experiment log.

*Explanation*: The latest version of autosubmit uses a database to efficiently track changes in the jobs of your experiment. It might happen that this small database gets corrupted.

*Solution*: run `autosubmit dbfix expid` where `expid` is the identifier of your experiment. This function will rebuild the database saving as much information as possible (usually all of it).



