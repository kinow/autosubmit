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

from config_parser import config_parser
from config_parser import expdef_parser
from config_parser import pltdef_parser
from config_parser import moddef_parser
from dir_config import LOCAL_ROOT_DIR
from dir_config import LOCAL_GIT_DIR

class AutosubmitConfig:
	"""Class to handle experiment configuration coming from file or database"""

	def __init__(self, expid):
		self._conf_parser_file = LOCAL_ROOT_DIR + "/" + expid + "/conf/" + "autosubmit_" + expid + ".conf"
		self._conf_parser = config_parser(self._conf_parser_file)
		self._exp_parser_file = self._conf_parser.get('config', 'EXPDEFFILE')
		self._exp_parser = expdef_parser(self._exp_parser_file)
	
	def init_git(self):
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

	def get_git_project(self):
		return self._exp_parser.get('experiment','GIT_PROJECT').lower()
	
	def get_git_project_origin(self):
		return self._exp_parser.get('git','GIT_PROJECT_ORIGIN').lower()

	def get_git_project_branch(self):
		return self._exp_parser.get('git','GIT_PROJECT_BRANCH').lower()
	
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

	def get_scratch_dir(self):
		return self._exp_parser.get('experiment', 'SCRATCH_DIR')
	
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
	
	def get_retrials(self):
		return int(self._conf_parser.get('config','RETRIALS'))
