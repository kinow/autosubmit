#!/usr/bin/env python

# Copyright 2014 Climate Forecasting Unit, IC3

# This file is part of Autosubmit.

# Autosubmit is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# Autosubmit is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with Autosubmit.  If not, see <http://www.gnu.org/licenses/>.

import re
from os import listdir
from commands import getstatusoutput
from autosubmit.config.config_parser import config_parser
from autosubmit.config.config_parser import expdef_parser
from autosubmit.config.config_parser import pltdef_parser
from autosubmit.config.config_parser import moddef_parser
from autosubmit.config.dir_config import LOCAL_ROOT_DIR
from autosubmit.config.dir_config import LOCAL_GIT_DIR

class AutosubmitConfig:
	"""Class to handle experiment configuration coming from file or database"""

	def __init__(self, expid):
		self._conf_parser_file = LOCAL_ROOT_DIR + "/" + expid + "/conf/" + "autosubmit_" + expid + ".conf"
		self._exp_parser_file = LOCAL_ROOT_DIR + "/" + expid + "/conf/" + "expdef_" + expid + ".conf"
		
	def check_conf(self):
		self._conf_parser = config_parser(self._conf_parser_file)
		self._exp_parser = expdef_parser(self._exp_parser_file)
	
	def check_git(self):
		self._plt_parser_file = self.get_git_file_platform()
		self._plt_parser = pltdef_parser(LOCAL_ROOT_DIR + "/" + self.get_expid() + "/" + LOCAL_GIT_DIR + "/" + self._plt_parser_file)
		self._mod_parser_file = self.get_git_file_model()
		self._mod_parser = moddef_parser(LOCAL_ROOT_DIR + "/" + self.get_expid() + "/" + LOCAL_GIT_DIR + "/" + self._mod_parser_file)

	def reload(self):
		self._conf_parser = config_parser(self._conf_parser_file)
		self._exp_parser_file = self._conf_parser.get('config', 'EXPDEFFILE')
		self._exp_parser = expdef_parser(self._exp_parser_file)
		git_project = self.get_git_project()
		if (git_project == "true"):
			self._plt_parser_file = self.get_git_file_platform() 
			self._plt_parser = pltdef_parser(LOCAL_ROOT_DIR + "/" + self.get_expid() + "/" + LOCAL_GIT_DIR + "/" + self._plt_parser_file) 
			self._mod_parser_file = self.get_git_file_model() 
			self._mod_parser = moddef_parser(LOCAL_ROOT_DIR + "/" + self.get_expid() + "/" + LOCAL_GIT_DIR + "/" + self._mod_parser_file)

	def load_parameters(self):
		expdef = []
		incldef = []
		for section in self._exp_parser.sections():
			if (section.startswith('include')):
				items = [x for x in self._exp_parser.items(section) if x not in self._exp_parser.items('DEFAULT')]
				incldef += items
			else:
				expdef += self._exp_parser.items(section)

		parameters = dict()
		for item in expdef:
			parameters[item[0]] = item[1]
		for item in incldef:
			parameters[item[0]] = file(item[1]).read()

		git_project = self.get_git_project()
		if (git_project == "true"):
			# Load git parameters
			print "Loading git parameters..."
			parameters2 = parameters.copy()
			parameters2.update(self.load_git_parameters())
			parameters = parameters2

		return parameters


	def load_git_parameters(self):
		pltdef = []
		moddef = []
		for section in self._plt_parser.sections():
			pltdef += self._plt_parser.items(section)
		for section in self._mod_parser.sections():
			moddef += self._mod_parser.items(section)
		
		parameters = dict()
		for item in pltdef:
			parameters[item[0]] = item[1]
		for item in moddef:
			parameters[item[0]] = item[1]

		return parameters

	def print_parameters(self, title, parameters):
		"""Prints the parameters table in a tabular mode"""
		print title
		print "----------------------"
		print "{0:<{col1}}| {1:<{col2}}".format("-- Parameter --","-- Value --",col1=15,col2=15)
		for i in parameters:
			print "{0:<{col1}}| {1:<{col2}}".format(i[0],i[1],col1=15,col2=15)
		print ""


	def check_parameters(self):
		"""Function to check configuration of Autosubmit.
		Returns True if all variables are set.
		If some parameter do not exist, the function returns False.
		
		:retruns: bool
		"""
		result = True
		
		for section in self._conf_parser.sections():
			self.print_parameters("AUTOSUBMIT PARAMETERS - " + section, self._conf_parser.items(section))
			if ("" in [item[1] for item in self._conf_parser.items(section)]):
				result = False
		for section in self._exp_parser.sections():
			self.print_parameters("EXPERIMENT PARAMETERS - " + section, self._exp_parser.items(section))
			if ("" in [item[1] for item in self._exp_parser.items(section)]):
				result = False

		git_project = self.get_git_project()
		if (git_project == "true"):
			for section in self._plt_parser.sections():
				self.print_parameters("PLATFORM PARAMETERS - " + section, self._plt_parser.items(section))
				if ("" in [item[1] for item in self._plt_parser.items(section)]):
					result = False
			for section in self._mod_parser.sections():
				self.print_parameters("MODEL PARAMETERS - " + section, self._mod_parser.items(section))
				if ("" in [item[1] for item in self._mod_parser.items(section)]):
					result = False

		return result


	def get_expid(self):
		return self._conf_parser.get('config','EXPID')

	def set_expid(self, exp_id):
		# Autosubmit conf
		content = file(self._conf_parser_file).read()
		if re.search('EXPID =.*', content):
			content = content.replace(re.search('EXPID =.*', content).group(0), "EXPID = " + exp_id) 
		file(self._conf_parser_file,'w').write(content)
		# Experiment conf
		content = file(self._exp_parser_file).read()
		if re.search('EXPID =.*', content):
			content = content.replace(re.search('EXPID =.*', content).group(0), "EXPID = " + exp_id) 
		file(self._exp_parser_file,'w').write(content)

	def get_git_project(self):
		return self._exp_parser.get('experiment','GIT_PROJECT').lower()
	
	def get_git_project_origin(self):
		return self._exp_parser.get('git','GIT_PROJECT_ORIGIN').lower()

	def get_git_project_branch(self):
		return self._exp_parser.get('git','GIT_PROJECT_BRANCH').lower()
	
	def get_git_project_commit(self):
		return self._exp_parser.get('git','GIT_PROJECT_BRANCH').lower()

	def set_git_project_commit(self):
		"""Function to register in the configuration the commit SHA of the git project version."""
		save = False
		project_name = listdir(LOCAL_ROOT_DIR + "/" + self.get_expid() + "/" + LOCAL_GIT_DIR)[0]
		(status1, output) = getstatusoutput("cd " + LOCAL_ROOT_DIR + "/" + self.get_expid() + "/" + LOCAL_GIT_DIR + "/" + project_name)
		(status2, output) = getstatusoutput("cd " + LOCAL_ROOT_DIR + "/" + self.get_expid() + "/" + LOCAL_GIT_DIR + "/" + project_name + "; " + "git rev-parse --abbrev-ref HEAD")
		if (status1 == 0 and status2 == 0):
			project_branch = output
			save = True
			print "Project branch is: " + project_branch
		else:
			print "Failed to retrieve project branch..." 
			save = False
		(status1, output) = getstatusoutput("cd " + LOCAL_ROOT_DIR + "/" + self.get_expid() + "/" + LOCAL_GIT_DIR + "/" + project_name)
		(status2, output) = getstatusoutput("cd " + LOCAL_ROOT_DIR + "/" + self.get_expid() + "/" + LOCAL_GIT_DIR + "/" + project_name + "; " + "git rev-parse HEAD")
		if (status1 == 0 and status2 == 0):
			project_sha = output
			save = True
			print "Project commit SHA is: " + project_sha
		else: 
			save = False
			print "Failed to retrieve project commit SHA..."
		project_branch_sha = project_branch + " " + project_sha

		# register changes
		if (save):
			content = file(self._exp_parser_file).read()
			if re.search('GIT_PROJECT_COMMIT =.*', content):
				content = content.replace(re.search('GIT_PROJECT_COMMIT =.*', content).group(0), "GIT_PROJECT_COMMIT = " + project_branch_sha) 
			file(self._exp_parser_file,'w').write(content)
			print "Project commit SHA succesfully registered to the configuration file."
		else:
			print "Changes NOT registered to the configuration file..."
	
	def get_git_file_platform(self):
		return self._exp_parser.get('git','GIT_FILE_PLATFORM_CONF')
	
	def get_git_file_model(self):
		return self._exp_parser.get('git','GIT_FILE_MODEL_CONF')

	def get_date_list(self):
		return self._exp_parser.get('experiment','DATELIST').split(' ')

	def get_starting_chunk(self):
		return int(self._exp_parser.get('experiment','CHUNKINI'))
	
	def get_num_chunks(self):
		return int(self._exp_parser.get('experiment','NUMCHUNKS'))

	def get_member_list(self):
		return self._exp_parser.get('experiment','MEMBERS').split(' ')

	def get_rerun(self):
		return self._exp_parser.get('experiment','RERUN').lower()

	def get_platform(self):
		return self._exp_parser.get('experiment', 'HPCARCH')
	
	def set_platform(self, hpc):
		content = file(self._exp_parser_file).read()
		if re.search('HPCARCH =.*', content):
			content = content.replace(re.search('HPCARCH =.*', content).group(0), "HPCARCH = " + hpc)
		file(self._exp_parser_file,'w').write(content)

	def set_version(self, autosubmit_version):
		content = file(self._conf_parser_file).read()
		if re.search('AUTOSUBMIT_VERSION =.*', content):
			content = content.replace(re.search('AUTOSUBMIT_VERSION =.*', content).group(0), "AUTOSUBMIT_VERSION = " + autosubmit_version)
		file(self._conf_parser_file,'w').write(content)

	def set_local_root(self):
		content = file(self._conf_parser_file).read()
		if re.search('AUTOSUBMIT_LOCAL_ROOT =.*', content):
			content = content.replace(re.search('AUTOSUBMIT_LOCAL_ROOT =.*', content).group(0), "AUTOSUBMIT_LOCAL_ROOT = " + LOCAL_ROOT_DIR)
		file(self._conf_parser_file,'w').write(content)

	def get_scratch_dir(self):
		return self._exp_parser.get('experiment', 'SCRATCH_DIR')

	def set_scratch_dir(self, hpc):
		content = file(self._exp_parser_file).read()
		if re.search('SCRATCH_DIR =.*', content):
			if hpc == "bsc":
				content = content.replace(re.search('SCRATCH_DIR =.*', content).group(0), "SCRATCH_DIR = /gpfs/scratch/ecm86")
			elif hpc == "hector":
				content = content.replace(re.search('SCRATCH_DIR =.*', content).group(0), "SCRATCH_DIR = /work/pr1u1011")
			elif hpc == "ithaca":
				content = content.replace(re.search('SCRATCH_DIR =.*', content).group(0), "SCRATCH_DIR = /scratch")
			elif hpc == "lindgren":
				content = content.replace(re.search('SCRATCH_DIR =.*', content).group(0), "SCRATCH_DIR = /cfs/scratch")
			elif hpc == "ecmwf":
				content = content.replace(re.search('SCRATCH_DIR =.*', content).group(0), "SCRATCH_DIR = /scratch/ms")
			elif hpc == "marenostrum3": 
				content = content.replace(re.search('SCRATCH_DIR =.*', content).group(0), "SCRATCH_DIR = /gpfs/scratch")
			elif hpc == "archer": 
				content = content.replace(re.search('SCRATCH_DIR =.*', content).group(0), "SCRATCH_DIR = /work/pr1u1011")
		file(self._exp_parser_file,'w').write(content)
	
	def get_hpcproj(self):
		return self._exp_parser.get('experiment', 'HPCPROJ')

	def get_hpcuser(self):
		return self._exp_parser.get('experiment', 'HPCUSER')
	
	def get_alreadySubmitted(self):
		return int(self._conf_parser.get('config','ALREADYSUBMITTED'))
	
	def get_totalJobs(self):
		return int(self._conf_parser.get('config','TOTALJOBS'))

	def	get_maxWaitingJobs(self):
		return int(self._conf_parser.get('config','MAXWAITINGJOBS'))
	
	def get_safetysleeptime(self):
		return int(self._conf_parser.get('config','SAFETYSLEEPTIME'))

	def set_safetysleeptime(self, hpc):
		content = file(self._conf_parser_file).read()
		if re.search('SAFETYSLEEPTIME =.*', content):
			if hpc == "bsc":
				content = content.replace(re.search('SAFETYSLEEPTIME =.*', content).group(0), "SAFETYSLEEPTIME = 10")
			elif hpc == "hector":
				content = content.replace(re.search('SAFETYSLEEPTIME =.*', content).group(0), "SAFETYSLEEPTIME = 300")
			elif hpc == "ithaca":
				content = content.replace(re.search('SAFETYSLEEPTIME =.*', content).group(0), "SAFETYSLEEPTIME = 10")
			elif hpc == "lindgren":
				content = content.replace(re.search('SAFETYSLEEPTIME =.*', content).group(0), "SAFETYSLEEPTIME = 300")
			elif hpc == "ecmwf":
				content = content.replace(re.search('SAFETYSLEEPTIME =.*', content).group(0), "SAFETYSLEEPTIME = 300")
			elif hpc == "marenostrum3": 
				content = content.replace(re.search('SAFETYSLEEPTIME =.*', content).group(0), "SAFETYSLEEPTIME = 300")
			elif hpc == "archer": 
				content = content.replace(re.search('SAFETYSLEEPTIME =.*', content).group(0), "SAFETYSLEEPTIME = 300")
		file(self._conf_parser_file,'w').write(content)
	
	def get_retrials(self):
		return int(self._conf_parser.get('config','RETRIALS'))
