#!/usr/bin/env python

from xml.dom.minidom import parseString
from hpcqueue import HPCQueue
from time import sleep

class LgQueue(HPCQueue):
	def __init__(self, expid):
		self._host = "lindgren"
		self._cancel_cmd = "qdel"
		self._checkjob_cmd = "qstat"
		self._submit_cmd = "qsub"
		self._status_cmd = "qsub -u \$USER | tail -n +6|cut -d' ' -f1"
		self._job_status = dict()
		self._job_status['COMPLETED'] = ['C', 'E']
		self._job_status['RUNNING'] = ['R']
		self._job_status['QUEUING'] = ['Q', 'H', 'S', 'T', 'W']
		self._job_status['FAILED'] = ['Failed', 'Node_fail', 'Timeout']
		self._pathdir = "\$HOME/LOG_"+expid
		self._expid = expid
		self._remote_log_dir = "/cfs/klemming/scratch/\${USER:0:1}/\$USER/" + expid + "/LOG_" + expid
		
	def parse_job_output(self, output):
		job_state = output.split('\n')[2].split()[4]
		return job_state

	def get_submitted_job_id(self, output):
		return output.split('.')[0]

	def jobs_in_queue(self, output):
		print output
		return output.split()


def main():
	q = LgQueue()
	q.check_job(1688)
	j = q.submit_job("/cfu/autosubmit/l002/templates/l002.sim")
	sleep(10)
	print q.check_job(j)
	q.cancel_job(j)
	
		
if __name__ == "__main__":
	main()
