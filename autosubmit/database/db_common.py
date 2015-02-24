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

import os
import sys
import sqlite3
import string

from autosubmit.config.dir_config import DB_DIR
from autosubmit.config.dir_config import DB_FILE

# Database parameters
# DB_DIR = '/cfu/autosubmit'
# DB_FILE = 'ecearth.db'
# DB_NAME = 'ecearth'

DB_PATH = DB_DIR + "/" + DB_FILE

DEFAULT_EXPID_BSC = "b000"
DEFAULT_EXPID_HEC = "h000"
DEFAULT_EXPID_ITH = "i000"
DEFAULT_EXPID_LIN = "l000"
DEFAULT_EXPID_ECM = "e000"
DEFAULT_EXPID_MN3 = "m000"
DEFAULT_EXPID_ARC = "a000"


def set_experiment(name, description):
    check_db()
    name = check_name(name)

    (conn, cursor) = open_conn()
    try:
        cursor.execute('insert into experiment (name, description) values (:name, :description)',
                       {'name': name, 'description': description})
    except sqlite3.IntegrityError:
        close_conn(conn, cursor)
        print 'The experiment name %s already exists!!!' % name
        sys.exit(1)

    conn.commit()
    close_conn(conn, cursor)
    return


def check_experiment_exists(name):
    """
    Checks if exist an experiment with the given name.
    :param name: Experiment name
    :return: If experiment exists returns true, if not returns false
    """
    check_db()
    name = check_name(name)

    (conn, cursor) = open_conn()

    # SQLite always return a unicode object, but we can change this
    # behaviour with the next sentence
    conn.text_factory = str
    cursor.execute('select name from experiment where name=:name', {'name': name})
    row = cursor.fetchone()
    close_conn(conn, cursor)
    if row is None:
        print 'The experiment name %s does not exist yet!!!' % name
        return False
    return True


def new_experiment(hpc, description):
    last_exp_name = last_name(hpc)
    if last_exp_name == 'empty':
        if hpc == 'bsc':
            new_name = DEFAULT_EXPID_BSC
        elif hpc == 'hector':
            new_name = DEFAULT_EXPID_HEC
        elif hpc == 'ithaca':
            new_name = DEFAULT_EXPID_ITH
        elif hpc == 'lindgren':
            new_name = DEFAULT_EXPID_LIN
        elif hpc == 'ecmwf':
            new_name = DEFAULT_EXPID_ECM
        elif hpc == 'marenostrum3':
            new_name = DEFAULT_EXPID_MN3
        elif hpc == 'archer':
            new_name = DEFAULT_EXPID_ARC
        else:
            raise ValueError('%c is not a valid HPC name' % hpc)
    else:
        new_name = next_name(last_exp_name)
    set_experiment(new_name, description)
    print 'The new experiment "%s" has been registered.' % new_name
    return new_name


def copy_experiment(name, hpc, description):
    if not check_experiment_exists(name):
        exit(1)
    new_name = new_experiment(hpc, description)
    return new_name


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
    # Convert the name to base 36 in number add 1 and then encode it
    return base36encode(base36decode(name) + 1)


def last_name(hpc):
    check_db()
    (conn, cursor) = open_conn()
    conn.text_factory = str
    if hpc == 'bsc':
        hpc_name = "b___"
    elif hpc == "hector":
        hpc_name = "h___"
    elif hpc == 'ithaca':
        hpc_name = "i___"
    elif hpc == 'lindgren':
        hpc_name = "l___"
    elif hpc == 'ecmwf':
        hpc_name = "e___"
    elif hpc == 'marenostrum3':
        hpc_name = "m___"
    elif hpc == 'archer':
        hpc_name = "a___"
    else:
        raise ValueError('%c is not a valid HPC name' % hpc)
    cursor.execute('select name '
                   'from experiment '
                   'where rowid=(select max(rowid) from experiment where name LIKE "' + hpc_name + '")')
    row = cursor.fetchone()
    if row is None:
        row = ('empty', )
    close_conn(conn, cursor)
    return row[0]


def delete_experiment(name):
    check_db()
    name = check_name(name)
    (conn, cursor) = open_conn()
    cursor.execute('delete from experiment '
                   'where name=:name', {'name': name})
    row = cursor.fetchone()
    if row is None:
        close_conn(conn, cursor)
        print 'The experiment %s has been deleted!!!' % name
        sys.exit(1)

    close_conn(conn, cursor)
    return


def check_name(name):
    name = name.lower()
    if len(name) != 4 and not name.isalnum():
        print "So sorry, but the name must have 4 alphanumeric chars!!!"
        sys.exit(1)
    return name


def check_db():
    if not os.path.exists(DB_PATH):
        print 'Some problem has happened...check the database file!!!'
        print 'DB file:', DB_PATH
        sys.exit(1)
    return


def open_conn():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    return conn, cursor


def close_conn(conn, cursor):
    conn.commit()
    cursor.close()
    conn.close()
    return

