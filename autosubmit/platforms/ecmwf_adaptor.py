""" LSF mn adaptor implementation
"""

import re
import os
import time
import threading

# noinspection PyPackageRequirements
import radical.utils.threads as sut
import saga.url as surl
import saga.utils.pty_shell
import saga.adaptors.base
import saga.adaptors.cpi.job
import saga.adaptors.loadl.loadljob
import saga.adaptors.pbs.pbsjob

SYNC_CALL = saga.adaptors.cpi.decorators.SYNC_CALL
ASYNC_CALL = saga.adaptors.cpi.decorators.ASYNC_CALL

SYNC_WAIT_UPDATE_INTERVAL = 1  # seconds
MONITOR_UPDATE_INTERVAL = 3  # seconds


# --------------------------------------------------------------------
#
# noinspection PyProtectedMember,PyPep8Naming
class _job_state_monitor(threading.Thread):
    """ thread that periodically monitors job states
    """

    def __init__(self, job_service):

        self.logger = job_service._logger
        self.js = job_service
        self._stop = sut.Event()

        super(_job_state_monitor, self).__init__()
        self.setDaemon(True)

    def stop(self):
        self._stop.set()

    def stopped(self):
        return self._stop.isSet()

    def run(self):
        while self.stopped() is False:
            try:
                # do bulk updates here! we don't want to pull information
                # job by job. that would be too inefficient!
                jobs = self.js.jobs
                job_keys = jobs.keys()

                for job in job_keys:
                    # if the job hasn't been started, we can't update its
                    # state. we can tell if a job has been started if it
                    # has a job id
                    if jobs[job].get('job_id', None) is not None:
                        # we only need to monitor jobs that are not in a
                        # terminal state, so we can skip the ones that are
                        # either done, failed or canceled
                        state = jobs[job]['state']
                        if (state != saga.job.DONE) and (state != saga.job.FAILED) and (state != saga.job.CANCELED):

                            job_info = self.js._job_get_info(job)
                            self.logger.info(
                                "Job monitoring thread updating Job %s (state: %s)" % (job, job_info['state']))

                            if job_info['state'] != jobs[job]['state']:
                                # fire job state callback if 'state' has changed
                                job._api()._attributes_i_set('state', job_info['state'], job._api()._UP, True)

                            # update job info
                            self.js.jobs[job] = job_info

                time.sleep(MONITOR_UPDATE_INTERVAL)
            except Exception as e:
                self.logger.warning("Exception caught in job monitoring thread: %s" % e)


# --------------------------------------------------------------------
#
def log_error_and_raise(message, exception, logger):
    """ loggs an 'error' message and subsequently throws an exception
    """
    logger.error(message)
    raise exception(message)


# --------------------------------------------------------------------
#
def _ecaccess_to_saga_jobstate(ecaccess_state):
    """ translates a mn one-letter state to saga
    """
    if ecaccess_state in ['EXEC']:
        return saga.job.RUNNING
    elif ecaccess_state in ['INIT', 'RETR', 'STDBY', 'WAIT']:
        return saga.job.PENDING
    elif ecaccess_state in ['DONE']:
        return saga.job.DONE
    elif ecaccess_state in ['STOP']:
        return saga.job.FAILED
    elif ecaccess_state in ['USUSP', 'SSUSP', 'PSUSP']:
        return saga.job.SUSPENDED
    else:
        return saga.job.UNKNOWN

_PTY_TIMEOUT = 2.0

# --------------------------------------------------------------------
# the adaptor name
#
_ADAPTOR_NAME = "autosubmit.platforms.ecmwf_adaptor"
_ADAPTOR_SCHEMAS = ["ecmwf"]
_ADAPTOR_OPTIONS       = [
    {
    'category'         : 'saga.adaptor.loadljob',
    'name'             : 'scheduler',
    'type'             : str,
    'default'          : 'pbs',
    'valid_options'    : ['pbs', 'load'],
    'documentation'    : '''Specifies the scheduler that uses the target machine. Can be PBS or LoadLeveler.''',
    'env_variable'     : None
    },
]

# --------------------------------------------------------------------
# the adaptor capabilities & supported attributes
#
_ADAPTOR_CAPABILITIES = {
    "jdes_attributes": [saga.job.NAME,
                        saga.job.EXECUTABLE,
                        saga.job.ARGUMENTS,
                        saga.job.ENVIRONMENT,
                        saga.job.INPUT,
                        saga.job.OUTPUT,
                        saga.job.ERROR,
                        saga.job.QUEUE,
                        saga.job.PROJECT,
                        saga.job.WALL_TIME_LIMIT,
                        saga.job.WORKING_DIRECTORY,
                        saga.job.SPMD_VARIATION,  # TODO: 'hot'-fix for BigJob
                        saga.job.TOTAL_CPU_COUNT],
    "job_attributes": [saga.job.EXIT_CODE,
                       saga.job.EXECUTION_HOSTS,
                       saga.job.CREATED,
                       saga.job.STARTED,
                       saga.job.FINISHED],
    "metrics": [saga.job.STATE],
    "callbacks": [saga.job.STATE],
    "contexts": {"ssh": "SSH public/private keypair",
                 "x509": "GSISSH X509 proxy context",
                 "userpass": "username/password pair (ssh)"}
}

# --------------------------------------------------------------------
# the adaptor documentation
#
_ADAPTOR_DOC = {
    "name": _ADAPTOR_NAME,
    "cfg_options": _ADAPTOR_OPTIONS,
    "capabilities": _ADAPTOR_CAPABILITIES,
    "description": """
The ecmwf adaptor allows to run and manage jobs on ECMWF machines
""",
    "schemas": {"ecmwf": "connect usig ecaccess tools"}
}

# --------------------------------------------------------------------
# the adaptor info is used to register the adaptor with SAGA
#
_ADAPTOR_INFO = {
    "name": _ADAPTOR_NAME,
    "version": "v0.1",
    "schemas": _ADAPTOR_SCHEMAS,
    "capabilities": _ADAPTOR_CAPABILITIES,
    "cpis": [
        {
            "type": "saga.job.Service",
            "class": "ECMWFJobService"
        },
        {
            "type": "saga.job.Job",
            "class": "ECMWFJob"
        }
    ]
}


###############################################################################
# The adaptor class
class Adaptor(saga.adaptors.base.Base):
    """ this is the actual adaptor class, which gets loaded by SAGA (i.e. by
        the SAGA engine), and which registers the CPI implementation classes
        which provide the adaptor's functionality.
    """

    # ----------------------------------------------------------------
    #
    def __init__(self):
        saga.adaptors.base.Base.__init__(self, _ADAPTOR_INFO, _ADAPTOR_OPTIONS)

        self.id_re = re.compile('^\[(.*)\]-\[(.*?)\]$')
        self.opts = self.get_config(_ADAPTOR_NAME)
        self.scheduler = self.opts['scheduler'].get_value()

    # ----------------------------------------------------------------
    #
    def sanity_check(self):
        # FIXME: also check for gsissh
        pass

    # ----------------------------------------------------------------
    #
    def parse_id(self, job_id):
        # split the id '[rm]-[pid]' in its parts, and return them.

        match = self.id_re.match(job_id)

        if not match or len(match.groups()) != 2:
            raise saga.BadParameter("Cannot parse job id '%s'" % job_id)

        return match.group(1), match.group(2)


###############################################################################
#
# noinspection PyMethodOverriding,PyMethodOverriding,PyProtectedMember
class ECMWFJobService(saga.adaptors.cpi.job.Service):
    """ implements saga.adaptors.cpi.job.Service
    """

    # ----------------------------------------------------------------
    #
    # noinspection PyMissingConstructor
    def __init__(self, api, adaptor):

        self._mt = None
        _cpi_base = super(ECMWFJobService, self)
        _cpi_base.__init__(api, adaptor)

        self._adaptor = adaptor

    # ----------------------------------------------------------------
    #
    def __del__(self):

        self.close()

    # ----------------------------------------------------------------
    #
    def close(self):

        if self.mt:
            self.mt.stop()
            self.mt.join(10)  # don't block forever on join()

        self._logger.info("Job monitoring thread stopped.")

        self.finalize(True)

    # ----------------------------------------------------------------
    #
    def finalize(self, kill_shell=False):

        if kill_shell:
            if self.shell:
                self.shell.finalize(True)

    # ----------------------------------------------------------------
    #
    @SYNC_CALL
    def init_instance(self, adaptor_state, rm_url, session):
        """ service instance constructor
        """
        self.rm = rm_url
        self.session = session
        self.ppn = 1
        self.queue = None
        self.shell = None
        self.jobs = dict()

        # the monitoring thread - one per service instance
        self.mt = _job_state_monitor(job_service=self)
        self.mt.start()

        rm_scheme = rm_url.scheme
        pty_url = surl.Url(rm_url)

        # we need to extrac the scheme for PTYShell. That's basically the
        # job.Serivce Url withou the mn+ part. We use the PTYShell to execute
        # mn commands either locally or via gsissh or ssh.
        if rm_scheme == "ecmwf":
            pty_url.scheme = "fork"

        self.shell = saga.utils.pty_shell.PTYShell(pty_url, self.session)

        self.initialize()
        return self.get_api()

    # ----------------------------------------------------------------
    #
    def initialize(self):
        ret, out, _ = self.shell.run_sync("which ecaccess -version")
        if ret == 0:
            self._logger.info("Found ECMWF tools. Version: {0}".format(out))

    def _job_run(self, job_obj):
        """ runs a job via qsub
        """
        # get the job description
        jd = job_obj.jd

        # normalize working directory path
        if jd.working_directory:
            jd.working_directory = os.path.normpath(jd.working_directory)

        if (self.queue is not None) and (jd.queue is not None):
            self._logger.warning("Job service was instantiated explicitly with 'queue=%s', but job description tries to"
                                 " a differnt queue: '%s'. Using '%s'." % (self.queue, jd.queue, self.queue))

        try:
            # create an LSF job script from SAGA job description
            if self._adaptor.scheduler == 'load':
                script = saga.adaptors.loadl.loadljob.LOADLJobService.__generate_llsubmit_script(jd)
            else:
                script = saga.adaptors.pbs.pbsjob._pbscript_generator("", self._logger, jd, self.ppn, None,
                                                                      self.scheduler_version)
            self._logger.info("Generated ECMWF script: %s" % script)
        except Exception, ex:
            script = ''
            log_error_and_raise(str(ex), saga.BadParameter, self._logger)

        # try to create the working directory (if defined)
        # WARNING: this assumes a shared filesystem between login node and
        #          compute nodes.
        if jd.working_directory is not None:
            self._logger.info("Creating working directory %s" % jd.working_directory)
            ret, out, _ = self.shell.run_sync("ecaccess-file-mkdir -p %s" % jd.working_directory)
            if ret != 0:
                # something went wrong
                message = "Couldn't create working directory - %s" % out
                log_error_and_raise(message, saga.NoSuccess, self._logger)

        # Now we want to execute the script. This process consists of two steps:
        # (1) we create a temporary file with 'mktemp' and write the contents of
        #     the generated PBS script into it
        # (2) we call 'qsub <tmpfile>' to submit the script to the queueing system
        cmdline = 'SCRIPTFILE=`mktemp -t SAGA-Python-LSFJobScript.XXXXXX` && ' \
                  'echo "{0}" > $SCRIPTFILE && ' \
                  '{1} < $SCRIPTFILE && ' \
                  'rm -f $SCRIPTFILE'.format(script, 'ecaccess-job-submit')
        ret, out, _ = self.shell.run_sync(cmdline)

        if ret != 0:
            # something went wrong
            message = "Error running job via 'ecaccess-job-submit': %s. Commandline was: %s" \
                      % (out, cmdline)
            log_error_and_raise(message, saga.NoSuccess, self._logger)
        else:
            # parse the job id. bsub's output looks like this:
            # Job <901545> is submitted to queue <regular>
            lines = out.split("\n")
            lines = filter(lambda l: l != '', lines)  # remove empty

            self._logger.info('bsub: %s' % ''.join(lines))

            mn_job_id = None
            for line in lines:
                if re.search('Job <.+> is submitted to queue', line):
                    mn_job_id = re.findall(r'<(.*?)>', line)[0]
                    break

            if not mn_job_id:
                raise Exception("Failed to detect job id after submission.")

            job_id = "[%s]-[%s]" % (self.rm, mn_job_id)

            self._logger.info("Submitted LSF job with id: %s" % job_id)

            # update job dictionary
            self.jobs[job_obj]['job_id'] = job_id
            self.jobs[job_obj]['submitted'] = job_id

            # set status to 'pending' and manually trigger callback
            # self.jobs[job_obj]['state'] = saga.job.PENDING
            # job_obj._api()._attributes_i_set('state', self.jobs[job_obj]['state'], job_obj._api()._UP, True)

            # return the job id
            return job_id

    # ----------------------------------------------------------------
    #
    def _retrieve_job(self, job_id):
        """ see if we can get some info about a job that we don't
            know anything about
        """
        rm, pid = self._adaptor.parse_id(job_id)

        ret, out, _ = self.shell.run_sync(
            "%s -noheader -o 'stat exec_host exit_code submit_time start_time finish_time delimiter=\",\"' %s" % ('bjobs', pid))

        if ret != 0:
            message = "Couldn't reconnect to job '%s': %s" % (job_id, out)
            log_error_and_raise(message, saga.NoSuccess, self._logger)

        else:
            # the job seems to exist on the backend. let's gather some data
            job_info = {
                'state': saga.job.UNKNOWN,
                'exec_hosts': None,
                'returncode': None,
                'create_time': None,
                'start_time': None,
                'end_time': None,
                'gone': False
            }

            results = out.split(',')
            job_info['state'] = _ecaccess_to_saga_jobstate(results[0])
            job_info['exec_hosts'] = results[1]
            if results[2] != '-':
                job_info['returncode'] = int(results[2])
            job_info['create_time'] = results[3]
            job_info['start_time'] = results[4]
            job_info['end_time'] = results[5]

            return job_info

    # ----------------------------------------------------------------
    #
    def _job_get_info(self, job_obj):
        """ get job attributes via bjob
        """

        # if we don't have the job in our dictionary, we don't want it
        if job_obj not in self.jobs:
            message = "Unknown job object: %s. Can't update state." % job_obj._id
            log_error_and_raise(message, saga.NoSuccess, self._logger)

        # prev. info contains the info collect when _job_get_info
        # was called the last time
        prev_info = self.jobs[job_obj]

        # if the 'gone' flag is set, there's no need to query the job
        # state again. it's gone forever
        if prev_info['gone'] is True:
            return prev_info

        # curr. info will contain the new job info collect. it starts off
        # as a copy of prev_info (don't use deepcopy because there is an API
        # object in the dict -> recursion)
        curr_info = dict()
        curr_info['job_id'] = prev_info.get('job_id')
        curr_info['state'] = prev_info.get('state')
        curr_info['exec_hosts'] = prev_info.get('exec_hosts')
        curr_info['returncode'] = prev_info.get('returncode')
        curr_info['create_time'] = prev_info.get('create_time')
        curr_info['start_time'] = prev_info.get('start_time')
        curr_info['end_time'] = prev_info.get('end_time')
        curr_info['gone'] = prev_info.get('gone')

        rm, pid = self._adaptor.parse_id(job_obj._id)

        # run the 'ecaccess-job-list' command to get some infos about our job
        # the result of ecaccess-job-list <id> looks like this:
        #
        # JOBID   USER    STAT  QUEUE      FROM_HOST   EXEC_HOST   JOB_NAME   SUBMIT_TIME
        # 901545  oweidne DONE  regular    yslogin5-ib ys3833-ib   *FILENAME  Nov 11 12:06
        #
        ret, out, _ = self.shell.run_sync('ecaccess-job-list {0}'.format(pid))

        if ret != 0:
            if "Illegal job ID" in out:
                # Let's see if the previous job state was running or pending. in
                # that case, the job is gone now, which can either mean DONE,
                # or FAILED. the only thing we can do is set it to 'DONE'
                curr_info['gone'] = True
                # we can also set the end time
                self._logger.warning(
                    "Previously running job has disappeared. This probably means that the backend doesn't store informations about finished jobs. Setting state to 'DONE'.")

                if prev_info['state'] in [saga.job.RUNNING, saga.job.PENDING]:
                    curr_info['state'] = saga.job.DONE
                else:
                    curr_info['state'] = saga.job.FAILED
            else:
                # something went wrong
                message = "Error retrieving job info via 'ecaccess-job-list ': %s" % out
                log_error_and_raise(message, saga.NoSuccess, self._logger)
        else:
            # parse the result
            results = out.split()
            curr_info['state'] = _ecaccess_to_saga_jobstate(results[2])
            curr_info['exec_hosts'] = results[5]

        # return the new job info dict
        return curr_info

    # ----------------------------------------------------------------
    #
    def _job_get_state(self, job_obj):
        """ get the job's state
        """
        return self.jobs[job_obj]['state']

    # ----------------------------------------------------------------
    #
    def _job_get_exit_code(self, job_obj):
        """ get the job's exit code
        """
        ret = self.jobs[job_obj]['returncode']

        # FIXME: 'None' should cause an exception
        if ret is None:
            return None
        else:
            return int(ret)

    # ----------------------------------------------------------------
    #
    def _job_get_execution_hosts(self, job_obj):
        """ get the job's exit code
        """
        return self.jobs[job_obj]['exec_hosts']

    # ----------------------------------------------------------------
    #
    def _job_get_create_time(self, job_obj):
        """ get the job's creation time
        """
        return self.jobs[job_obj]['create_time']

    # ----------------------------------------------------------------
    #
    def _job_get_start_time(self, job_obj):
        """ get the job's start time
        """
        return self.jobs[job_obj]['start_time']

    # ----------------------------------------------------------------
    #
    def _job_get_end_time(self, job_obj):
        """ get the job's end time
        """
        return self.jobs[job_obj]['end_time']

    # ----------------------------------------------------------------
    #
    def _job_cancel(self, job_obj):
        """ cancel the job via 'qdel'
        """
        rm, pid = self._adaptor.parse_id(job_obj._id)

        ret, out, _ = self.shell.run_sync('ecaccess-job-delete {0}'.format(pid))

        if ret != 0:
            message = "Error canceling job via 'ecaccess-job-delete': %s" % out
            log_error_and_raise(message, saga.NoSuccess, self._logger)

        # assume the job was succesfully canceled
        self.jobs[job_obj]['state'] = saga.job.CANCELED

    # ----------------------------------------------------------------
    #
    def _job_wait(self, job_obj, timeout):
        """ wait for the job to finish or fail
        """
        time_start = time.time()
        self._adaptor.parse_id(job_obj._id)

        while True:
            state = self.jobs[job_obj]['state']  # this gets updated in the bg.

            if state == saga.job.DONE or state == saga.job.FAILED or state == saga.job.CANCELED:
                return True

            # avoid busy poll
            time.sleep(SYNC_WAIT_UPDATE_INTERVAL)

            # check if we hit timeout
            if timeout >= 0:
                time_now = time.time()
                if time_now - time_start > timeout:
                    return False

    # ----------------------------------------------------------------
    #
    @SYNC_CALL
    def create_job(self, jd):
        """ implements saga.adaptors.cpi.job.Service.get_url()
        """
        # this dict is passed on to the job adaptor class -- use it to pass any
        # state information you need there.
        adaptor_state = {"job_service": self,
                         "job_description": jd,
                         "job_schema": self.rm.schema,
                         "reconnect": False
                         }

        # create a new job object
        job_obj = saga.job.Job(_adaptor=self._adaptor,
                               _adaptor_state=adaptor_state)

        # add job to internal list of known jobs.
        self.jobs[job_obj._adaptor] = {
            'state': saga.job.NEW,
            'job_id': None,
            'exec_hosts': None,
            'returncode': None,
            'create_time': None,
            'start_time': None,
            'end_time': None,
            'gone': False,
            'submitted': False
        }

        return job_obj

    # ----------------------------------------------------------------
    #
    @SYNC_CALL
    def get_job(self, jobid):
        """ Implements saga.adaptors.cpi.job.Service.get_job()
        """

        # try to get some information about this job
        job_info = self._retrieve_job(jobid)

        # this dict is passed on to the job adaptor class -- use it to pass any
        # state information you need there.
        adaptor_state = {"job_service": self,
                         # TODO: fill job description
                         "job_description": saga.job.Description(),
                         "job_schema": self.rm.schema,
                         "reconnect": True,
                         "reconnect_jobid": jobid
                         }

        job = saga.job.Job(_adaptor=self._adaptor,
                           _adaptor_state=adaptor_state)

        # throw it into our job dictionary.
        self.jobs[job._adaptor] = job_info
        return job

    # ----------------------------------------------------------------
    #
    @SYNC_CALL
    def get_url(self):
        """ implements saga.adaptors.cpi.job.Service.get_url()
        """
        return self.rm

    # ----------------------------------------------------------------
    #
    @SYNC_CALL
    def list(self):
        """ implements saga.adaptors.cpi.job.Service.list()
        """
        ids = []

        ret, out, _ = self.shell.run_sync("ecaccess-job-list")

        if ret != 0 and len(out) > 0:
            message = "failed to list jobs via 'ecaccess-job-list   ': %s" % out
            log_error_and_raise(message, saga.NoSuccess, self._logger)
        elif ret != 0 and len(out) == 0:

            pass
        else:
            for line in out.split("\n"):
                # output looks like this:
                # 112059.svc.uc.futuregrid testjob oweidner 0 Q batch
                # 112061.svc.uc.futuregrid testjob oweidner 0 Q batch
                if len(line.split()) > 1:
                    jobid = "[%s]-[%s]" % (self.rm, line.split()[0].split('.')[0])
                    ids.append(str(jobid))

        return ids

        # # ----------------------------------------------------------------
        # #
        # def container_run (self, jobs) :
        #     self._logger.debug ("container run: %s"  %  str(jobs))
        #     # TODO: this is not optimized yet
        #     for job in jobs:
        #         job.run ()
        #
        #
        # # ----------------------------------------------------------------
        # #
        # def container_wait (self, jobs, mode, timeout) :
        #     self._logger.debug ("container wait: %s"  %  str(jobs))
        #     # TODO: this is not optimized yet
        #     for job in jobs:
        #         job.wait ()
        #
        #
        # # ----------------------------------------------------------------
        # #
        # def container_cancel (self, jobs) :
        #     self._logger.debug ("container cancel: %s"  %  str(jobs))
        #     raise saga.NoSuccess ("Not Implemented");


###############################################################################
#
# noinspection PyMethodOverriding,PyProtectedMember
class ECMWFJob(saga.adaptors.cpi.job.Job):
    """ implements saga.adaptors.cpi.job.Job
    """

    # noinspection PyMissingConstructor
    def __init__(self, api, adaptor):

        # initialize parent class
        _cpi_base = super(ECMWFJob, self)
        _cpi_base.__init__(api, adaptor)

    def _get_impl(self):
        return self

    @SYNC_CALL
    def init_instance(self, job_info):
        """ implements saga.adaptors.cpi.job.Job.init_instance()
        """
        # init_instance is called for every new saga.job.Job object
        # that is created
        self.jd = job_info["job_description"]
        self.js = job_info["job_service"]

        if job_info['reconnect'] is True:
            self._id = job_info['reconnect_jobid']
            self._started = True
        else:
            self._id = None
            self._started = False

        return self.get_api()

    # ----------------------------------------------------------------
    #
    @SYNC_CALL
    def get_state(self):
        """ implements saga.adaptors.cpi.job.Job.get_state()
        """
        return self.js._job_get_state(job_obj=self)

    # ----------------------------------------------------------------
    #
    @SYNC_CALL
    def wait(self, timeout):
        """ implements saga.adaptors.cpi.job.Job.wait()
        """
        if self._started is False:
            log_error_and_raise("Can't wait for job that hasn't been started",
                                saga.IncorrectState, self._logger)
        else:
            self.js._job_wait(job_obj=self, timeout=timeout)

    # ----------------------------------------------------------------
    #
    @SYNC_CALL
    def cancel(self, timeout):
        """ implements saga.adaptors.cpi.job.Job.cancel()
        """
        if self._started is False:
            log_error_and_raise("Can't wait for job that hasn't been started",
                                saga.IncorrectState, self._logger)
        else:
            self.js._job_cancel(self)

    # ----------------------------------------------------------------
    #
    @SYNC_CALL
    def run(self):
        """ implements saga.adaptors.cpi.job.Job.run()
        """
        self._id = self.js._job_run(self)
        self._started = True

    # ----------------------------------------------------------------
    #
    @SYNC_CALL
    def get_service_url(self):
        """ implements saga.adaptors.cpi.job.Job.get_service_url()
        """
        return self.js.rm

    # ----------------------------------------------------------------
    #
    @SYNC_CALL
    def get_id(self):
        """ implements saga.adaptors.cpi.job.Job.get_id()
        """
        return self._id

    # ----------------------------------------------------------------
    #
    @SYNC_CALL
    def get_exit_code(self):
        """ implements saga.adaptors.cpi.job.Job.get_exit_code()
        """
        if self._started is False:
            return None
        else:
            return self.js._job_get_exit_code(self)

    # ----------------------------------------------------------------
    #
    @SYNC_CALL
    def get_created(self):
        """ implements saga.adaptors.cpi.job.Job.get_created()
        """
        if self._started is False:
            return None
        else:
            return self.js._job_get_create_time(self)

    # ----------------------------------------------------------------
    #
    @SYNC_CALL
    def get_started(self):
        """ implements saga.adaptors.cpi.job.Job.get_started()
        """
        if self._started is False:
            return None
        else:
            return self.js._job_get_start_time(self)

    # ----------------------------------------------------------------
    #
    @SYNC_CALL
    def get_finished(self):
        """ implements saga.adaptors.cpi.job.Job.get_finished()
        """
        if self._started is False:
            return None
        else:
            return self.js._job_get_end_time(self)

    # ----------------------------------------------------------------
    #
    @SYNC_CALL
    def get_execution_hosts(self):
        """ implements saga.adaptors.cpi.job.Job.get_execution_hosts()
        """
        if self._started is False:
            return None
        else:
            return self.js._job_get_execution_hosts(self)
