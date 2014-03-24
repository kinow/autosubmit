#!/usr/bin/env python

from dir_config import LOCAL_ROOT_DIR
import pickle
from job.job_list import JobList
from job.job_list import RerunJobList
from job.job_common import Status
from job.job_common import Type
import argparse
from monitor import GenerateOutput
from sys import setrecursionlimit
import json
from pyparsing import nestedExpr

def get_status(s):
	if s == 'READY':
		return Status.READY
	elif s == 'COMPLETED':
		return Status.COMPLETED
	elif s == 'WAITING':
		return Status.WAITING
	elif s == 'SUSPENDED':
		return Status.SUSPENDED
	elif s == 'FAILED':
		return Status.FAILED
	elif s == 'UNKNOWN':
		return Status.UNKNWON

def get_tyoe(t):
	if t == 'LOCALSETUP':
		return Type.LOCALSETUP
	elif t == 'REMOTESETUP':
		return Type.REMOTESETUP
	elif t == 'INITIALISATION':
		return Type.INITIALISATION
	elif t == 'SIMULATION':
		return Type.SIMULATION
	elif t == 'POSTPROCESSING':
		return Type.POSTPROCESSING
	elif t == 'CLEANING':
		return Type.CLEANING
	elif t == 'LOCALTRANSFER':
		return Type.TRANSFER

def get_members(out):
		count = 0
		data = []
		for element in out:
			if (count%2 == 0):
				ms = {'m': out[count], 'cs': get_chunks(out[count+1])}
				data.append(ms)
				count = count + 1
			else:
				count = count + 1

		return data

def get_chunks(out):
	count = 0
	data = []
	for element in out:
		if (element.find("-") != -1):
			numbers = element.split("-")
			for count in range(int(numbers[0]), int(numbers[1])+1):
				data.append(str(count))
		else:
			data.append(element)

	return data

def create_json(text):
	count = 0
	data = []
	#text = "[ 19601101 [ fc0 [1 2 3 4] fc1 [1] ] 16651101 [ fc0 [1-30 31 32] ] ]"
	
	out = nestedExpr('[',']').parseString(text).asList()

	for element in out[0]:
		if (count%2 == 0):
			sd = {'sd': out[0][count], 'ms': get_members(out[0][count+1])}
			data.append(sd)
			count = count + 1
		else:
			count = count + 1

	sds = {'sds': data}
	result = json.dumps(sds)
	return result


if __name__ == '__main__':
	parser = argparse.ArgumentParser(description='Autosubmit change pikcle')
	parser.add_argument('-e', '--expid', type=str, nargs=1, required=True, help='Experiment ID')
	parser.add_argument('-j', '--joblist', type=str, nargs=1, required=True, help='Job list')
	parser.add_argument('-s', '--save', action="store_true", default=False, help='Save changes to disk')
	parser.add_argument('-t', '--status_final', choices = ('READY', 'COMPLETED', 'WAITING', 'SUSPENDED', 'FAILED', 'UNKNOWN'), required = True, help = 'Supply the target status')
	group1 = parser.add_mutually_exclusive_group(required = True)
	group1.add_argument('-l', '--list', type = str, help='Alternative 1: Supply the list of job names to be changed. Default = Any. LIST = "b037_20101101_fc3_21_sim b037_20111101_fc4_26_sim"')
	group1.add_argument('-f', '--filter', action="store_true", help='Alternative 2: Supply a filter for the job list. See help of filter arguments: chunk filter, status filter or type filter')
	group2 = parser.add_argument_group('filter arguments')
	group2.add_argument('-fc', '--filter_chunks', type = str, default = 'Any', help = 'Supply the list of chunks to change the status. Default = Any. LIST = [ 19601101 [ fc0 [1 2 3 4] fc1 [1] ] 19651101 [ fc0 [16-30] ] ]')#, required = True)
	group2.add_argument('-fs', '--filter_status', type = str, choices = ('Any', 'READY', 'COMPLETED', 'WAITING', 'SUSPENDED', 'FAILED', 'UNKNOWN'), default = 'Any', help = 'Select the original status to filter the list of jobs')
	group2.add_argument('-ft', '--filter_type', type = str, choices = ('Any', 'LOCALSETUP', 'REMOTESETUP', 'INITIALISATION', 'SIMULATION', 'POSTPROCESSING', 'CLEANING', 'LOCALTRANSFER'), default = 'Any', help = 'Select the job type to filter the list of jobs')
	args = parser.parse_args()

	expid = args.expid[0]
	root_name = args.joblist[0]
	save = args.save
	final = args.status_final

	print expid
	l1 = pickle.load(file(LOCAL_ROOT_DIR + "/" + expid + "/pkl/" + root_name + "_" + expid + ".pkl", 'r'))

	
	if(args.filter):
		if(args.filter_chunks):
			fc = args.filter_chunks
			print fc

			if (fc == 'Any'):
				for job in l1.get_job_list():
					job.set_status(get_status(final))
					print "CHANGED: job: " + job.get_name() + " status to: " + final
			else:
				data = json.loads(create_json(fc))
				#change localsetup and remotesetup
				#[...]
				for date in data['sds']:
					for member in date['ms']:
						jobname_ini = expid + "_" + str(date['sd']) + "_" + str(member['m']) + "_ini"
						job = l1.get_job_by_name(jobname_ini)
						job.set_status(get_status(final))
						print "CHANGED: job: " + job.get_name() + " status to: " + final
						#change also trans
						#[...]
						for chunk in member['cs']:
							jobname_sim = expid + "_" + str(date['sd']) + "_" + str(member['m']) + "_" + str(chunk) + "_sim"
							jobname_post = expid + "_" + str(date['sd']) + "_" + str(member['m']) + "_" + str(chunk) + "_post" 
							jobname_clean = expid + "_" + str(date['sd']) + "_" + str(member['m']) + "_" + str(chunk) + "_clean" 
							job = l1.get_job_by_name(jobname_sim)
							job.set_status(get_status(final))
							print "CHANGED: job: " + job.get_name() + " status to: " + final
							job = l1.get_job_by_name(jobname_post)
							job.set_status(get_status(final))
							print "CHANGED: job: " + job.get_name() + " status to: " + final
							job = l1.get_job_by_name(jobname_clean)
							job.set_status(get_status(final))
							print "CHANGED: job: " + job.get_name() + " status to: " + final
		

	if(args.list):
		jobs = args.list.split()

		if (jobs == 'Any'):
			for job in l1.get_job_list():
				job.set_status(get_status(final))
				print "CHANGED: job: " + job.get_name() + " status to: " + final
		else:
			for job in l1.get_job_list():
				if (job.get_name() in jobs):
					job.set_status(get_status(final))
					print "CHANGED: job: " + job.get_name() + " status to: " + final

		setrecursionlimit(50000)
		l1.update_list()
		pickle.dump(l1, file(LOCAL_ROOT_DIR + "/" + expid + "/pkl/" + root_name + "_" + expid + ".pkl", 'w'))



	if(save):
		l1.update_from_file()
	else:
		l1.update_from_file(False)

	if(save):
		setrecursionlimit(50000)
		pickle.dump(l1, file(LOCAL_ROOT_DIR + "/" + expid + "/pkl/" + root_name + "_" + expid + ".pkl", 'w'))

	GenerateOutput(expid, l1.get_job_list())


