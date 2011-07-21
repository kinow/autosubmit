#!/usr/bin/env python

import commands
import pydot
import pickle
from job.job_list import JobList
import matplotlib
import sys
from dir_config import LOCAL_ROOT_DIR
import argparse
import time
from job.job_common import Status

table = dict([(Status.UNKNOWN, 'white'), (Status.WAITING, 'gray'), (Status.READY, 'lightblue'), (Status.SUBMITTED, 'cyan'), (Status.QUEUING, 'lightpink'), (Status.RUNNING, 'green'), (Status.COMPLETED, 'yellow'), (Status.FAILED, 'red')])

def ColorStatus(status):
	color = table[Status.UNKNOWN]
	if status == Status.WAITING:
		color = table[Status.WAITING]
	elif status == Status.READY:
		color = table[Status.READY]
	elif status == Status.SUBMITTED:
		color = table[Status.SUBMITTED]
	elif status == Status.QUEUING:
		color = table[Status.QUEUING]
	elif status == Status.RUNNING:
		color = table[Status.RUNNING]
	elif status == Status.COMPLETED:
		color = table[Status.COMPLETED]
	elif status == Status.FAILED:
		color = table[Status.FAILED]
	return color

def CreateTreeList(expid, joblist):
	graph = pydot.Dot(graph_type='digraph')

	legend = pydot.Subgraph(graph_name = 'Legend', label = 'Legend', rank = "source")
	legend.add_node(pydot.Node(name='WAITING', shape='box', style="filled", fillcolor=table[Status.WAITING]))
	legend.add_node(pydot.Node(name='READY', shape='box', style="filled", fillcolor=table[Status.READY]))
	legend.add_node(pydot.Node(name='SUBMITTED', shape='box', style="filled", fillcolor=table[Status.SUBMITTED]))
	legend.add_node(pydot.Node(name='QUEUING', shape='box', style="filled", fillcolor=table[Status.QUEUING]))
	legend.add_node(pydot.Node(name='RUNNING', shape='box', style="filled", fillcolor=table[Status.RUNNING]))
	legend.add_node(pydot.Node(name='COMPLETED', shape='box', style="filled", fillcolor=table[Status.COMPLETED]))
	legend.add_node(pydot.Node(name='FAILED', shape='box', style="filled", fillcolor=table[Status.FAILED]))
	graph.add_subgraph(legend)

	exp = pydot.Subgraph(graph_name = 'Experiment', label = expid)
	for job in joblist:
		node_job = pydot.Node(job.get_name(),shape='box', style="filled", fillcolor=ColorStatus(job.get_status()))
		exp.add_node(node_job)
		#exp.set_node_style(node_job,shape='box', style="filled", fillcolor=ColorStatus(job.get_status()))
		if job.has_children()!=0:
			for child in job.get_children():
				node_child=pydot.Node(child.get_name() ,shape='box', style="filled", fillcolor=ColorStatus(child.get_status()))
				exp.add_node(node_child)
				#exp.set_node_style(node_child,shape='box', style="filled", fillcolor=ColorStatus(job.get_status()))
				exp.add_edge(pydot.Edge(node_job, node_child))

	graph.add_subgraph(exp)

	return graph

def GenerateOutput(expid, joblist, output_format="pdf"):
	now = time.localtime()
	output_date = time.strftime("%Y%m%d_%H%M", now) 
	output_file = LOCAL_ROOT_DIR + "/" + expid + "/plot/" + expid + "_" + output_date + "." + output_format

	graph = CreateTreeList(expid, joblist)

	if output_format == "png":
		graph.write_png(output_file)
	else:
		graph.write_pdf(output_file)

if __name__ == "__main__":
	parser = argparse.ArgumentParser(description='Plot autosubmit graph')
	parser.add_argument('-e', '--expid', required=True, nargs = 1)
	parser.add_argument('-j', '--joblist', required=True, nargs = 1)
	parser.add_argument('-o', '--output', required=True, nargs = 1, choices = ('pdf', 'png'), default = 'pdf')

	args = parser.parse_args()

	expid = args.expid[0]
	root_name = args.joblist[0]
	output = args.output[0]

	filename = LOCAL_ROOT_DIR + "/" + expid + '/pkl/' +root_name + '_' + expid + '.pkl'
	jobs = pickle.load(file(filename,'r'))
	if not type(jobs) == type([]):
		jobs = jobs.get_job_list()

	GenerateOutput(expid, jobs, output)
