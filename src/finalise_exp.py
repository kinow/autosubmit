#!/usr/bin/env python
"""Functions for finalise experiment. 
Registering in the DB the commit SHA of the templates, and model project version.
Cleaning space on LOCAL_ROOT_DIR/git directory by using git clean.
Cleaning space on LOCAL_ROOT_DIR/plot directory.
Use these functions for finalised experiments."""
from dir_config import LOCAL_ROOT_DIR, DB_DIR, DB_FILE, DB_NAME
import argparse
from os import path
from pysqlite2 import dbapi2 as sql

DB_PATH = DB_DIR + DB_FILE

def open_conn():
	conn = sql.connect(DB_PATH)
	cursor = conn.cursor()
	return (conn, cursor)

def close_conn(conn,cursor):
	conn.commit()
	cursor.close()
	conn.close()
	return

def check_db():
	if not path.exists(DB_PATH):
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

def get_experiment(name):
	check_db()
	name = check_name(name)

	(conn, cursor) = open_conn()

	# SQLite always return a unicode object, but we can change this
	# behaviour with the next sentence
	conn.text_factory = str
	cursor.execute('select * from experiment where name=?', (name,))
	row = cursor.fetchone()
	if row == None:
		close_conn(conn, cursor)
		print 'The experiment name %s does not exist yet!!!' % name
		sys.exit(1)

	close_conn(conn, cursor)
	return row

def set_experiment(name, model_name, model_branch, template_name, template_branch, ocean_diagnostics_branch, description):
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



def register_sha(expid):
	"""Function to register in the DB the commit SHA of the template and the model project versions."""
	exp = get_experiment(expid)
	print exp
	# check expdef_cxxx
	model_name = exp[2]
	(status, output) = getstatusoutput("cd " + LOCAL_ROOT_DIR + "/git/model/" + "; " + "git branch")
	if (status):
		model_branch = output
	else:
		print "Failed to retrieve template SHA..."
		sys.exit(1)
	(status, output) = getstatusoutput("cd " + LOCAL_ROOT_DIR + "/git/model/" + "; " + "git rev-parse HEAD")
	if (status):
		model_sha = output
		print "Model SHA is: " + model_sha
	else: 
		print "Failed to retrieve template SHA..."
		sys.exit(1)
	model_name_sha = model_name + " " + model_sha

	# check expdef_cxxx
	template_name = exp[5]
	(status, output) = getstatusoutput("cd " + LOCAL_ROOT_DIR + "/git/templates/" + "; " + "git branch")
	if (status):
		template_branch = output
	else:
		print "Failed to retrieve template branch..."
		sys.exit(1)
	(status, output) = getstatusoutput("cd " + LOCAL_ROOT_DIR + "/git/templates/" + "; " + "git rev-parse HEAD")
	if (status):
		template_sha = output
		print "Template SHA is: " + template_sha
	else: 
		print "Failed to retrieve template SHA..."
		sys.exit(1)
	template_branch_sha = template_branch + " " + template_sha

	set_experiment(expid, model_name, model_branch_sha, template_name, template_branch_sha)
	

def clean_git():
	"""Function to clean space on LOCAL_ROOT_DIR/git directory."""
	#(status, output) = getstatusoutput("cd " + LOCAL_ROOT_DIR + "/git/templates/" + "; " + "git clean")


def clean_plot():
	"""Function to clean space on LOCAL_ROOT_DIR/plot directory."""
	

####################
# Main Program
####################
if __name__ == "__main__":

	parser = argparse.ArgumentParser(description='Clean autosubmit finalised experiments directory given a experiment identifier')
	parser.add_argument('-e', '--expid', required=True, nargs = 1)
	args = parser.parse_args()
	if args.expid is None:
		parser.error("Missing expid.")
	
	print "Looking for model and template commit SHA..."
	register_sha(args.expid[0])
	print "SHA for model and template succesfully registered in the database."
	#print "Cleaning GIT directory..."
	#clean_git(args.expid[0])
	#print "GIT directory clean! further runs will require checkout model and templates again"
	#print "Cleaning plot directory..."
	#clean_plot(args.expid[0])
	#print "Plot directory clean! last two plots remanining there."

