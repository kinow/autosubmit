#!/usr/bin/env python

import string
from pysqlite2 import dbapi2 as sql
import sys, os
import argparse
import shutil
import re

# Database parameters
DB_DIR = '/cfu/autosubmit/'
DB_FILE = 'ecearth.db'
DB_NAME = 'ecearth'

DB_PATH = DB_DIR + DB_FILE

DEFAULT_EXPID_BSC = "b000"
DEFAULT_EXPID_HEC = "h000"
DEFAULT_EXPID_ITH = "i000"
DEFAULT_EXPID_LIN = "l000"
DEFAULT_EXPID_ECM = "e000"
DEFAULT_EXPID_MN3 = "m000"

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

def set_experiment(name, exp_type, description):
	check_db()
	name = check_name(name)

	(conn, cursor) = open_conn()
	try:
		cursor.execute('insert into experiment values(null, ?, ?, ?, null, null, null, null)', (name, exp_type, description))
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
	cursor.execute('select name from experiment where rowid=(select max(rowid) from experiment where name LIKE "' + hpc_name + '")')
	row = cursor.fetchone()
	if row == None:
		row = ('empty', )
	close_conn(conn,cursor)
	return row[0]

def new_experiment(exp_type, HPC, description):
	last_exp_name = last_name(HPC)
	if last_exp_name == 'empty':
		if HPC == 'bsc':
			new_name = DEFAULT_EXPID_BSC
		elif HPC == "hector":
			new_name = DEFAULT_EXPID_HEC
		elif HPC == 'ithaca':
			new_name = DEFAULT_EXPID_ITH
		elif HPC == 'lindgren':
			new_name = DEFAULT_EXPID_LIN
		elif HPC == 'ecmwf':
			new_name = DEFAULT_EXPID_ECM
		elif HPC == 'marenostrum3':
			new_name = DEFAULT_EXPID_MN3
	else:
		new_name = next_name(last_exp_name)
	set_experiment(new_name, exp_type, description)
	print 'Thew new experiment "%s" has been registered.' % new_name
	return new_name

def copy_experiment(name, HPC, description):
	new_exp = get_experiment(name)
	new_name = new_experiment(new_exp[1], HPC, description)
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
def prepare_conf_files(content, exp_id, hpc):
	replace_strings = ['REMOTE_DIR =', 'ECEARTH_DIR =.']
	if re.search('EXPID =.*', content):
		content = content.replace(re.search('EXPID =.*', content).group(0), "EXPID = " + exp_id)
	if re.search('HPCARCH =.*', content):
		content = content.replace(re.search('HPCARCH =.*', content).group(0), "HPCARCH = " + hpc)
	if re.search('SAFETYSLEEPTIME =.*', content):
		if hpc == "bsc":
			content = content.replace(re.search('SAFETYSLEEPTIME =.*', content).group(0), "SAFETYSLEEPTIME = 10")
		elif hpc == "hector":
			content = content.replace(re.search('SAFETYSLEEPTIME =.*', content).group(0), "SAFETYSLEEPTIME = 10")
		elif hpc == "ithaca":
			content = content.replace(re.search('SAFETYSLEEPTIME =.*', content).group(0), "SAFETYSLEEPTIME = 10")
		elif hpc == "lindgren":
			content = content.replace(re.search('SAFETYSLEEPTIME =.*', content).group(0), "SAFETYSLEEPTIME = 300")
		elif hpc == "ecmwf":
			content = content.replace(re.search('SAFETYSLEEPTIME =.*', content).group(0), "SAFETYSLEEPTIME = 300")
		elif hpc == "marenostrum3": 
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

	return content


#############################
# Main function
#############################
if __name__ == "__main__":

	parser = argparse.ArgumentParser()
	group = parser.add_mutually_exclusive_group()
	group.add_argument('--new', '-n', nargs = 1, choices = ('ecearth', 'ecearth3', 'ifs', 'ifs3', 'nemo'))
	group.add_argument('--copy', '-c', nargs = 1)
	parser.add_argument('--HPC', '-H', nargs = 1, choices = ('bsc', 'hector', 'ithaca', 'lindgren', 'ecmwf', 'marenostrum3'))
	parser.add_argument('--description', '-d', nargs = 1)

	args = parser.parse_args()
	if args.description is None:
		parser.error("Missing experiment description.")
	if args.HPC is None:
		parser.error("Missing HPC.");

	if args.new is None and args.copy is None:
		parser.error("Missing method either New or Copy.")
	if args.new:
		exp_id = new_experiment(args.new[0], args.HPC[0], args.description[0])
		os.mkdir(DB_DIR + exp_id)
		os.mkdir(DB_DIR + exp_id + '/conf')
		os.mkdir(DB_DIR + exp_id + '/templates')
		print "Copying config files..."
		files = os.listdir('../conf')
		for filename in files:
			if os.path.isfile('../conf/' + filename):
				index = filename.index('.')
				new_filename = filename[:index] + "_" + exp_id + filename[index:]
				content = file('../conf/' + filename, 'r').read()
				content = prepare_conf_files(content, exp_id, args.HPC[0])
				print DB_DIR + exp_id + "/conf/" + new_filename
				file(DB_DIR + exp_id + "/conf/" + new_filename, 'w').write(content)

		print "Copying templates files..."
		# list all files in templates of type args.new[0]
		print args.new[0]
		print os.listdir('../templates/' + args.new[0])
		files = [f for f in os.listdir('../templates/' + args.new[0]) if os.path.isfile('../templates/' + args.new[0] + "/" + f)]
		extensions = set( f[f.index('.'):] for f in files)
		# merge header and body of template
		for ext in extensions:
			content = file("../headers/" + args.new[0] + "/" + args.HPC[0] + ext).read()
			content += file("../templates/" + args.new[0] + "/" + args.new[0] + ext).read()
			file(DB_DIR + exp_id + "/templates/" + "template_" + exp_id + ext, 'w').write(content)
		# list all files in common templates
		print os.listdir('../templates/common')
		files = [f for f in os.listdir('../templates/common') if os.path.isfile('../templates/common' + "/" + f)]
		extensions= set( f[f.index('.'):] for f in files)
		# merge header and body of common template
		for ext in extensions:
			content = file("../headers/common" + "/" + args.HPC[0] + ext).read()
			content += file("../templates/common" + "/" + "common" + ext).read()
			file(DB_DIR + exp_id + "/templates/" + "template_" + exp_id + ext, 'w').write(content)

	elif args.copy:
		if os.path.exists(DB_DIR + args.copy[0]):
			exp_id = copy_experiment(args.copy[0], args.HPC[0], args.description[0])
			os.mkdir(DB_DIR + exp_id)
			os.mkdir(DB_DIR + exp_id + '/conf')
			print "Copying previous experiment config and templates directories"
			files = os.listdir(DB_DIR + args.copy[0] + "/conf")
			for filename in files:
				if os.path.isfile(DB_DIR + args.copy[0] + "/conf/" + filename):
					new_filename = filename.replace(args.copy[0], exp_id)
					content = file(DB_DIR + args.copy[0] + "/conf/" + filename, 'r').read()
					content = prepare_conf_files(content, exp_id, args.HPC[0])
					file(DB_DIR + exp_id + "/conf/" + new_filename, 'w').write(content)
			shutil.copytree(DB_DIR+args.copy[0]+"/templates", DB_DIR + exp_id + "/templates")
		else:
			print "The previous experiment directory does not exist"
			sys.exit(1)
	
	shutil.copy('../conf/archdef/' + args.HPC[0] + ".conf", DB_DIR + exp_id + "/conf/archdef_" + exp_id + ".conf")
	if args.new[0] == "ecearth" or args.new[0] == "ecearth3" or args.new[0] == "nemo":
		shutil.copy('../postp/ocean/common_ocean_post.txt', DB_DIR + exp_id + "/templates/")
	print "Creating temporal directory..."
	os.mkdir(DB_DIR+exp_id+"/"+"tmp")
	print "Creating pkl directory..."
	os.mkdir(DB_DIR+exp_id+"/"+"pkl")
	print "Creating plot directory..."
	os.mkdir(DB_DIR+exp_id+"/"+"plot")
	os.chmod(DB_DIR+exp_id+"/"+"plot",0o775)
	print "Remember to MODIFY the config files!"
