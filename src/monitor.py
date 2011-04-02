#!/usr/bin/env python

import commands
import pydot
import pickle
from job.job_list import JobList
import time
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import logging
import sys

job_logger = logging.getLogger("AutoLog.monitor")

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
	graph=pydot.Dot(graph_type='digraph')
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

	pngfile=expid+'_graph.png'
	pdffile=expid+'_graph.pdf'
	#graph.set_graphviz_executables({'dot': '/gpfs/apps/GRAPHVIZ/2.26.3/bin/dot'})
	graph.write_png(pngfile) 
	#graph.write_pdf(pdffile) 
 

if __name__ == "__main__":
	if not len(sys.argv)>0:
		print "please give an expid... "
		sys.exit()
	else:  
		expid=sys.argv[1]

	if not len(sys.argv)>1:
		print "please give a root name for the pickle... "
		sys.exit()
	else:  
		rootname=sys.argv[2]

	filename='/cfu/autosubmit/' + expid + '/pkl/' +rootname+'_'+expid+'.pkl'
	file1=open(filename,'r')
	jobs=pickle.load(file(filename,'r'))
	if not type(jobs) == type([]):
		jobs=jobs.job_list
	#dummy_list(jobs)
	#for job in jobs:
	# job.setExpid('ploum')
	CreateTreeList(rootname+'_'+expid, jobs)
	file1.close()
