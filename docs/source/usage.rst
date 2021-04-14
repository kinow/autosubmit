*****
Usage
*****

Command list
============

-expid  Create a new experiment
-create  Create specified experiment workflow
-check  Check configuration for specified experiment
-describe  Show details for specified experiment
-run  Run specified experiment
-inspect  Generate cmd files
-test  Test experiment
-testcase  Test case experiment
-monitor  Plot specified experiment
-stats  Plot statistics for specified experiment
-setstatus  Sets job status for an experiment
-recovery  Recover specified experiment
-clean  Clean specified experiment
-refresh  Refresh project directory for an experiment
-delete  Delete specified experiment
-configure  Configure database and path for autosubmit
-install  Install database for Autosubmit on the configured folder
-archive  Clean, compress and remove from the experiments' folder a finalized experiment
-unarchive  Restores an archived experiment
-migrate_exp  Migrates an experiment from one user to another
-report  extract experiment parameters

.. toctree::
   :titlesonly:

   new_experiment/create_exp
   new_experiment/test
   new_experiment/testcase
   run_modes/run
   run_modes/run_members
   run_modes/start_time
   run_modes/start_after
   run_modes/rerun
   run_modes/wrappers
   run_modes/remote_dependencies
   run_modes/run_two_step
   configuration/configure
   configuration/new_job
   configuration/new_platform
   configuration/communication_library
   configuration/refresh
   configuration/create_members
   configuration/check
   workflow_validation/inspect
   workflow_validation/monitor
   workflow_validation/groups
   workflow_recovery/recovery
   workflow_recovery/stop
   workflow_recovery/recovery
   archive/clean
   archive/delete
   archive/archive
   archive/unarchive
   stats/report
   stats/stats
   stats/describe
   advanced_features/migrate
   advanced_features/custom_header
