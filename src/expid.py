#!/usr/bin/env python

import string
from pysqlite2 import dbapi2 as sql
import sys, os
import argparse
import shutil
import re
import dir_config
from dir_config import DB_DIR
from dir_config import LOCAL_ROOT_DIR
from dir_config import GIT_DIR
from commands import getstatusoutput
from check_compatibility import check_compatibility, print_compatibility

# Database parameters
#DB_DIR = '/cfu/autosubmit/'
DB_FILE = 'ecearth.db'
DB_NAME = 'ecearth'

DB_PATH = DB_DIR + DB_FILE

DEFAULT_EXPID_BSC = "b000"
DEFAULT_EXPID_HEC = "h000"
DEFAULT_EXPID_ITH = "i000"
DEFAULT_EXPID_LIN = "l000"
DEFAULT_EXPID_ECM = "e000"
DEFAULT_EXPID_MN3 = "m000"
DEFAULT_EXPID_ARC = "a000"

def base36encode(number, alphabet=string.digits + string.ascii_lowercase):
	"""Convert positive integer to a base36 string."""
	if not isinstance(number, (int, long)):
		raise TypeError('number must be an integer')
 
	# Special case for zero
	if number == 0:
		return '0'
 
	base36 = ''
 
	sign = ''
	if number < 0:
		sign = '-'
		number = - number
 
	while len(base36) < 4:
		number, i = divmod(number, len(alphabet))
		base36 = alphabet[i] + base36
 
	return sign + base36
 
def base36decode(number):
	return int(number, 36)

def next_name(name):
	name = check_name(name)
	#Convert the name to base 36 in number add 1 and then encode it 
	return base36encode(base36decode(name)+1)

def set_experiment(name, exp_type, model_branch, template_name, template_branch, ocean_diagnostics_branch, description):
	check_db()
	name = check_name(name)

	(conn, cursor) = open_conn()
	try:
		cursor.execute('insert into experiment values(null, ?, ?, ?, ?, ?, ?, ?)', (name, exp_type, description, model_branch, template_name, template_branch, ocean_diagnostics_branch))
	except sql.IntegrityError:
		close_conn(conn, cursor)
		print 'The experiment name %s - %s already exists!!!' % (name, exp_type)
		sys.exit(1)

	conn.commit()
	close_conn(conn, cursor)
	return

def get_experiment(name):
	check_db()
	name = check_name(name)

	(conn, cursor) = open_conn()

	# SQLite always return a unicode object, but we can change this
	# behaviour with the next sentence
	conn.text_factory = str
	cursor.execute('select name,type from experiment where name=?', (name,))
	row = cursor.fetchone()
	if row == None:
		close_conn(conn, cursor)
		print 'The experiment name %s does not exist yet!!!' % name
		sys.exit(1)

	close_conn(conn, cursor)
	return row

def last_name(HPC):
	check_db()
	(conn, cursor) = open_conn()
	conn.text_factory = str
	if HPC == 'bsc':
		hpc_name = "b___"
	elif HPC == "hector":
		hpc_name = "h___"
	elif HPC == 'ithaca':
		hpc_name = "i___"
	elif HPC == 'lindgren':
		hpc_name = "l___"
	elif HPC == 'ecmwf':
		hpc_name = "e___"
	elif HPC == 'marenostrum3':
		hpc_name = "m___"
	elif HPC == 'archer':
		hpc_name = "a___"
	cursor.execute('select name from experiment where rowid=(select max(rowid) from experiment where name LIKE "' + hpc_name + '")')
	row = cursor.fetchone()
	if row == None:
		row = ('empty', )
	close_conn(conn,cursor)
	return row[0]

def new_experiment(exp_type, HPC, model_branch, template_name, template_branch, ocean_diagnostics_branch, description):
	last_exp_name = last_name(HPC)
	if last_exp_name == 'empty':
		if HPC == 'bsc':
			new_name = DEFAULT_EXPID_BSC
		elif HPC == 'hector':
			new_name = DEFAULT_EXPID_HEC
		elif HPC == 'ithaca':
			new_name = DEFAULT_EXPID_ITH
		elif HPC == 'lindgren':
			new_name = DEFAULT_EXPID_LIN
		elif HPC == 'ecmwf':
			new_name = DEFAULT_EXPID_ECM
		elif HPC == 'marenostrum3':
			new_name = DEFAULT_EXPID_MN3
		elif HPC == 'archer':
			new_name = DEFAULT_EXPID_ARC
	else:
		new_name = next_name(last_exp_name)
	set_experiment(new_name, exp_type, model_branch, template_name, template_branch, ocean_diagnostics_branch, description)
	print 'The new experiment "%s" has been registered.' % new_name
	return new_name

def copy_experiment(name, HPC, model_branch, template_name, template_branch, ocean_diagnostics_branch, description):
	new_exp = get_experiment(name)
	new_name = new_experiment(new_exp[1], HPC, model_branch, template_name, template_branch, ocean_diagnostics_branch, description)
	return new_name

def check_db():
	if not os.path.exists(DB_PATH):
		print 'Some problem has happened...check the database file!!!'
		print 'DB file:',DB_PATH
		sys.exit(1)
	return

def check_name(name):
	name = name.lower()
	if len(name) != 4 and not name.isalnum():
		print "So sorry, but the name must have 4 alphanumeric chars!!!"
		sys.exit(1)
	return name

def open_conn():
	conn = sql.connect(DB_PATH)
	cursor = conn.cursor()
	return (conn, cursor)

def close_conn(conn,cursor):
	conn.commit()
	cursor.close()
	conn.close()
	return

#############################
# Conf files
#############################
def prepare_conf_files(content, exp_id, hpc, template_name, autosubmit_version):
	replace_strings = ['REMOTE_DIR =', 'ECEARTH_DIR =.']
	if re.search('EXPID =.*', content):
		content = content.replace(re.search('EXPID =.*', content).group(0), "EXPID = " + exp_id)
	if re.search('HPCARCH =.*', content):
		content = content.replace(re.search('HPCARCH =.*', content).group(0), "HPCARCH = " + hpc)
	if re.search('TEMPLATE_NAME =.*', content):
		content = content.replace(re.search('TEMPLATE_NAME =.*', content).group(0), "TEMPLATE_NAME = " + template_name)
	if re.search('AUTOSUBMIT_VERSION =.*', content):
		content = content.replace(re.search('AUTOSUBMIT_VERSION =.*', content).group(0), "AUTOSUBMIT_VERSION = " + autosubmit_version)

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

	for string in replace_strings:
		if content.find(string) == -1:
			return content
	
	if hpc == "bsc":
		content = content.replace(re.search('REMOTE_DIR =.*', content).group(0), "REMOTE_DIR = /gpfs/projects/ecm86/%(HPCUSER)s")
		content = content.replace(re.search('ECEARTH_DIR =.*', content).group(0), "ECEARTH_DIR = /gpfs/projects/ecm86/common/ecearth")
	elif hpc == "hector":
		content = content.replace(re.search('REMOTE_DIR =.*', content).group(0), "REMOTE_DIR = /share/scratch/cfu/%(HPCUSER)s")
		content = content.replace(re.search('ECEARTH_DIR =.*', content).group(0), "ECEARTH_DIR = /share/scratch/cfu/tools/ecearth")
	elif hpc == "ithaca":
		content = content.replace(re.search('REMOTE_DIR =.*', content).group(0), "REMOTE_DIR = /share/scratch/cfu/%(HPCUSER)s")
		content = content.replace(re.search('ECEARTH_DIR =.*', content).group(0), "ECEARTH_DIR = /share/scratch/cfu/tools/ecearth")
	elif hpc == "lindgren":
		content = content.replace(re.search('REMOTE_DIR =.*', content).group(0), "REMOTE_DIR = /share/scratch/cfu/%(HPCUSER)s")
		content = content.replace(re.search('ECEARTH_DIR =.*', content).group(0), "ECEARTH_DIR = /share/scratch/cfu/tools/ecearth")
	elif hpc == "ecmwf":
		content = content.replace(re.search('REMOTE_DIR =.*', content).group(0), "REMOTE_DIR = /share/scratch/cfu/%(HPCUSER)s")
		content = content.replace(re.search('ECEARTH_DIR =.*', content).group(0), "ECEARTH_DIR = /share/scratch/cfu/tools/ecearth")
	elif hpc == "marenostrum3": 
		content = content.replace(re.search('REMOTE_DIR =.*', content).group(0), "REMOTE_DIR = /share/scratch/cfu/%(HPCUSER)s")
		content = content.replace(re.search('ECEARTH_DIR =.*', content).group(0), "ECEARTH_DIR = /share/scratch/cfu/tools/ecearth")
	elif hpc == "archer": 
		content = content.replace(re.search('REMOTE_DIR =.*', content).group(0), "REMOTE_DIR = /share/scratch/cfu/%(HPCUSER)s")
		content = content.replace(re.search('ECEARTH_DIR =.*', content).group(0), "ECEARTH_DIR = /share/scratch/cfu/tools/ecearth")

	return content


#############################
# Main function
#############################
if __name__ == "__main__":

	##obtain version for autosubmit being used in expid.py step
	##git describe --tags `git rev-list --tags --max-count=1`; git describe --tags; git rev-parse --abbrev-ref HEAD; 
	(status, output) = getstatusoutput("git rev-parse HEAD")
	autosubmit_version = output

	parser = argparse.ArgumentParser()
	group1 = parser.add_mutually_exclusive_group(required = True)
	group1.add_argument('--new', '-n', action = "store_true")
	group1.add_argument('--copy', '-y', type = str)
	group2 = parser.add_argument_group('experiment arguments')
	group2.add_argument('--HPC', '-H', choices = ('bsc', 'hector', 'ithaca', 'lindgren', 'ecmwf', 'marenostrum3', 'archer'), required = True)
	group2.add_argument('--model_name', '-M', choices = ('dummy', 'ecearth', 'nemo'), required = True) 
	group2.add_argument('--model_branch', '-m', type = str, help = "{'develop-v2.3.0', 'develop-v3.0.1', ...} Check available branches here: https://dev.cfu.local/ecearth.git https://dev.cfu.local/nemo.git")
	group2.add_argument('--template_name', '-T',  type = str, help = "{'dummy', 'ecearth', 'ifs', 'nemo', 'ecearth3', 'ifs3', 'nemo3' ...}",required = True) ##find a way to allow only compatible ones with model_name
	group2.add_argument('--template_branch', '-t', type = str, default = 'master', help = "{'master' (defualt), 'develop', ...} Check available branches here: https://dev.cfu.local/templates.git") ##find a way to allow only compatible ones with model_name
	group2.add_argument('--ocean_diagnostics_branch', '-o', type = str, default = 'master', help = "{'master' (default), 'develop', ...} Check available branches here: https://dev.cfu.local/ocean_diagnostics.git") 
	group2.add_argument('--description', '-d', type = str, required = True)

	args = parser.parse_args()
	if args.description is None:
		parser.error("Missing experiment description.")
	if args.HPC is None:
		parser.error("Missing HPC.");
	##complete missing errors for new arguments

	if args.new is None and args.copy is None:
		parser.error("Missing method either New or Copy.")
	if args.new:
		##new parameters to be inserted on database
		##  --HPC  --model_name --model_branch  --template_name --template_branch --ocean_diagnostics_branch --description
		exp_id = new_experiment(args.model_name, args.HPC, args.model_branch, args.template_name, args.template_branch, args.ocean_diagnostics_branch, args.description)
		os.mkdir(DB_DIR + exp_id)
		##now templates are checked out with a git clone 
		##destination path must be an existing empty directory
		os.mkdir(DB_DIR + exp_id + '/git')
		if (args.model_name == 'dummy'):# or args.template_name == 'dummy'):
			shutil.copytree("../templates", DB_DIR + exp_id + "/git/templates")
		else:
			print "Checking out templates and config files..."
			if args.template_branch is not 'master':
				(status, output) = getstatusoutput("git clone -b " + args.template_branch + " " + GIT_DIR + "/templates.git " + DB_DIR + exp_id + "/git/templates")
			else:
				(status, output) = getstatusoutput("git clone " + GIT_DIR + "/templates.git " + DB_DIR + exp_id + "/git/templates")
			
			autosubmit_version_filename = "../VERSION"
			template_version_filename = LOCAL_ROOT_DIR + "/" + exp_id + "/git/templates/VERSION"
			
			if not check_compatibility(autosubmit_version_filename, template_version_filename):
				print "Compatibility check FAILED!"
				print_compatibility()
				print "WARNING: running after FAILED compatibility check is at your own risk!!!"
			else:
				print "Compatibility check PASSED!"


			##now ocean diagnostics are checked out with a git clone 
			print "Checking out ocean diagnostics..."
			if args.ocean_diagnostics_branch is not 'master':
				(status, output) = getstatusoutput("git clone -b " + args.ocean_diagnostics_branch + " " + GIT_DIR + "/ocean_diagnostics.git " + DB_DIR + exp_id + "/git/ocean_diagnostics")
			else:
				(status, output) = getstatusoutput("git clone " + GIT_DIR + "/ocean_diagnostics.git " + DB_DIR + exp_id + "/git/ocean_diagnostics") 

			print "Checking out model sources..."
			#repo = Repo(GIT_DIR + "/" + args.model_name + ".git")
			#cloned_repo = repo.clone(DB_DIR + exp_id)
			#if args.model_branch:
			#	cloned_repo.checkout('head', b=args.model_branch) 
			if args.model_branch is not 'master':
				(status, output) = getstatusoutput("git clone -b " + args.model_branch + " " + GIT_DIR + "/" + args.model_name + ".git " + DB_DIR + exp_id + "/git/model")
			else:
				(status, output) = getstatusoutput("git clone " + GIT_DIR + "/" + args.model_name + ".git " + DB_DIR + exp_id + "/git/model")

		os.mkdir(DB_DIR + exp_id + '/conf')
		print "Copying config files..."
		##autosubmit config and architecture copyed from AS.
		files = os.listdir('../conf')
		for filename in files:
			if os.path.isfile('../conf/' + filename):
				index = filename.index('.')
				new_filename = filename[:index] + "_" + exp_id + filename[index:]
				content = file('../conf/' + filename, 'r').read()
				content = prepare_conf_files(content, exp_id, args.HPC, args.template_name, autosubmit_version)
				print DB_DIR + exp_id + "/conf/" + new_filename
				file(DB_DIR + exp_id + "/conf/" + new_filename, 'w').write(content)

		# merge expdef config and common and template config files
		## probably not needed if autosubmit read separate files (this would break backwards compatibility)
		## separate files would be useful to track versions per run ?
		content = file(DB_DIR + exp_id + "/conf/expdef_" + exp_id + ".conf").read()
		content += file(DB_DIR + exp_id + "/git/templates/common/common.conf").read()
		content += file(DB_DIR + exp_id + "/git/templates/" + args.template_name + "/" + args.template_name + ".conf").read()
		file(DB_DIR + exp_id + "/conf/expdef_" + exp_id + ".conf", 'w').write(content)

	elif args.copy:
		if os.path.exists(DB_DIR + args.copy):
			exp_id = copy_experiment(args.copy, args.HPC, args.model_branch, args.template_name, args.template_branch, args.ocean_diagnostics_branch, args.description)
			os.mkdir(DB_DIR + exp_id)
			os.mkdir(DB_DIR + exp_id + '/conf')
			print "Copying previous experiment config directories"
			files = os.listdir(DB_DIR + args.copy + "/conf")
			for filename in files:
				if os.path.isfile(DB_DIR + args.copy + "/conf/" + filename):
					new_filename = filename.replace(args.copy, exp_id)
					content = file(DB_DIR + args.copy + "/conf/" + filename, 'r').read()
					content = prepare_conf_files(content, exp_id, args.HPC, args.template_name, autosubmit_version)
					file(DB_DIR + exp_id + "/conf/" + new_filename, 'w').write(content)
			# think in a way to do that for experiments which git directory had been cleaned ( git clone ? )
			dirs = os.listdir(DB_DIR + args.copy + "/git")
			if (dirs):
				print "Cloning previous experiment templates, ocean diagnostics and model sources..."
				# what to do with configs that are coming from new template ?
				for dirname in dirs:
					if os.path.isdir(DB_DIR + args.copy + "/git/" + dirname):
						if os.path.isdir(DB_DIR + args.copy + "/git/" + dirname + "/.git"):
							(status, output) = getstatusoutput("git clone " + DB_DIR + args.copy + "/git/" + dirname + " " + DB_DIR + exp_id + "/git/" + dirname)
						else:
							shutil.copytree(DB_DIR + args.copy + "/git/" + dirname, DB_DIR + exp_id + "/git/" + dirname)
			else:
				print "Checking out templates and config files..."
				(status, output) = getstatusoutput("git clone -b " + args.template_branch + " " + GIT_DIR + "/templates.git " + DB_DIR + exp_id + "/git/templates")		
				print "Checking out ocean diagnostics..."
				(status, output) = getstatusoutput("git clone -b " + args.ocean_diagnostics_branch + " " + GIT_DIR + "/ocean_diagnostics.git " + DB_DIR + exp_id + "/git/ocean_diagnostics")
				print "Checking out model sources..."
				(status, output) = getstatusoutput("git clone -b " + args.model_branch + " " + GIT_DIR + "/" + args.model_name + ".git " + DB_DIR + exp_id + "/git/model")
			
			autosubmit_version_filename = "../VERSION"
			template_version_filename = LOCAL_ROOT_DIR + "/" + exp_id + "/git/templates/VERSION"
			
			if not check_compatibility(autosubmit_version_filename, template_version_filename):
				print "Compatibility check FAILED!"
				print_compatibility()
				print "WARNING: running after FAILED compatibility check is at your own risk!!!"
			else:
				print "Compatibility check PASSED!"

			#shutil.copytree(DB_DIR+args.copy+"/git", DB_DIR + exp_id + "/git")
		else:
			print "The previous experiment directory does not exist"
			sys.exit(1)
	
	content = file("../conf/archdef/" + args.HPC + ".conf").read()
	content += file("../conf/archdef/common.conf").read()
	file(DB_DIR + exp_id + "/conf/archdef_" + exp_id + ".conf", 'w').write(content)
	print "Creating temporal directory..."
	os.mkdir(DB_DIR+exp_id+"/"+"tmp")
	print "Creating pkl directory..."
	os.mkdir(DB_DIR+exp_id+"/"+"pkl")
	print "Creating plot directory..."
	os.mkdir(DB_DIR+exp_id+"/"+"plot")
	os.chmod(DB_DIR+exp_id+"/"+"plot",0o775)
	print "Remember to MODIFY the config files!"
