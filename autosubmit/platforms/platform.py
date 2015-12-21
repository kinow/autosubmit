import subprocess

import saga
import os

from autosubmit.config.basicConfig import BasicConfig
from autosubmit.job.job_common import Status
# noinspection PyPackageRequirements
from config.log import Log


class Platform:
    def __init__(self, expid, name):
        """

        :param expid:
        :param name:
        """
        self.expid = expid
        self.name = name
        self.tmp_path = os.path.join(BasicConfig.LOCAL_ROOT_DIR, self.expid, BasicConfig.LOCAL_TMP_DIR)
        self._serial_platform = None
        self._queue = None
        self._serial_queue = None
        self._transfer = "sftp"
        self._attributes = None
        self.host = ''
        self.user = ''
        self.project = ''
        self.budget = ''
        self.type = ''
        self.scratch = ''
        self.root_dir = ''
        self.service = None
        self.scheduler = None

    @property
    def serial_platform(self):
        if self._serial_platform is None:
            return self
        return self._serial_platform

    @serial_platform.setter
    def serial_platform(self, value):
        self._serial_platform = value

    @property
    def queue(self):
        if self._default_queue is None:
            return ''
        return self._default_queue

    @queue.setter
    def queue(self, value):
        self._default_queue = value

    @property
    def serial_queue(self):
        if self._serial_queue is None:
            return self.queue
        return self._serial_queue

    @serial_queue.setter
    def serial_queue(self, value):
        self._serial_queue = value

    @property
    def transfer(self):
        if self._transfer == 'file':
            return "file://"
        return '{0}://{1}'.format(self._transfer, self.host)

    @transfer.setter
    def transfer(self, value):
        pass

    def add_parameters(self, parameters, main_hpc=False):

        if main_hpc:
            prefix = 'HPC'
            parameters['SCRATCH_DIR'.format(prefix)] = self.scratch
        else:
            prefix = self.name + '_'

        parameters['{0}ARCH'.format(prefix)] = self.name
        parameters['{0}USER'.format(prefix)] = self.user
        parameters['{0}PROJ'.format(prefix)] = self.project
        parameters['{0}BUDG'.format(prefix)] = self.budget
        parameters['{0}TYPE'.format(prefix)] = self.type
        parameters['{0}SCRATCH_DIR'.format(prefix)] = self.scratch
        parameters['{0}ROOTDIR'.format(prefix)] = self.root_dir

    def send_file(self, filename):
        if self.type == 'ecaccess':
            try:
                subprocess.check_call(['ecaccess-file-mkdir', '{0}:{1}'.format(self.host, self.root_dir)])
                subprocess.check_call(['ecaccess-file-mkdir', '{0}:{1}'.format(self.host, self.get_files_path())])
                destiny_path = os.path.join(self.get_files_path(), filename)
                subprocess.check_call(['ecaccess-file-put', os.path.join(self.tmp_path, filename),
                                       '{0}:{1}'.format(self.host, destiny_path)])
                subprocess.check_call(['ecaccess-file-chmod', '740', '{0}:{1}'.format(self.host, destiny_path)])
                return
            except subprocess.CalledProcessError:
                raise Exception("Could't send file {0} to {1}:{2}".format(os.path.join(self.tmp_path, filename),
                                                                          self.host, self.get_files_path()))
        out = saga.filesystem.File("file://{0}".format(os.path.join(self.tmp_path, filename)))
        if self.type == 'local':
            out.copy("file://{0}".format(os.path.join(self.tmp_path, 'LOG_' + self.expid, filename,)),
                     saga.filesystem.CREATE_PARENTS)
        else:
            workdir = self.get_workdir(self.get_files_path())
            out.copy(workdir.get_url())
        del out

    def get_workdir(self, path):
        if not path:
            raise Exception("Workdir invalid")

        sftp_directory = 'sftp://{0}{1}'.format(self.host, path)
        try:
            return saga.filesystem.Directory(sftp_directory, session=self.service.session)
        except saga.BadParameter as ex:
            try:
                return saga.filesystem.Directory(sftp_directory,
                                                 saga.filesystem.CREATE, session=self.service.session)
            except saga.BadParameter as ex:
                new_directory = os.path.split(path)[1]
                parent = self.get_workdir(os.path.dirname(path))
                parent.make_dir(new_directory)
                return saga.filesystem.Directory(sftp_directory, session=self.service.session)

    def get_file(self, filename, must_exist=True):
        if self.type == 'ecaccess':
            try:
                subprocess.check_call(['ecaccess-file-get', '{0}:{1}'.format(self.host,
                                                                             os.path.join(self.get_files_path(),
                                                                                          filename)),
                                       os.path.join(self.tmp_path, filename)])
                return True
            except subprocess.CalledProcessError:
                if must_exist:
                    raise Exception("Could't get file {0} from {1}:{2}".format(os.path.join(self.tmp_path, filename),
                                                                               self.host, self.get_files_path()))
                return False
        try:
            if self.type == 'local':
                out = saga.filesystem.File("file://{0}".format(os.path.join(self.tmp_path, 'LOG_' + self.expid,
                                                                            filename)))
            else:
                out = saga.filesystem.File("sftp://{0}{1}".format(self.host, os.path.join(self.get_files_path(),
                                                                                          filename)))
            out.copy("file://{0}".format(os.path.join(self.tmp_path, filename)))
            del out
            return True
        except saga.DoesNotExist as ex:
            if must_exist:
                raise ex
            return False

    def get_completed_files(self, job_name):
        return self.get_file('{0}_COMPLETED'.format(job_name), False)

    def get_files_path(self):
        if self.type == "local":
            path = os.path.join(self.root_dir, BasicConfig.LOCAL_TMP_DIR, 'LOG_{0}'.format(self.expid))
        else:
            path = os.path.join(self.root_dir, 'LOG_{0}'.format(self.expid))
        return path

    def create_saga_job(self, job, scriptname):
        """

        :param job:
        :param scriptname:
        :return:
        :rtype: saga.job.Job
        """
        jd = saga.job.Description()
        jd.executable = os.path.join(self.get_files_path(), scriptname)
        jd.working_directory = self.get_files_path()
        jd.output = "{0}.out".format(job.name)
        jd.error = "{0}.err".format(job.name)
        self.add_atribute(jd, 'Name', job.name)

        wallclock = job.parameters["WALLCLOCK"]
        if wallclock == '':
            wallclock = 0
        else:
            wallclock = wallclock.split(':')
            wallclock = int(wallclock[0]) * 60 + int(wallclock[1])
        self.add_atribute(jd, 'WallTimeLimit', wallclock)

        self.add_atribute(jd, 'Queue', job.parameters["CURRENT_QUEUE"])
        self.add_atribute(jd, 'Project', job.parameters["CURRENT_BUDG"])

        self.add_atribute(jd, 'TotalCpuCount', job.parameters["NUMPROC"])
        self.add_atribute(jd, 'ProcessesPerHost', job.parameters["NUMTASK"])
        self.add_atribute(jd, 'ThreadsPerProcess', job.parameters["NUMTHREADS"])

        self.add_atribute(jd, 'TotalPhysicalMemory', job.parameters["MEMORY"])

        saga_job = self.service.create_job(jd)
        return saga_job

    def add_atribute(self, jd, name, value):
        if self._attributes is None:
            # noinspection PyProtectedMember
            self._attributes = self.service._adaptor._adaptor._info['capabilities']['jdes_attributes']
        if name not in self._attributes or not value:
            return
        jd.set_attribute(name, value)

    def check_job(self, jobid, default_status=Status.COMPLETED):
        if jobid not in self.service.jobs:
            return Status.COMPLETED
        # noinspection PyBroadException
        try:
            saga_status = self.service.get_job(jobid).state
        except Exception as e:
            # If SAGA can not get the job state, we change it to completed
            # It will change to FAILED if not COMPLETED file is present
            Log.debug('Can not get job state: {0}', e)
            return default_status

        if saga_status == saga.job.UNKNOWN:
            return Status.UNKNOWN
        elif saga_status == saga.job.PENDING:
            return Status.QUEUING
        elif saga_status == saga.job.FAILED:
            return Status.FAILED
        elif saga_status == saga.job.CANCELED:
            return Status.FAILED
        elif saga_status == saga.job.DONE:
            return Status.COMPLETED
        elif saga_status == saga.job.RUNNING:
            return Status.RUNNING
        elif saga_status == saga.job.SUSPENDED:
            return Status.SUSPENDED
