#!/usr/bin/env python

# Copyright 2014 Climate Forecasting Unit, IC3

# This file is part of Autosubmit.

# Autosubmit is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# Autosubmit is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with Autosubmit.  If not, see <http://www.gnu.org/licenses/>.


import os
import re

from autosubmit.job.job_common import Status
from autosubmit.job.job_common import Type
from autosubmit.job.job_common import Template
from autosubmit.job.job_common import ArHeader
from autosubmit.job.job_common import BscHeader
from autosubmit.job.job_common import EcHeader
from autosubmit.job.job_common import HtHeader
from autosubmit.job.job_common import ItHeader
from autosubmit.job.job_common import MnHeader
from autosubmit.job.job_common import PsHeader
from autosubmit.job.job_common import LgHeader

from autosubmit.job.job_common import StatisticsSnippet
from autosubmit.config.basicConfig import BasicConfig
from autosubmit.date.chunk_date_lib import *


class Job:
    """Class to handle all the tasks with Jobs at HPC.
       A job is created by default with a name, a jobid, a status and a type.
       It can have children and parents. The inheritance reflects the dependency between jobs.
       If Job2 must wait until Job1 is completed then Job2 is a child of Job1. Inversely Job1 is a parent of Job2 """

    def __init__(self, name, jobid, status, jobtype):
        self.name = name
        self._long_name = None
        self.long_name = name
        self._short_name = None
        self.short_name = name

        self.id = jobid
        self.status = status
        self.type = jobtype
        self.parents = list()
        self.children = list()
        self.fail_count = 0
        self.expid = name.split('_')[0]
        self._complete = True
        self.parameters = dict()
        self._tmp_path = BasicConfig.LOCAL_ROOT_DIR + "/" + self.expid + "/" + BasicConfig.LOCAL_TMP_DIR + "/"

    def delete(self):
        del self.name
        del self._long_name
        del self._short_name
        del self.id
        del self.status
        del self.type
        del self.parents
        del self.children
        del self.fail_count
        del self.expid
        del self._complete
        del self.parameters
        del self._tmp_path
        del self

    def print_job(self):
        print 'NAME: %s' % self.name
        print 'JOBID: %s' % self.id
        print 'STATUS: %s' % self.status
        print 'TYPE: %s' % self.type
        print 'PARENTS: %s' % [p.name for p in self.parents]
        print 'CHILDREN: %s' % [c.name for c in self.children]
        print 'FAIL_COUNT: %s' % self.fail_count
        print 'EXPID: %s' % self.expid

    # Properties

    @property
    def long_name(self):
        """Returns the job long name"""
        # name is returned instead of long_name. Just to ensure backwards compatibility with experiments
        # that does not have long_name attribute.
        if hasattr(self, '_long_name'):
            return self._long_name
        else:
            return self.name

    @long_name.setter
    def long_name(self, value):
        self._long_name = value

    @property
    def short_name(self):
        """Returns the job short name"""
        return self._short_name

    @short_name.setter
    def short_name(self, value):
        n = value.split('_')
        if len(n) == 5:
            self._short_name = n[1][:6] + "_" + n[2][2:] + "_" + n[3] + n[4][:1]
        elif len(n) == 4:
            self._short_name = n[1][:6] + "_" + n[2][2:] + "_" + n[3][:1]
        elif len(n) == 2:
            self._short_name = n[1]
        else:
            self._short_name = n[0][:15]

    def log_job(self):
        job_logger.info("%s\t%s\t%s" % ("Job Name", "Job Id", "Job Status"))
        job_logger.info("%s\t\t%s\t%s" % (self.name, self.id, self.status))

    def get_all_children(self):
        """Returns a list with job's childrens and all it's descendents"""
        job_list = list()
        for job in self.children:
            job_list.append(job)
            job_list += job.get_all_children()
        # convert the list into a Set to remove duplicates and the again to a list
        return list(set(job_list))

    def print_parameters(self):
        print self.parameters

    def inc_fail_count(self):
        self.fail_count += 1

    def add_parent(self, new_parent):
        self.parents += [new_parent]

    def add_children(self, new_children):
        self.children += [new_children]

    def delete_parent(self, parent):
        # careful, it is only possible to remove one parent at a time
        self.parents.remove(parent)

    def delete_child(self, child):
        # careful it is only possible to remove one child at a time
        self.children.remove(child)

    def has_children(self):
        return self.children.__len__()

    def has_parents(self):
        return self.parents.__len__()

    def compare_by_status(self, other):
        return cmp(self.status(), other.status)

    def compare_by_type(self, other):
        return cmp(self.type(), other.type)

    def compare_by_id(self, other):
        return cmp(self.id(), other.id)

    def compare_by_name(self, other):
        return cmp(self.name, other.name)

    def check_end_time(self):
        logname = self._tmp_path + self.name + '_COMPLETED'
        if os.path.exists(logname):
            return open(logname).readline().split()[0]
        else:
            return 0

    def check_queued_time(self):
        logname = self._tmp_path + self.name + '_COMPLETED'
        if os.path.exists(logname):
            return open(logname).readline().split()[1]
        else:
            return 0

    def check_run_time(self):
        logname = self._tmp_path + self.name + '_COMPLETED'
        if os.path.exists(logname):
            return open(logname).readline().split()[2]
        else:
            return 0

    def check_failed_times(self):
        logname = self._tmp_path + self.name + '_COMPLETED'
        if os.path.exists(logname):
            return open(logname).readline().split()[3]
        else:
            return 0

    def check_fail_queued_time(self):
        logname = self._tmp_path + self.name + '_COMPLETED'
        if os.path.exists(logname):
            return open(logname).readline().split()[4]
        else:
            return 0

    def check_fail_run_time(self):
        logname = self._tmp_path + self.name + '_COMPLETED'
        if os.path.exists(logname):
            return open(logname).readline().split()[5]
        else:
            return 0

    def check_completion(self):
        """ Check the presence of *COMPLETED file and touch a Checked or failed file """
        logname = self._tmp_path + self.name + '_COMPLETED'
        if os.path.exists(logname):
            self._complete = True
            os.system('touch ' + self._tmp_path + self.name + 'Checked')
            self.status = Status.COMPLETED
        else:
            os.system('touch ' + self._tmp_path + self.name + 'Failed')
            self.status = Status.FAILED

    def remove_dependencies(self):
        """If Complete remove the dependency """
        if self._complete:
            self.status = Status.COMPLETED
            # job_logger.info("Job is completed, we are now removing the dependency in"
            # " his %s child/children:" % self.has_children())
            for child in self.children:
                # job_logger.debug("number of Parents:",child.has_parents())
                if child.get_parents().__contains__(self):
                    child.delete_parent(self)
        else:
            # job_logger.info("The checking in check_completion tell us that job %s has failed" % self.name)
            self.status = Status.FAILED

    def update_parameters(self):
        parameters = self.parameters
        splittedname = self.long_name.split('_')
        parameters['JOBNAME'] = self.name
        parameters['FAIL_COUNT'] = str(self.fail_count)

        string_date = None
        prev_days = None

        if self.type == Type.TRANSFER:
            parameters['SDATE'] = splittedname[1]
            string_date = splittedname[1]
            parameters['MEMBER'] = splittedname[2]
        elif (self.type == Type.INITIALISATION or
              self.type == Type.SIMULATION or
              self.type == Type.POSTPROCESSING or
              self.type == Type.CLEANING):
            parameters['SDATE'] = splittedname[1]
            string_date = splittedname[1]
            parameters['MEMBER'] = splittedname[2]
            if self.type == Type.INITIALISATION:
                parameters['CHUNK'] = '1'
                chunk = 1
            else:
                parameters['CHUNK'] = splittedname[3]
                chunk = int(splittedname[3])
            total_chunk = int(parameters['NUMCHUNKS'])
            chunk_length_in_month = int(parameters['CHUNKSIZE'])
            chunk_start = chunk_start_date(string_date, chunk, chunk_length_in_month)
            chunk_end = chunk_end_date(chunk_start, chunk_length_in_month)
            run_days = running_days(chunk_start, chunk_end)
            prev_days = previous_days(string_date, chunk_start)
            chunk_end_days = previous_days(string_date, chunk_end)
            day_before = previous_day(string_date)
            chunk_end_1 = previous_day(chunk_end)
            parameters['DAY_BEFORE'] = day_before
            parameters['Chunk_START_DATE'] = chunk_start
            parameters['Chunk_END_DATE'] = chunk_end_1
            parameters['RUN_DAYS'] = str(run_days)
            parameters['Chunk_End_IN_DAYS'] = str(chunk_end_days)

            chunk_start_m = chunk_start_month(chunk_start)
            chunk_start_y = chunk_start_year(chunk_start)

            parameters['Chunk_START_YEAR'] = str(chunk_start_y)
            parameters['Chunk_START_MONTH'] = str(chunk_start_m)
            if total_chunk == chunk:
                parameters['Chunk_LAST'] = 'TRUE'
            else:
                parameters['Chunk_LAST'] = 'FALSE'

        if self.type == Type.SIMULATION:
            parameters['PREV'] = str(prev_days)
            parameters['WALLCLOCK'] = parameters['WALLCLOCK_SIM']
            parameters['NUMPROC'] = parameters['NUMPROC_SIM']
            parameters['TASKTYPE'] = 'SIMULATION'
        elif self.type == Type.POSTPROCESSING:
            starting_date_year = chunk_start_year(string_date)
            starting_date_month = chunk_start_month(string_date)
            parameters['Starting_DATE_YEAR'] = str(starting_date_year)
            parameters['Starting_DATE_MONTH'] = str(starting_date_month)
            parameters['WALLCLOCK'] = parameters['WALLCLOCK_POST']
            parameters['NUMPROC'] = parameters['NUMPROC_POST']
            parameters['TASKTYPE'] = 'POSTPROCESSING'
        elif self.type == Type.CLEANING:
            parameters['WALLCLOCK'] = parameters['WALLCLOCK_CLEAN']
            parameters['NUMPROC'] = parameters['NUMPROC_CLEAN']
            parameters['TASKTYPE'] = 'CLEANING'
        elif self.type == Type.INITIALISATION:
            parameters['WALLCLOCK'] = parameters['WALLCLOCK_INI']
            parameters['NUMPROC'] = parameters['NUMPROC_INI']
            parameters['TASKTYPE'] = 'INITIALISATION'
        elif self.type == Type.LOCALSETUP:
            parameters['TASKTYPE'] = 'LOCAL SETUP'
        elif self.type == Type.REMOTESETUP:
            parameters['TASKTYPE'] = 'REMOTE SETUP'
            parameters['WALLCLOCK'] = parameters['WALLCLOCK_SETUP']
            parameters['NUMPROC'] = parameters['NUMPROC_SETUP']
        elif self.type == Type.TRANSFER:
            parameters['TASKTYPE'] = 'TRANSFER'
        else:
            print "Unknown Job Type"

        self.parameters = parameters

        return parameters

    def _get_remote_header(self):
        if self.parameters['HPCARCH'] == "bsc":
            remote_header = BscHeader
        elif self.parameters['HPCARCH'] == "ithaca":
            remote_header = ItHeader
        elif self.parameters['HPCARCH'] == "hector":
            remote_header = HtHeader
        elif self.parameters['HPCARCH'] == "archer":
            remote_header = ArHeader
        elif self.parameters['HPCARCH'] == "lindgren":
            remote_header = LgHeader
        elif self.parameters['HPCARCH'] == "ecmwf":
            remote_header = EcHeader
        elif self.parameters['HPCARCH'] == "marenostrum3":
            remote_header = MnHeader
        else:
            remote_header = None
        return remote_header

    def update_content(self, project_dir):
        local_header = PsHeader
        remote_header = self._get_remote_header()

        template = Template()
        if self.parameters['PROJECT_TYPE'].lower() != "none":
            dir_templates = project_dir

            local_setup = self.parameters['FILE_LOCALSETUP']

            if local_setup != '':
                template.read_localsetup_file(os.path.join(dir_templates, local_setup))

            remote_setup = self.parameters['FILE_REMOTESETUP']
            if remote_setup != '':
                template.read_localsetup_file(os.path.join(dir_templates, remote_setup))

            ini = self.parameters['FILE_INI']
            if ini != '':
                template.read_localsetup_file(os.path.join(dir_templates, ini))
            sim = self.parameters['FILE_SIM']
            if sim != '':
                template.read_localsetup_file(os.path.join(dir_templates, sim))

            post = self.parameters['FILE_POST']
            if post != '':
                template.read_localsetup_file(os.path.join(dir_templates, post))

            clean = self.parameters['FILE_CLEAN']
            if clean != '':
                template.read_localsetup_file(os.path.join(dir_templates, clean))

            trans = self.parameters['FILE_TRANS']
            if trans != '':
                template.read_localsetup_file(os.path.join(dir_templates, trans))

        if self.type == Type.SIMULATION:
            items = [remote_header.HEADER_SIM,
                     StatisticsSnippet.AS_HEADER_REM,
                     template.SIMULATION,
                     StatisticsSnippet.AS_TAILER_REM]
        elif self.type == Type.POSTPROCESSING:
            items = [remote_header.HEADER_POST,
                     StatisticsSnippet.AS_HEADER_REM,
                     template.POSTPROCESSING,
                     StatisticsSnippet.AS_TAILER_REM]
        elif self.type == Type.CLEANING:
            items = [remote_header.HEADER_CLEAN,
                     StatisticsSnippet.AS_HEADER_REM,
                     template.CLEANING,
                     StatisticsSnippet.AS_TAILER_REM]
        elif self.type == Type.INITIALISATION:
            items = [remote_header.HEADER_INI,
                     StatisticsSnippet.AS_HEADER_REM,
                     template.INITIALISATION,
                     StatisticsSnippet.AS_TAILER_REM]
        elif self.type == Type.LOCALSETUP:
            items = [local_header.HEADER_LOCALSETUP,
                     StatisticsSnippet.AS_HEADER_LOC,
                     template.LOCALSETUP,
                     StatisticsSnippet.AS_TAILER_LOC]
        elif self.type == Type.REMOTESETUP:
            items = [remote_header.HEADER_REMOTESETUP,
                     StatisticsSnippet.AS_HEADER_REM,
                     template.REMOTESETUP,
                     StatisticsSnippet.AS_TAILER_REM]
        elif self.type == Type.TRANSFER:
            items = [local_header.HEADER_LOCALTRANS,
                     StatisticsSnippet.AS_HEADER_LOC,
                     template.TRANSFER,
                     StatisticsSnippet.AS_TAILER_LOC]
        else:
            items = None
            print "Unknown Job Type"

        template_content = ''.join(items)
        return template_content

    def create_script(self, as_conf):
        parameters = self.update_parameters()
        template_content = self.update_content(as_conf.get_project_dir())
        # print "jobType: %s" % self._type
        # print template_content

        for key, value in parameters.items():
            # print "%s:\t%s" % (key,parameters[key])
            template_content = template_content.replace("%" + key + "%", parameters[key])

        scriptname = self.name + '.cmd'
        file(self._tmp_path + scriptname, 'w').write(template_content)

        return scriptname

    def check_script(self, as_conf):
        parameters = self.update_parameters()
        template_content = self.update_content(as_conf.get_project_dir())

        variables = re.findall('%' + '(\w+)' + '%', template_content)
        # variables += re.findall('%%'+'(.+?)'+'%%', template_content)
        out = set(parameters).issuperset(set(variables))

        if not out:
            print "The following set of variables to be substituted in template script is not part of parameters set: "
            print set(variables) - set(parameters)
        else:
            self.create_script(as_conf)

        return out


if __name__ == "__main__":
    mainJob = Job('uno', '1', Status.READY, 0)
    job1 = Job('uno', '1', Status.READY, 0)
    job2 = Job('dos', '2', Status.READY, 0)
    job3 = Job('tres', '3', Status.READY, 0)
    jobs = [job1, job2, job3]
    mainJob.parents = jobs
    print mainJob.parents
    # mainJob.set_children(jobs)
    job1.add_children(mainJob)
    job2.add_children(mainJob)
    job3.add_children(mainJob)
    print mainJob.get_all_children()
    print mainJob.children
    job3.check_completion()
    print "Number of Parents: ", mainJob.has_parents()
    print "number of children : ", mainJob.has_children()
    mainJob.print_job()
    mainJob.delete()
#
