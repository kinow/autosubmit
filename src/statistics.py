#!/usr/bin/env python

import commands
import pydot
import pickle
from job.job_list import JobList
from job.job_list import RerunJobList
import matplotlib
import sys
from dir_config import LOCAL_ROOT_DIR
import argparse
import time
from job.job_common import Status
from job.job_common import Type

import numpy as np
import matplotlib.pyplot as plt



def CreateBarDiagram(expid, joblist, output_file):
	def autolabel(rects):	
		# attach text labels
		for rect in rects:
			height = rect.get_height()
			if (height > max_time):
				ax[plot-1].text(rect.get_x()+rect.get_width()/2., 1.05*max_time, '%d'%int(height),ha='center', va='bottom', rotation='vertical', fontsize=8)


	def failabel(rects):
		for rect in rects:
			height = rect.get_height()
			if (height > 0):
				ax[plot-1].text(rect.get_x()+rect.get_width()/2., 1.05*height, '%d'%int(height),ha='center', va='bottom', fontsize=8)
			
	average_run_time=sum([float(job.check_run_time())/3600 for job in joblist])/len(joblist)
	max_time=max(max([float(job.check_run_time())/3600 for job in joblist]),max([float(job.check_queued_time())/3600 for job in joblist]))
	min_time=min([float(job.check_run_time())/3600-average_run_time for job in joblist])
	#print average_run_time
	l1=0
	l2=len(joblist)
	#print [int(job.check_queued_time())/3600 for job in joblist[l1:l2]]
	#print [int(job.check_run_time())/3600 for job in joblist[l1:l2]]
	#print [int(job.check_run_time())/3600-average_run_time for job in joblist[l1:l2]]
	#print [int(job.check_failed_times()) for job in joblist[l1:l2]]
	MAX=12.0
	N=len(joblist)
	num_plots=int(np.ceil(N/MAX))

	ind = np.arange(int(MAX))  # the x locations for the groups
	width = 0.16       # the width of the bars
	
	plt.close('all')
	fig = plt.figure(1, figsize = (14,6*num_plots))
	#fig = plt.figure()
	ax=[]

	for plot in range(1,num_plots+1):
		ax.append(fig.add_subplot(num_plots,1, plot))
		l1=int((plot-1)*MAX)
		l2=int(plot*MAX)
		if plot == num_plots:
			ind = np.arange(len([int(job.check_queued_time())/3600 for job in joblist[l1:l2]]))
		rects1 = ax[plot-1].bar(ind, [int(job.check_queued_time())/3600 for job in joblist[l1:l2]], width, color='r')
		rects2 = ax[plot-1].bar(ind+width, [int(job.check_run_time())/3600 for job in joblist[l1:l2]], width, color='g')
		rects3 = ax[plot-1].bar(ind+width*2, [int(job.check_run_time())/3600-average_run_time for job in joblist[l1:l2]], width, color='b')
		rects4 = ax[plot-1].bar(ind+width*3, [int(job.check_failed_times()) for job in joblist[l1:l2]], width, color='y')
		rects5 = ax[plot-1].bar(ind+width*4, [int(job.check_fail_queued_time())/3600 for job in joblist[l1:l2]], width, color='m')
		rects6 = ax[plot-1].bar(ind+width*5, [int(job.check_fail_run_time())/3600 for job in joblist[l1:l2]], width, color='c')
		ax[plot-1].set_ylabel('hours')
		ax[plot-1].set_xticks(ind+width)
		ax[plot-1].set_xticklabels( [job.get_name() for job in joblist[l1:l2]], rotation='vertical')
		box = ax[plot-1].get_position()
		ax[plot-1].set_position([box.x0, box.y0, box.width * 0.8, box.height*0.8])
		ax[plot-1].set_title(expid, fontsize=20, fontweight='bold')
		lgd = ax[plot-1].legend( (rects1[0], rects2[0], rects3[0], rects4[0], rects5[0], rects6[0]), ('Queued (h)', 'Run (h)', 'Excess (h)', 'Failed jobs (#)', 'Fail Queued (h)', 'Fail Run (h)'), loc="upper left", bbox_to_anchor=(1,1) )
		failabel(rects4)
		autolabel(rects5)
		autolabel(rects6)
		plt.ylim((1.15*min_time,1.15*max_time))

	#fig.set_size_inches(14,num_plots*6)
	#plt.show()
	#plt.savefig(output_file, bbox_extra_artists=(lgd), bbox_inches='tight') 
	#plt.savefig(output_file, bbox_inches='tight') 
	plt.savefig(output_file, bbox_extra_artists=(lgd)) 


def GenerateOutput(expid, joblist, output_format="pdf"):
	now = time.localtime()
	output_date = time.strftime("%Y%m%d_%H%M", now) 
	output_file = LOCAL_ROOT_DIR + "/" + expid + "/plot/statistics_" + expid + "_" + output_date + "." + output_format

	CreateBarDiagram(expid, joblist, output_file)

	#if output_format == "png":
	#elif output_format == "pdf":
	#elif output_format == "ps":

if __name__ == "__main__":
	parser = argparse.ArgumentParser(description='Plot statistics graph')
	parser.add_argument('-e', '--expid', required=True, nargs = 1)
	parser.add_argument('-j', '--joblist', required=True, nargs = 1)
	parser.add_argument('-o', '--output', required=True, nargs = 1, choices = ('pdf', 'png', 'ps'), default = 'pdf')

	args = parser.parse_args()

	expid = args.expid[0]
	root_name = args.joblist[0]
	output = args.output[0]

	filename = LOCAL_ROOT_DIR + "/" + expid + '/pkl/' +root_name + '_' + expid + '.pkl'
	jobs = pickle.load(file(filename,'r'))
	if not type(jobs) == type([]):
		jobs = [job for job in jobs.get_finished() if job.get_type() == Type.SIMULATION]

	GenerateOutput(expid, jobs, output)
