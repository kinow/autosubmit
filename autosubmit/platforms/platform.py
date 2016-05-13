import subprocess
from time import sleep

import saga
import os
import datetime

from autosubmit.job.job_common import Status, Type
from autosubmit.config.log import Log
from autosubmit.date.chunk_date_lib import date2str


class Platform:
    """
    Class to manage the connections to the different platforms.
    """

    def __init__(self, expid, name, config):
        """

        :param config:
        :param expid:
        :param name:
        """
        self.expid = expid
        self.name = name
        self.config = config
        self.tmp_path = os.path.join(self.config.LOCAL_ROOT_DIR, self.expid, self.config.LOCAL_TMP_DIR)
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
        self.directory = None

    @property
    def serial_platform(self):
        """
        Platform to use for serial jobs
        :return: platform's object
        :rtype: platform
        """
        if self._serial_platform is None:
            return self
        return self._serial_platform

    @serial_platform.setter
    def serial_platform(self, value):
        self._serial_platform = value

    @property
    def queue(self):
        """
        Queue to use for jobs
        :return: queue's name
        :rtype: str
        """
        if self._default_queue is None:
            return ''
        return self._default_queue

    @queue.setter
    def queue(self, value):
        self._default_queue = value

    @property
    def serial_queue(self):
        """
        Queue to use for serial jobs
        :return: queue's name
        :rtype: str
        """
        if self._serial_queue is None:
            return self.queue
        return self._serial_queue

    @serial_queue.setter
    def serial_queue(self, value):
        self._serial_queue = value

    def add_parameters(self, parameters, main_hpc=False):
        """
        Add parameters for the current platform to the given parameters list

        :param parameters: parameters list to update
        :type parameters: dict
        :param main_hpc: if it's True, uses HPC instead of NAME_ as prefix for the parameters
        :type main_hpc: bool
        """
        if main_hpc:
            prefix = 'HPC'
            parameters['SCRATCH_DIR'.format(prefix)] = self.scratch
        else:
            prefix = self.name + '_'

        parameters['{0}ARCH'.format(prefix)] = self.name
        parameters['{0}HOST'.format(prefix)] = self.host
        parameters['{0}QUEUE'.format(prefix)] = self.queue
        parameters['{0}USER'.format(prefix)] = self.user
        parameters['{0}PROJ'.format(prefix)] = self.project
        parameters['{0}BUDG'.format(prefix)] = self.budget
        parameters['{0}TYPE'.format(prefix)] = self.type
        parameters['{0}SCRATCH_DIR'.format(prefix)] = self.scratch
        parameters['{0}ROOTDIR'.format(prefix)] = self.root_dir
        parameters['{0}LOGDIR'.format(prefix)] = self.get_files_path()

    def send_file(self, filename):
        """
        Sends a local file to the platform
        :param filename: name of the file to send
        :type filename: str
        """
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
        # noinspection PyTypeChecker
        out = saga.filesystem.File("file://{0}".format(os.path.join(self.tmp_path, filename)))
        if self.type == 'local':
            out.copy("file://{0}".format(os.path.join(self.tmp_path, 'LOG_' + self.expid, filename)),
                     saga.filesystem.CREATE_PARENTS)
        else:
            workdir = self.get_workdir(self.get_files_path())
            out.copy(workdir.get_url())
            workdir.close()
        out.close()

    def get_workdir(self, path):
        """
        Creates and returns a DIrectory object for the current workdir

        :param path: path to the workdir
        :type path: str
        :return: working directory object
        :rtype: saga.file.Directory
        """
        if not path:
            raise Exception("Workdir invalid")

        sftp_directory = 'sftp://{0}{1}'.format(self.host, path)
        try:
            # noinspection PyTypeChecker
            return saga.filesystem.Directory(sftp_directory, session=self.service.session)
        except saga.BadParameter:
            try:
                # noinspection PyTypeChecker
                return saga.filesystem.Directory(sftp_directory,
                                                 saga.filesystem.CREATE,
                                                 session=self.service.session)
            except saga.BadParameter:
                new_directory = os.path.split(path)[1]
                parent = self.get_workdir(os.path.dirname(path))
                parent.make_dir(new_directory)
                parent.close()
                # noinspection PyTypeChecker
                return saga.filesystem.Directory(sftp_directory, session=self.service.session)

    def get_file(self, filename, must_exist=True):
        """
        Copies a file from the current platform to experiment's tmp folder

        :param filename: file name
        :type filename: str
        :param must_exist: If True, raises an exception if file can not be copied
        :type must_exist: bool
        :return: True if file is copied succesfully, false otherwise
        :rtype: bool
        """
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

        if not self.exists_file(filename):
            if must_exist:
                raise Exception('File {0} does not exists'.format(filename))
            return False

        out = self.directory.open(os.path.join(str(self.directory.url), filename))

        out.copy("file://{0}".format(os.path.join(self.tmp_path, filename)))
        out.close()
        return True

    def exists_file(self, filename):
        """
        Checks if a file exists on this platform

        :param filename: file name
        :type filename: str
        :return: True if it exists, False otherwise
        """
        # noinspection PyBroadException
        if not self.directory:
            try:
                if self.type == 'local':
                    # noinspection PyTypeChecker
                    self.directory = saga.filesystem.Directory("file://{0}".format(os.path.join(self.tmp_path,
                                                                                                'LOG_' + self.expid)))
                else:
                    # noinspection PyTypeChecker
                    self.directory = saga.filesystem.Directory("sftp://{0}{1}".format(self.host, self.get_files_path()))
            except:
                return False

        # noinspection PyBroadException
        try:
            self.directory.list(filename)
        except:
            return False

        return True

    def delete_file(self, filename):
        """
        Deletes a file from this platform

        :param filename: file name
        :type filename: str
        :return: True if succesful or file does no exists
        :rtype: bool
        """
        if self.type == 'ecaccess':
            try:
                subprocess.check_call(['ecaccess-file-delete',
                                       '{0}:{1}'.format(self.host, os.path.join(self.get_files_path(), filename))])
                return True
            except subprocess.CalledProcessError:
                return True

        if not self.exists_file(filename):
            return True

        try:
            if self.type == 'local':
                # noinspection PyTypeChecker
                out = saga.filesystem.File("file://{0}".format(os.path.join(self.tmp_path, 'LOG_' + self.expid,
                                                                            filename)))
            else:
                # noinspection PyTypeChecker
                out = saga.filesystem.File("sftp://{0}{1}".format(self.host, os.path.join(self.get_files_path(),
                                                                                          filename)))
            out.remove()
            out.close()
            return True
        except saga.DoesNotExist:
            return True

    def get_completed_files(self, job_name, retries=1):
        """
        Get the COMPLETED file of the given job


        :param job_name: name of the job
        :type job_name: str
        :param retries: Max number of tries to get the file
        :type retries: int
        :return: True if successful, false otherwise
        :rtype: bool
        """
        while True:
            if self.get_file('{0}_COMPLETED'.format(job_name), False):
                return True
            if retries == 0:
                return False
            retries -= 1
            sleep(5)

    def remove_stat_file(self, jobname):
        """
        Removes *STAT* files from remote

        :param jobname: name of job to check
        :type jobname: str
        :return: True if succesful, False otherwise
        :rtype: bool
        """
        filename = jobname + '_STAT'
        if self.delete_file(filename):
            Log.debug('{0}_STAT have been removed', jobname)
            return True
        return False

    def remove_completed_file(self, jobname):
        """
        Removes *COMPLETED* files from remote

        :param jobname: name of job to check
        :type jobname: str
        :return: True if succesful, False otherwise
        :rtype: bool
        """
        filename = jobname + '_COMPLETED'
        if self.delete_file(filename):
            Log.debug('{0} been removed', filename)
            return True
        return False

    def get_stat_file(self, jobname, retries=1):
        """
        Copies *STAT* files from remote to local

        :param retries: number of intents to get the completed files
        :type retries: int
        :param jobname: name of job to check
        :type jobname: str
        :return: True if succesful, False otherwise
        :rtype: bool
        """
        filename = jobname + '_STAT'
        stat_local_path = os.path.join(self.config.LOCAL_ROOT_DIR, self.expid, self.config.LOCAL_TMP_DIR, filename)
        if os.path.exists(stat_local_path):
            os.remove(stat_local_path)

        while True:
            if self.get_file(filename, False):
                Log.debug('{0}_STAT file have been transfered', jobname)
                return True
            if retries == 0:
                break
            retries -= 1
            # wait five seconds to check get file
            sleep(5)

        Log.debug('Something did not work well when transferring the STAT file')
        return False

    def get_files_path(self):
        """
        Get the path to the platform's LOG directory

        :return: platform's LOG directory
        :rtype: str
        """
        if self.type == "local":
            path = os.path.join(self.root_dir, self.config.LOCAL_TMP_DIR, 'LOG_{0}'.format(self.expid))
        else:
            path = os.path.join(self.root_dir, 'LOG_{0}'.format(self.expid))
        return path

    def create_saga_job(self, job, scriptname):
        """
        Creates a saga job from a given job object.

        :param job: job object
        :type job: autosubmit.job.job.Job
        :param scriptname: job script's name
        :rtype scriptname: str
        :return: saga job object for the given job
        :rtype: saga.job.Job
        """
        jd = saga.job.Description()
        if job.type == Type.BASH:
            binary = 'source'
        elif job.type == Type.PYTHON:
            binary = 'python '
        elif job.type == Type.R:
            binary = 'Rscript'

        #jd.executable = '{0} {1}'.format(binary, os.path.join(self.get_files_path(), scriptname))
        jd.executable = os.path.join(self.get_files_path(), scriptname)
        jd.working_directory = self.get_files_path()
        str_datetime = date2str(datetime.datetime.now(), 'S')
        jd.output = "{0}.{1}.out".format(job.name, str_datetime)
        jd.error = "{0}.{1}.err".format(job.name, str_datetime)
        self.add_attribute(jd, 'Name', job.name)

        wallclock = job.parameters["WALLCLOCK"]
        if wallclock == '':
            wallclock = 0
        else:
            wallclock = wallclock.split(':')
            wallclock = int(wallclock[0]) * 60 + int(wallclock[1])
        self.add_attribute(jd, 'WallTimeLimit', wallclock)

        self.add_attribute(jd, 'Queue', job.parameters["CURRENT_QUEUE"])
        self.add_attribute(jd, 'Project', job.parameters["CURRENT_BUDG"])

        self.add_attribute(jd, 'TotalCPUCount', job.parameters["NUMPROC"])
        self.add_attribute(jd, 'ProcessesPerHost', job.parameters["NUMTASK"])
        self.add_attribute(jd, 'ThreadsPerProcess', job.parameters["NUMTHREADS"])

        self.add_attribute(jd, 'TotalPhysicalMemory', job.parameters["MEMORY"])

        saga_job = self.service.create_job(jd)
        return saga_job

    def add_attribute(self, jd, name, value):
        """
        Adds an attribute to a given job descriptor, only if it is supported by the adaptor.

        :param jd: job descriptor to use:
        :type jd: saga.job.Descriptor
        :param name: attribute's name
        :type name: str
        :param value: attribute's value
        """
        if self._attributes is None:
            # noinspection PyProtectedMember
            self._attributes = self.service._adaptor._adaptor._info['capabilities']['jdes_attributes']
        if name not in self._attributes or not value:
            return
        jd.set_attribute(name, value)

    def check_job(self, jobid, default_status=Status.COMPLETED, retries=30):
        """
        Checks job running status

        :param retries: retries
        :param jobid: job id
        :type jobid: str
        :param default_status: status to assign if it can be retrieved from the platform
        :type default_status: autosubmit.job.job_common.Status
        :return: current job status
        :rtype: autosubmit.job.job_common.Status
        """
        if jobid not in self.service.jobs:
            return Status.COMPLETED
        # noinspection PyBroadException
        saga_status = None
        while saga_status is None and retries > 0:
            try:
                saga_status = self.service.get_job(jobid).state
            except Exception as e:
                # If SAGA can not get the job state, we change it to completed
                # It will change to FAILED if not COMPLETED file is present
                Log.debug('Can not get job state: {0}', e)
                retries -= 1
                sleep(5)

        if saga_status is None:
            return default_status
        elif saga_status == saga.job.UNKNOWN:
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
