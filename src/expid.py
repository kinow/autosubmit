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


import string
from pysqlite2 import dbapi2 as sql
import sys, os
import argparse
import shutil
import re
import dir_config
from dir_config import LOCAL_ROOT_DIR
from dir_config import DB_DIR, DB_FILE, DB_NAME
from dir_config import GIT_DIR
from commands import getstatusoutput
from check_compatibility import check_compatibility, print_compatibility

# Database parameters
#DB_DIR = '/cfu/autosubmit/'
#DB_FILE = 'ecearth.db'
#DB_NAME = 'ecearth'

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

def set_experiment(name, description):
	check_db()
	name = check_name(name)

	(conn, cursor) = open_conn()
	try:
		cursor.execute('insert into experiment (name, description) values (:name, :description)', {'name':name, 'description':description})
	except sql.IntegrityError:
		close_conn(conn, cursor)
		print 'The experiment name %s already exists!!!' % (name)
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
	cursor.execute('select name from experiment where name=:name', {'name':name})
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

def new_experiment(HPC, description):
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
	set_experiment(new_name, description)
	print 'The new experiment "%s" has been registered.' % new_name
	return new_name

def copy_experiment(name, HPC, description):
	new_exp = get_experiment(name)
	new_name = new_experiment(HPC, description)
	return new_name

def delete_experiment(name):
	check_db()
	name = check_name(name)
	(conn, cursor) = open_conn()
	cursor.execute('delete from experiment where name=:name', {'name':name})
	row = cursor.fetchone()
	if row == None:
		close_conn(conn, cursor)
		print 'The experiment name %s does not exist yet!!!' % name
		sys.exit(1)

	close_conn(conn, cursor)
	return

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
def prepare_conf_files(content, exp_id, hpc, autosubmit_version):
	if re.search('EXPID =.*', content):
		content = content.replace(re.search('EXPID =.*', content).group(0), "EXPID = " + exp_id)
	if re.search('HPCARCH =.*', content):
		content = content.replace(re.search('HPCARCH =.*', content).group(0), "HPCARCH = " + hpc)
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
	group1.add_argument('--delete', '-D', type = str)
	group2 = parser.add_argument_group('experiment arguments')
	group2.add_argument('--HPC', '-H', choices = ('bsc', 'hector', 'ithaca', 'lindgren', 'ecmwf', 'marenostrum3', 'archer'), required = True)
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
		##  --HPC  --description
		exp_id = new_experiment(args.HPC, args.description)
		os.mkdir(DB_DIR + exp_id)
		
		os.mkdir(DB_DIR + exp_id + '/conf')
		print "Copying config files..."
		##autosubmit config and architecture copyed from AS.
		files = os.listdir('../conf')
		for filename in files:
			if os.path.isfile('../conf/' + filename):
				index = filename.index('.')
				new_filename = filename[:index] + "_" + exp_id + filename[index:]
				content = file('../conf/' + filename, 'r').read()
				content = prepare_conf_files(content, exp_id, args.HPC, autosubmit_version)
				print DB_DIR + exp_id + "/conf/" + new_filename
				file(DB_DIR + exp_id + "/conf/" + new_filename, 'w').write(content)

		content = file(DB_DIR + exp_id + "/conf/expdef_" + exp_id + ".conf").read()
		file(DB_DIR + exp_id + "/conf/expdef_" + exp_id + ".conf", 'w').write(content)

	elif args.copy:
		if os.path.exists(DB_DIR + args.copy):
			exp_id = copy_experiment(args.copy, args.HPC, args.description)
			os.mkdir(DB_DIR + exp_id)
			os.mkdir(DB_DIR + exp_id + '/conf')
			print "Copying previous experiment config directories"
			files = os.listdir(DB_DIR + args.copy + "/conf")
			for filename in files:
				if os.path.isfile(DB_DIR + args.copy + "/conf/" + filename):
					new_filename = filename.replace(args.copy, exp_id)
					content = file(DB_DIR + args.copy + "/conf/" + filename, 'r').read()
					content = prepare_conf_files(content, exp_id, args.HPC, autosubmit_version)
					file(DB_DIR + exp_id + "/conf/" + new_filename, 'w').write(content)
		else:
			print "The previous experiment directory does not exist"
			sys.exit(1)
	
	elif args.delete:
		if os.path.exists(DB_DIR + args.delete):
			os.rmdir(DB_DIR + args.delete)
			print "Removing experiment..."
		delete_experiment(args.delete)
	
	content = file("../conf/platforms/" + args.HPC + ".conf").read()
	#content += file("../conf/archdef/common.conf").read()
	file(DB_DIR + exp_id + "/conf/archdef_" + exp_id + ".conf", 'w').write(content)
	print "Creating temporal directory..."
	os.mkdir(DB_DIR+exp_id+"/"+"tmp")
	print "Creating pkl directory..."
	os.mkdir(DB_DIR+exp_id+"/"+"pkl")
	print "Creating plot directory..."
	os.mkdir(DB_DIR+exp_id+"/"+"plot")
	os.chmod(DB_DIR+exp_id+"/"+"plot",0o775)
	print "Remember to MODIFY the config files!"
