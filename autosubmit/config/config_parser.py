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

import sys
import re
from pyparsing import nestedExpr
from os import path
from ConfigParser import SafeConfigParser

invalid_values = False


def check_values(key, value, valid_values):
    global invalid_values

    if value.lower() not in valid_values:
        print "Invalid value %s: %s" % (key, value)
        invalid_values = True


def check_regex(key, value, regex):
    global invalid_values

    prog = re.compile(regex)

    if not prog.match(value.lower()):
        print "Invalid value %s: %s" % (key, value)
        invalid_values = True


def check_json(key, value):
    global invalid_values

    # noinspection PyBroadException
    try:
        nestedExpr('[', ']').parseString(value).asList()
    except:
        print "Invalid value %s: %s" % (key, value)
        invalid_values = True


def config_parser(filename):
    loglevel = ['debug', 'info', 'warning', 'error', 'critical']

    # check file existance
    if not path.isfile(filename):
        print "File does not exist: " + filename
        sys.exit()

    # load values
    parser = SafeConfigParser()
    parser.optionxform = str
    parser.read(filename)

    check_values('LOGLEVEL', parser.get('config', 'LOGLEVEL'), loglevel)

    if invalid_values:
        print "Invalid Autosubmit config file"
        sys.exit()
    else:
        print "Autosubmit config file OK"

    return parser


def expdef_parser(filename):
    hpcarch = ['bsc', 'ithaca', 'lindgren', 'ecmwf', 'marenostrum3', 'hector', 'archer']
    hpcproj = "\s*[\w\-]+\s*$"
    hpcuser = "\s*[\w\-]+\s*$"
    startdate = "(\s*[0-9]{4}[0-9]{2}[0-9]{2}\s*)+$"
    chunkini = "\s*\d+\s*$"
    numchunks = "\s*\d+\s*$"
    chunksize = "\s*\d+\s*$"
    members = "(\s*fc\d+\s*)+$"
    rerun = "\s*(true|false)\s*$"
    projecttype = ['git', 'svn', 'local', 'none']
    projectname = "\s*[\w\-]+\s*$"
    wallclock = "\s*\d\d:\d\d\s*$"
    numproc = "\s*\d+\s*$"
    multiproc = "\s*\d+(:\d+)*\s*$"
    
    #option that must be in config file and has no default value
    mandatory_opt = ['EXPID']

    # check file existance
    if not path.isfile(filename):
        print "File does not exist: " + filename 
        sys.exit()

    # load values
    parser = SafeConfigParser()
    parser.optionxform = str
    parser.read(filename)

    # check which options of the mandatory one are not in config file
    missing = list(set(mandatory_opt).difference(parser.options('experiment')))
    if missing:
        print "Missing options"
        print missing
        sys.exit()

    # check autosubmit.py variables
    check_values('HPCARCH', parser.get('experiment', 'HPCARCH'), hpcarch)
    check_regex('HPCPROJ', parser.get('experiment', 'HPCPROJ'), hpcproj)
    check_regex('HPCUSER', parser.get('experiment', 'HPCUSER'), hpcuser)
    check_regex('WALLCLOCK_SETUP', parser.get('wallclocks', 'WALLCLOCK_SETUP'), wallclock)
    check_regex('WALLCLOCK_INI', parser.get('wallclocks', 'WALLCLOCK_INI'), wallclock)
    check_regex('WALLCLOCK_SIM', parser.get('wallclocks', 'WALLCLOCK_SIM'), wallclock)
    check_regex('WALLCLOCK_POST', parser.get('wallclocks', 'WALLCLOCK_POST'), wallclock)
    check_regex('WALLCLOCK_CLEAN', parser.get('wallclocks', 'WALLCLOCK_CLEAN'), wallclock)
    check_regex('NUMPROC_SETUP', parser.get('numprocs', 'NUMPROC_SETUP'), numproc)
    check_regex('NUMPROC_INI', parser.get('numprocs', 'NUMPROC_INI'), numproc)
    check_regex('NUMPROC_SIM', parser.get('numprocs', 'NUMPROC_SIM'), multiproc)
    check_regex('NUMTASK_SIM', parser.get('numprocs', 'NUMTASK_SIM'), multiproc)
    check_regex('NUMTHREAD_SIM', parser.get('numprocs', 'NUMTHREAD_SIM'), multiproc)
    check_regex('NUMPROC_POST', parser.get('numprocs', 'NUMPROC_POST'), numproc)
    check_regex('NUMPROC_CLEAN', parser.get('numprocs', 'NUMPROC_CLEAN'), numproc)

    # check create_exp.py variables
    check_regex('DATELIST', parser.get('experiment', 'DATELIST'), startdate)
    check_regex('MEMBERS', parser.get('experiment', 'MEMBERS'), members)
    check_regex('CHUNKINI', parser.get('experiment', 'CHUNKINI'), chunkini)
    check_regex('NUMCHUNKS', parser.get('experiment', 'NUMCHUNKS'), numchunks)
    check_regex('CHUNKSIZE', parser.get('experiment', 'CHUNKSIZE'), chunksize)
    check_regex('RERUN', parser.get('rerun', 'RERUN'), rerun)
    if parser.get('rerun', 'RERUN') == "TRUE":
        check_json('CHUNKLIST', parser.get('rerun', 'CHUNKLIST'))
    check_values('PROJECT_TYPE', parser.get('project', 'PROJECT_TYPE'), projecttype)
    check_regex('PROJECT_NAME', parser.get('project', 'PROJECT_NAME'), projectname)
    #if (parser.get('project', 'PROJECT_TYPE') == "git"):
    #   check_regex('PROJECT_ORIGIN', parser.get('git', 'PROJECT_ORIGIN'), gitorigin)

    if invalid_values:
        print "Invalid experiment config file"
        sys.exit()
    else:
        print "Experiment config file OK"

    return parser

def projdef_parser(filename):

    # check file existance
    if not path.isfile(filename):
        print "File does not exist: " + filename
        sys.exit()

    # load values
    parser = SafeConfigParser()
    parser.optionxform = str
    parser.read(filename)

    if invalid_values:
        print "Invalid model config file"
        sys.exit()
    else:
        print "Model config file OK"

    return parser


####################
# Main Program
####################
def main():
    if len(sys.argv) != 2:
        print "Error missing config file"
    else:
        autosubmit_conf_parser(sys.argv[1])


if __name__ == "__main__":
    main()
