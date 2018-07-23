from unittest import TestCase
from math import ceil
from autosubmit.platforms.wrappers.wrapper_builder import PythonWrapperBuilder
import textwrap
import collections


class TestMachinefiles(TestCase):

    def setUp(self):
        self.job_scripts = ['JOB_1', 'JOB_2', 'JOB_3']

    def test_job_less_than_48_cores_standard(self):
        num_processors = 60
        jobs_resources = {'MACHINEFILES': 'STANDARD', 'JOB': {'PROCESSORS': '20', 'TASKS': '48'},
                          'PROCESSORS_PER_NODE': '48'}

        wrapper_builder = PythonWrapperBuilder(header_directive='', jobs_scripts=self.job_scripts,
                                               num_processors=num_processors, expid='a000',
                                               jobs_resources=jobs_resources)

        nodes = self._create_nodelist(num_processors)
        cores_list = wrapper_builder.build_cores_list()
        machinefiles_code = wrapper_builder.get_machinefile_function().replace("_NEWLINE_", '\\n')

        result = dict()

        script = textwrap.dedent("""
        from math import ceil
        
        all_nodes = {0}
        section = 'JOB'
        {1}
        machinefiles_dict = dict()
        for job in {2}:
        {3}
            machinefiles_dict[job] = machines
        """).format(nodes, cores_list, self.job_scripts, wrapper_builder._indent(machinefiles_code, 4))

        exec (script, result)

        machinefiles_dict = result["machinefiles_dict"]
        all_machines = list()
        for job, machines in machinefiles_dict.items():
            machines = machines.split("\n")[:-1]
            job_section = job.split("_")[0]
            job_cores = int(jobs_resources[job_section]['PROCESSORS'])
            self.assertEquals(len(machines), job_cores)
            all_machines += machines

        machines_count = collections.Counter(all_machines)
        for count in machines_count.values():
            self.assertLessEqual(count, int(jobs_resources['PROCESSORS_PER_NODE']))

    def test_job_more_than_48_cores_standard(self):
        num_processors = 150
        jobs_resources = {'MACHINEFILES': 'STANDARD', 'JOB': {'PROCESSORS': '50', 'TASKS': '48'},
                          'PROCESSORS_PER_NODE': '48'}

        wrapper_builder = PythonWrapperBuilder(header_directive='', jobs_scripts=self.job_scripts,
                                               num_processors=num_processors, expid='a000',
                                               jobs_resources=jobs_resources)

        nodes = self._create_nodelist(num_processors)
        cores_list = wrapper_builder.build_cores_list()
        machinefiles_code = wrapper_builder.get_machinefile_function().replace("_NEWLINE_", '\\n')

        result = dict()

        script = textwrap.dedent("""
        from math import ceil

        all_nodes = {0}
        section = 'JOB'
        {1}
        machinefiles_dict = dict()
        for job in {2}:
        {3}
            machinefiles_dict[job] = machines
        """).format(nodes, cores_list, self.job_scripts, wrapper_builder._indent(machinefiles_code, 4))

        exec (script, result)
        machinefiles_dict = result["machinefiles_dict"]
        for job, machines in machinefiles_dict.items():
            machines = machines.split("\n")[:-1]
            job_section = job.split("_")[0]
            job_cores = int(jobs_resources[job_section]['PROCESSORS'])
            self.assertEquals(len(machines), job_cores)

    def _create_nodelist(self, num_cores):
        num_nodes = int(ceil(num_cores/float(48)))

        node_list = []

        for i in range(num_nodes):
            node_list.append('node_'+str(i))
        return node_list