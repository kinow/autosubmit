import unittest
from autosubmit.statistics.statistics import Statistics
from autosubmit.job.job_common import Status
from autosubmit.job.job_utils import SubJobManager, SubJob
from autosubmitconfigparser.config.basicconfig import BasicConfig
from autosubmitconfigparser.config.configcommon import AutosubmitConfig
from bscearth.utils.config_parser import ConfigParserFactory
from autosubmit.autosubmit import Autosubmit
from autosubmit.job.job_list import JobList
# import autosubmit.experiment.common_db_requests as DbRequests
import autosubmit.database.db_structure as DbStructure
# from autosubmit.database.db_jobdata import JobDataStructure, ExperimentGraphDrawing

class TestStatistics(unittest.TestCase):
  def setUp(self):
    self.expid = "a49z"

  def test_normal_execution(self):
    print("Testing normal execution")
    expid = self.expid
    period_fi = ""
    period_ini = ""
    ft = "Any"
    results = None
    subjobs = list()
    BasicConfig.read()
    path_structure = BasicConfig.STRUCTURES_DIR
    path_local_root = BasicConfig.LOCAL_ROOT_DIR
    as_conf = AutosubmitConfig(expid)
    as_conf.reload(first_load=True)
    job_list = Autosubmit.load_job_list(expid, as_conf, False)
    jobs_considered = [job for job in job_list.get_job_list() if job.status not in [
            Status.READY, Status.WAITING]]
    job_to_package, package_to_jobs, _, _ = JobList.retrieve_packages(
            BasicConfig, expid, [job.name for job in job_list.get_job_list()])
    queue_time_fixes = {}
    if job_to_package:
      current_table_structure = DbStructure.get_structure(expid, BasicConfig.STRUCTURES_DIR)
      subjobs = []
      for job in job_list.get_job_list():
          job_info = JobList.retrieve_times(job.status, job.name, job._tmp_path, make_exception=False, job_times=None, seconds=True, job_data_collection=None)
          time_total = (job_info.queue_time + job_info.run_time) if job_info else 0
          subjobs.append(
              SubJob(job.name,
                  job_to_package.get(job.name, None),
                  job_info.queue_time if job_info else 0,
                  job_info.run_time if job_info else 0,
                  time_total,
                  job_info.status if job_info else Status.UNKNOWN)
          )
      queue_time_fixes = SubJobManager(subjobs, job_to_package, package_to_jobs, current_table_structure).get_collection_of_fixes_applied()


    if len(jobs_considered) > 0:
      print("Get results")
      exp_stats = Statistics(jobs_considered, period_ini, period_fi, queue_time_fixes)
      exp_stats.calculate_statistics()
      exp_stats.calculate_summary()
      exp_stats.make_old_format()    
      print(exp_stats.get_summary_as_list())
      failed_jobs_dict = exp_stats.build_failed_jobs_only_list() 
    else:
        raise Exception("Autosubmit API couldn't find jobs that match your search critearia (Section: {0}) in the period from {1} to {2}.".format(
            ft, period_ini, period_fi))
    return results

if __name__ == '__main__':
  unittest.main()