import saga
import os
from autosubmit.config.basicConfig import BasicConfig
from autosubmit.job.job_common import Status


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
        self.queue = None
        self.serial_queue = None
        self._transfer = "sftp"

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
        out = saga.filesystem.File("file://{0}".format(os.path.join(self.tmp_path, filename)))
        if self.type == 'local':
            out.copy("file://{0}".format(os.path.join(self.tmp_path, 'LOG_'+self.expid, filename,)),
                     saga.filesystem.CREATE_PARENTS)
        else:
            sftp_directory = 'sftp://{0}{1}'.format(self.host, self.root_dir)
            workdir = saga.filesystem.Directory(sftp_directory,
                                                saga.filesystem.CREATE, session=self.service.session)
            out.copy(workdir.get_url())

    def get_file(self, filename):
        if self.type == 'local':
            out = saga.filesystem.File("file://{0}".format(os.path.join(self.tmp_path, 'LOG_'+self.expid,
                                                                        filename)))
        else:
            out = saga.filesystem.File("sftp://{0}{1}".format(self.host, os.path.join(self.root_dir, filename)))
        out.copy("file://{0}".format(os.path.join(self.tmp_path, filename)))

    def get_completed_files(self, job_name):
        self.get_file('{0}_COMPLETED'.format(job_name))

    def _get_files_path(self):
        if self.type == "local":
            path = os.path.join(self.root_dir, BasicConfig.LOCAL_TMP_DIR, 'LOG_{0}'.format(self.expid))
        else:
            path = self.root_dir
        return path

    def submit_job(self, job, scriptname):
        jd = saga.job.Description()
        jd.executable = os.path.join(self._get_files_path(), scriptname)
        jd.working_directory = self._get_files_path()
        jd.output = "{0}.out".format(job.name)
        jd.error = "{0}.err".format(job.name)
        self.add_atribute(jd, 'wall_time_limit', 5)

        self.add_atribute(jd, 'queue', job.parameters["CURRENT_QUEUE"])
        self.add_atribute(jd, 'project', job.parameters["CURRENT_BUDGET"])

        self.add_atribute(jd, 'total_cpu_count', int(job.parameters["PROCESSORS"]))
        self.add_atribute(jd, 'number_of_processes', 5)
        self.add_atribute(jd, 'processes_per_host', 5)
        self.add_atribute(jd, 'threads_per_process', 5)

        saga_job = self.service.create_job(jd)
        saga_job.run()
        return saga_job.id

    def add_atribute(self, jd, name, value):
        if self.service is None:
            return


    def check_job(self, id):
        if id not in self.service.jobs:
            return Status.COMPLETED
        saga_status = self.service.get_job(id).state
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




