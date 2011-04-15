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

def ColorStatus(status):
	color='white'
	if status==0:
		color='cyan'
	elif status==1:
		color='blue'
	elif status==2:
		color='pink'
	elif status==3:
		color='yellow'
	elif status==4:
		color='orange'
	elif status==5:
		color='green'
	elif status==-1:
		color='red'
	return color

def CreateTreeList(expid, joblist):
	graph = pydot.Dot(graph_type='digraph')
	for job in joblist:
		node_job = pydot.Node(job.get_name(),shape='box', style="filled", fillcolor=ColorStatus(job.get_status()))
		graph.add_node(node_job)
		#graph.set_node_style(node_job,shape='box', style="filled", fillcolor=ColorStatus(job.get_status()))
		if job.has_children()!=0:
			for child in job.get_children():
				node_child=pydot.Node(child.get_name() ,shape='box', style="filled", fillcolor=ColorStatus(child.get_status()))
				graph.add_node(node_child)
				#graph.set_node_style(node_child,shape='box', style="filled", fillcolor=ColorStatus(job.get_status()))
				graph.add_edge(pydot.Edge(node_job, node_child))

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
