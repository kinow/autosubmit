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

"""
Main module for autosubmit. Only contains an interface class to all functionality implemented on autosubmit
"""
import os
import sys
import sqlite3
import string

from autosubmit.config.log import Log
from autosubmit.config.basicConfig import BasicConfig


def create_db(qry):
    """
    Creates a new database for autosubmit

    :param qry: query to create the new database
    :return: None
    """
    (conn, cursor) = open_conn()
    try:
        cursor.execute(qry)
    except sqlite3.Error:
        close_conn(conn, cursor)
        Log.error('The database can not be created.' + 'DB file:' + BasicConfig.DB_PATH)
        sys.exit(1)

    conn.commit()
    close_conn(conn, cursor)
    return


def _set_experiment(name, description):
    """
    Stores experiment in database

    :param name: experiment's name
    :param description: experiment's description
    :return: None
    """
    check_db()
    name = check_name(name)

    (conn, cursor) = open_conn()
    try:
        cursor.execute('insert into experiment (name, description) values (:name, :description)',
                       {'name': name, 'description': description})
    except sqlite3.IntegrityError as e:
        close_conn(conn, cursor)
        Log.error('Could not register experiment: {0}'.format(e))
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
        Log.error('The experiment name "{0}" does not exist yet!!!', name)
        return False
    return True


def new_experiment(hpc, description):
    """
    Stores a new experiment on the database and generates its identifier

    :param hpc: name of the main HPC to be used by the experiment
    :param description: experiment's description
    :return: experiment id for the new experiment
    """
    last_exp_name = last_name(hpc)
    if last_exp_name == 'empty':
        if hpc == 'test':
            new_name = 'test000'
        else:
            new_name = hpc[0]+'000'
    else:
        new_name = _next_name(last_exp_name)
    _set_experiment(new_name, description)
    Log.info('The new experiment "{0}" has been registered.' , new_name)
    return new_name


def copy_experiment(name, hpc, description):
    """
    Creates a new experiment by copying an existing experiment

    :param name: identifier of experiment to copy
    :param hpc: name of the main HPC to be used by the experiment
    :param description: experiment's description
    :return: experiment id for the new experiment
    """
    if not check_experiment_exists(name):
        exit(1)
    new_name = new_experiment(hpc, description)
    return new_name


def base36encode(number, alphabet=string.digits + string.ascii_lowercase):
    """
    Convert positive integer to a base36 string.

    :param number: number to convert
    :param alphabet: set of characters to use
    :return: number's base36 string value
    """
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

    while number > 0:
        number, i = divmod(number, len(alphabet))
        # noinspection PyAugmentAssignment
        base36 = alphabet[i] + base36

    return sign + base36


def base36decode(number):
    """
    Converts a base36 string to a positive integer

    :param number: base36 string to convert
    :return: number's integer value
    """
    return int(number, 36)


def _next_name(name):
    """
    Get next experiment identifier

    :param name: previous experiment identifier
    :return: new experiment identifier
    """
    name = check_name(name)
    # Convert the name to base 36 in number add 1 and then encode it
    return base36encode(base36decode(name) + 1)


def last_name(hpc):
    """
    Gets last experiment identifier used for HPC

    :param hpc: HPC name
    :return: last experiment identifier used for HPC, 'empty' if there is none
    """
    check_db()
    (conn, cursor) = open_conn()
    conn.text_factory = str
    if hpc == 'test':
        hpc_name = 'test'
    else:
        hpc_name = hpc[0]
    hpc_name += '___'
    cursor.execute('select name '
                   'from experiment '
                   'where rowid=(select max(rowid) from experiment where name LIKE "' + hpc_name + '")')
    row = cursor.fetchone()
    if row is None:
        row = ('empty', )
    close_conn(conn, cursor)
    return row[0]


def delete_experiment(name):
    """
    Removes experiment from database

    :param name: experiment identifier
    :return: None
    """
    check_db()
    name = check_name(name)
    (conn, cursor) = open_conn()
    cursor.execute('delete from experiment '
                   'where name=:name', {'name': name})
    row = cursor.fetchone()
    if row is None:
        Log.debug('The experiment {0} has been deleted!!!', name)
    close_conn(conn, cursor)
    return


def check_name(name):
    """
    Checks if it is a valid experiment identifier

    :param name: experiment identifier to check
    :return: name if is valid, terminates program otherwise
    """
    name = name.lower()
    if len(name) < 4 or not name.isalnum():
        Log.error("So sorry, but the name must have at least 4 alphanumeric chars!!!")
        sys.exit(1)
    return name


def check_db():
    """
    Checks if database file exist

    :return: None if exists, terminates program if not
    """

    if not os.path.exists(BasicConfig.DB_PATH):
        Log.error('Some problem has happened...check the database file.' + 'DB file:' + BasicConfig.DB_PATH)
        sys.exit(1)
    return


def open_conn():
    """
    Opens a connection to database

    :return: connection object, cursor object
    """
    conn = sqlite3.connect(BasicConfig.DB_PATH)
    cursor = conn.cursor()
    return conn, cursor


def close_conn(conn, cursor):
    """
    Commits changes and close connection to database

    :param conn: connection to close
    :param cursor: cursor to close
    :return:
    """
    conn.commit()
    cursor.close()
    conn.close()
    return

