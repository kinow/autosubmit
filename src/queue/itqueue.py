#!/usr/bin/env python

from xml.dom.minidom import parseString
from hpcqueue import HPCQueue
from time import sleep

class ItQueue(HPCQueue):
	def __init__(self,expid):
		self._host = "sun-login"
		self._cancel_cmd = "qdel"
		self._checkjob_cmd = "qstat -xml -j"
		self._submit_cmd = "qsub"
		self._job_status = dict()
		self._job_status['COMPLETED'] = []
		self._job_status['RUNNING'] = ['128']
		self._job_status['QUEUING'] = []
		self._job_status['FAILED'] = []
		self._pathdir = "\$HOME/LOG_"+expid
		
	def parse_job_output(self, output):
		dom = parseString(output)
		job_xml = dom.getElementsByTagName("JAT_status")
		job_state = job_xml[0].firstChild.nodeValue
		return job_state

	def get_submitted_job_id(self, output):
		return output.split(' ')[2]

	def jobs_in_queue(self, output):
		dom = parseString(output)
		jobs_xml = dom.getElementsByTagName("JB_job_number")
		return [int(element.firstChild.nodeValue) for element in jobs_xml ]

		
if __name__ == "__main__":
	q = ItQueue()
	q.check_job(1688)
	j = q.submit_job("/home/cfu/omula/test/run_t159l62_orca1.ksh")
	sleep(10)
	print q.check_job(j)
	q.cancel_job(j)
