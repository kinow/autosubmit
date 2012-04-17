#!/usr/bin/env python

from xml.dom.minidom import parseString
from hpcqueue import HPCQueue
from time import sleep

class PsQueue(HPCQueue):
	def __init__(self, expid):
		self._host = "ellen"
		self._cancel_cmd = "kill -SIGINT"
		self._checkjob_cmd = "source ~/.profile; pscall.sh"
		self._submit_cmd = "source ~/.profile; shcall.sh"
		self._job_status = dict()
		self._job_status['COMPLETED'] = ['1']
		self._job_status['RUNNING'] = ['0']
		self._job_status['QUEUING'] = ['qw', 'hqw', 'hRwq']
		self._job_status['FAILED'] = ['Eqw', 'Ehqw', 'EhRqw']
		self._pathdir = "\$HOME/LOG_"+expid
		self._expid = expid
		self._remote_log_dir = "/cfs/klemming/scratch/\${USER:0:1}/\$USER/" + expid + "/LOG_" + expid
		
	def parse_job_output(self, output):
		return output

	def get_submitted_job_id(self, output):
		return output

	def jobs_in_queue(self, output):
		dom = parseString(output)
		jobs_xml = dom.getElementsByTagName("JB_job_number")
		return [int(element.firstChild.nodeValue) for element in jobs_xml ]

		
def main():
	q = PsQueue()
	q.check_job(1688)
	j = q.submit_job("/cfu/autosubmit/l002/templates/l002.sim")
	sleep(10)
	print q.check_job(j)
	q.cancel_job(j)

if __name__ == "__main__":
	main()
