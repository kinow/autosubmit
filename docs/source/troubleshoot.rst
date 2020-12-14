###############
Troubleshooting
###############

How to change the job status stopping autosubmit
================================================

Review :ref:`setstatus`.

How to change the job status without stopping autosubmit
========================================================

Review :ref:`setstatusno`.

Other possible errors
=====================

I see the `database malformed` error on my experiment log.

*Explanation*: The latest version of autosubmit uses a database to efficiently track changes in the jobs of your experiment. It might happen that this small database gets corrupted.

*Solution*: run `autosubmit dbfix expid` where `expid` is the identifier of your experiment. This function will rebuild the database saving as much information as possible (usually all of it).

