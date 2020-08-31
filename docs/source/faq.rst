############
Critical Error codes - Solutions
############

Database Issues  - Critical Error codes [7001-7005]
====================

+------+----------------------------------------------+-----------------------------------------------------------------+
| Code | Details                                      | Solution                                                        |
+======+----------------------------------------------+===============================+=================================+
| 7001 | Connection to the db couldn't be established | Check if database exists                                        |
+------+----------------------------------------------+-----------------------------------------------------------------+
| 7002 | Wrong version                                | Check system sqlite version                                     |
+------+----------------------------------------------+-----------------------------------------------------------------+
| 7003 | DB doesn't exists                            | Check if database exists                                        |
+------+----------------------------------------------+-----------------------------------------------------------------+
| 7004 | Can't create a new database                  | check your user permissions                                     |
+------+----------------------------------------------+-----------------------------------------------------------------+
| 7005 | AS database is corrupted or locked           | Please, open a new issue ASAP. (If you are on BSC environment)  |
+------+----------------------------------------------+-----------------------------------------------------------------+

Default Solution
---------------
These issues are usually from server side, ask first in Autosubmit git if you don't have a custom installation-

----

Wrong User Input  - Critical Error codes [7010-7030]
====================

+------------+------------+-----------+
| Code   | Details   | Solution  |
+============+============+===========+
| 7010 | Experiment has been halted in a manual way     |
+------+------------+-----------+
| 7011 | Wrong arguments for an specific command   | Check the command section for more info   |
+------+------------+-----------+
| 7012 | Insufficient permissions for an specific experiment. | Check if you have enough permissions, experiment exists or specified expid has a typo|
+------+------------+-----------+
| 7013 | Pending commits | You must commit/synchronize pending changes in the experiment proj folder.  |
+------+------------+-----------+
| 7014 | Wrong configuration   | Check your experiment/conf files, also take a look to  the ASLOG/command.log detailed output   |
+------+------------+-----------+

Default Solution
---------------

These issues are usually mistakes from the user input, check the avaliable logs and git resolved issues. Alternative, you can ask for help to Autosubmit team.

----

Platform issues  - Critical Error codes. Local [7040-7050] and remote [7050-7060]
====================

+------+------------+----------+
| Code | Details   | Solution  |
+======+=================================================================+================================================================================================+
| 7040 | Invalid experiment pkl/db likely due a local platform failure   | Should be recovered automatically, if not check if there is a backup file and do it manually   |
+------+------------+-----------+
| 7041 | Weird job status   | Weird Job status, try to recover experiment(check the recovery how-to for more info) if this issue persist please, report it to gitlab  |
+------+------------+-----------+
| 7050 | Connection can't be established.   | check your experiment platform configuration   |
+------+------------+-----------+
| 7050 | Failure after a restart, connection can't be restored.   | Check or ask (manually) if the remote platforms have any known issue   |
+------+------------+-----------+
| 7051 | Invalid ssh configuration.   | Check .ssh/config file. Additionally, Check if you can perform a password less connection to that platform.  |
+------+------------+-----------+

Default Solution
---------------

Check autosubmit log for detailed information, there will be additional error codes.

----

Uncatalogued Issues  - Critical Error codes [7060+]
====================

+------+------------+-----------+
| Code | Details   | Solution  |
+======+===========+===========+
| 7060 |  Display issues during monitoring   | try to use a different output or txt   |
+------+------------+-----------+
| 7061 | Stat command failed   | Check Aslogs command output, open a git issue   |
+------+------------+-----------+
| 7062 | Svn issues   | Check, in expdef, if url exists   |
+------+------------+-----------+
| 7063 | cp/rsync issues   | Check if destination path exists   |
+------+------------+-----------+
| 7064 | Git issues   | check that the proj folder is a well configured git folder. Also, check [GIT] expdef config  |
+------+------------+-----------+
| 7065 | Wrong git configuration   | Invalid git url. Check [GIT] expdef config. If issue persists, check if proj folder is a well configured git folder.   |
+------+------------+-----------+
| 7066 | Presubmission feature issues   | New feature, this message should be prompt. Please report it to Git|
+------+------------+-----------+

Default Solution
---------------

Check autosubmit log for detailed information, there will be additional error codes.

----
