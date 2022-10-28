# #!/usr/bin/env python3
# import datetime
# import os
# import time
# import sys
# import inspect
# sys.path.insert(0, os.path.abspath('.'))
# from autosubmit.autosubmit import Autosubmit
# from autosubmitconfigparser.config.config_common import AutosubmitConfig, BasicConfig
# from bscearth.utils.config_parser import ConfigParserFactory
# from autosubmit.job.job_list import JobList
# from autosubmit.database.db_jobdata import JobDataStructure
# from bscearth.utils.log import Log
# from autosubmit.autosubmit import Autosubmit
# from pyparsing import nestedExpr

# text = "[ 1960(0605-1206) [ fc0 [1 2 3 4] fc1 [1] ] 16651101 [ fc0 [1-30 31 32] ] ]"
# out = Autosubmit._create_json(text)
# print(out)

# def test_retrieve_energy():
#     BasicConfig.read()
#     expid = "a2ze"
#     job_name = "a2ze_REMOTE_COMPILE"
#     as_conf = AutosubmitConfig(
#         expid, BasicConfig, ConfigParserFactory())
#     if not as_conf.check_conf_files():
#         Log.critical('Can not run with invalid configuration')
#         return False
#     submitter = Autosubmit._get_submitter(as_conf)
#     submitter.load_platforms(as_conf)
#     job_list = Autosubmit.load_job_list(
#         expid, as_conf, notransitive=False)
#     Autosubmit._load_parameters(
#         as_conf, job_list, submitter.platforms)

#     for job in job_list.get_job_list():
#         if job.platform_name is None:
#             job.platform_name = "marenostrum4"
#         # noinspection PyTypeChecker
#         job._platform = submitter.platforms[job.platform_name.lower(
#         )]

#     list_jobs = job_list.get_job_list()
#     job_honk = [job for job in list_jobs if job.name == job_name][0]
#     job_honk.write_end_time(True)


# def main():
#     job_structure = JobDataStructure('a29z')
#     # print(job_structure._select_pragma_version())
#     return None


# if __name__ == "__main__":
#     main()
