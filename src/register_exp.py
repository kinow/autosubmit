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

"""Functions for registering in the DB the commit SHA of the GIT projects version.
Use these functions for registering GIT version of templates, model and ocean diagnosics under development."""
from dir_config import LOCAL_ROOT_DIR, DB_DIR, DB_FILE, DB_NAME
import argparse
from os import path
from sys import exit
from pysqlite2 import dbapi2 as sql
from commands import getstatusoutput

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
		exit(1)
	return

def check_name(name):
	name = name.lower()
	if len(name) != 4 and not name.isalnum():
		print "So sorry, but the name must have 4 alphanumeric chars!!!"
		exit(1)
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
		exit(1)

	close_conn(conn, cursor)
	return row

def set_experiment(name, model_name, model_branch, template_name, template_branch, ocean_diagnostics_branch):
	check_db()
	name = check_name(name)

	(conn, cursor) = open_conn()
	try:
		cursor.execute('update experiment set type=:model_name, model_branch=:model_branch, template_name=:template_name, template_branch=:template_branch, ocean_diagnostics_branch=:ocean_diagnostics_branch where name=:name', {'name':name, 'model_name':model_name, 'model_branch':model_branch, 'template_name':template_name, 'template_branch':template_branch, 'ocean_diagnostics_branch':ocean_diagnostics_branch})
	except sql.IntegrityError:
		close_conn(conn, cursor)
		print 'The experiment name %s - %s already exists!!!' % (name, exp_type)
		exit(1)

	conn.commit()
	close_conn(conn, cursor)
	return



def register_sha(expid, save):
	"""Function to register in the DB the commit SHA of the template, model and ocean diagnostics project versions."""
	exp = get_experiment(expid)
	print exp

	# check model
	# check expdef_cxxx ?
	model_name = exp[2]
	(status1, output) = getstatusoutput("cd " + LOCAL_ROOT_DIR + "/" + expid + "/git/model/")
	(status2, output) = getstatusoutput("cd " + LOCAL_ROOT_DIR + "/" + expid + "/git/model/" + "; " + "git rev-parse --abbrev-ref HEAD")
	if (status1 == 0 and status2 == 0):
		model_branch = output
		print "Model branch is: " + model_branch
	else:
		print "Failed to retrieve model branch..." 
		exit(1)
	(status1, output) = getstatusoutput("cd " + LOCAL_ROOT_DIR + "/" + expid + "/git/model/")
	(status2, output) = getstatusoutput("cd " + LOCAL_ROOT_DIR + "/" + expid + "/git/model/" + "; " + "git rev-parse HEAD")
	if (status1 == 0 and status2 == 0):
		model_sha = output
		print "Model SHA is: " + model_sha
	else: 
		print "Failed to retrieve model SHA..."
		exit(1)
	model_branch_sha = model_branch + " " + model_sha

	# check templates
	# check expdef_cxxx ?
	template_name = exp[5]
	(status1, output) = getstatusoutput("cd " + LOCAL_ROOT_DIR + "/" + expid + "/git/templates/")
	(status2, output) = getstatusoutput("cd " + LOCAL_ROOT_DIR + "/" + expid + "/git/templates/" + "; " + "git rev-parse --abbrev-ref HEAD")
	if (status1 == 0 and status2 == 0):
		template_branch = output
		print "Template branch is: " + template_branch
	else:
		print "Failed to retrieve template branch..."
		exit(1)
	(status1, output) = getstatusoutput("cd " + LOCAL_ROOT_DIR + "/" + expid + "/git/templates/")
	(status2, output) = getstatusoutput("cd " + LOCAL_ROOT_DIR + "/" + expid + "/git/templates/" + "; " + "git rev-parse HEAD")
	if (status1 == 0 and status2 == 0):
		template_sha = output
		print "Template SHA is: " + template_sha
	else: 
		print "Failed to retrieve template SHA..."
		exit(1)
	template_branch_sha = template_branch + " " + template_sha

	# check ocean diagnostics
	(status1, output) = getstatusoutput("cd " + LOCAL_ROOT_DIR + "/" + expid + "/git/ocean_diagnostics/")
	(status2, output) = getstatusoutput("cd " + LOCAL_ROOT_DIR + "/" + expid + "/git/ocean_diagnostics/" + "; " + "git rev-parse --abbrev-ref HEAD")
	if (status1 == 0 and status2 == 0):
		ocean_diagnostics_branch = output
		print "Ocean diagnostics branch is: " + ocean_diagnostics_branch
	else:
		print "Failed to retrieve ocean diagnostics branch..."
		exit(1)
	(status1, output) = getstatusoutput("cd " + LOCAL_ROOT_DIR + "/" + expid + "/git/ocean_diagnostics/")
	(status2, output) = getstatusoutput("cd " + LOCAL_ROOT_DIR + "/" + expid + "/git/ocean_diagnostics/" + "; " + "git rev-parse HEAD")
	if (status1 == 0 and status2 == 0):
		ocean_diagnostics_sha = output
		print "Ocean diagnostics SHA is: " + ocean_diagnostics_sha
	else: 
		print "Failed to retrieve ocean diagnostics SHA..."
		exit(1)
	ocean_diagnostics_branch_sha = ocean_diagnostics_branch + " " + ocean_diagnostics_sha
	
	# register changes
	if (save):
		set_experiment(expid, model_name, model_branch_sha, template_name, template_branch_sha, ocean_diagnostics_branch_sha)
		print "SHA for model, templates and ocean_diagnostics succesfully registered to the database."
	else:
		print "Changes NOT registered to the database..."
	
####################
# Main Program
####################
if __name__ == "__main__":

	parser = argparse.ArgumentParser(description='Register experiment GIT directory changes to database, given an experiment identifier')
	parser.add_argument('-e', '--expid', required=True, nargs = 1, help='Give an experiment identifier...')
	parser.add_argument('-s', '--save', action="store_true", default=False, help='Save changes to database')
	args = parser.parse_args()
	if args.expid is None:
		parser.error("Missing expid.")
	
	print "Looking for model, templates and ocean_diagnostics commit SHA..."
	register_sha(args.expid[0], args.save)
