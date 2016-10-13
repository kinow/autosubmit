#!/usr/bin/env python

# Copyright 2015 Earth Sciences Department, BSC-CNS

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
Module containing functions to manage autosubmit's database.
"""
import os
import sqlite3

from autosubmit.config.log import Log
from autosubmit.config.basicConfig import BasicConfig

CURRENT_DATABASE_VERSION = 1


def create_db(qry):
    """
    Creates a new database for autosubmit

    :param qry: query to create the new database
    :type qry: str    """

    try:
        (conn, cursor) = open_conn(False)
    except DbException as e:
        Log.error('Connection to database could not be established: {0}', e.message)
        return False

    try:
        cursor.executescript(qry)
    except sqlite3.Error:
        close_conn(conn, cursor)
        Log.error('The database can not be created.' + 'DB file:' + BasicConfig.DB_PATH)
        return False

    conn.commit()
    close_conn(conn, cursor)
    return True


def check_db():
    """
    Checks if database file exist

    :return: None if exists, terminates program if not
    """

    if not os.path.exists(BasicConfig.DB_PATH):
        Log.error('Some problem has happened...check the database file.' + 'DB file:' + BasicConfig.DB_PATH)
        return False
    return True


def open_conn(check_version=True):
    """
    Opens a connection to database

    :param check_version: If true, check if the database is compatible with this autosubmit version
    :type check_version: bool
    :return: connection object, cursor object
    :rtype: sqlite3.Connection, sqlite3.Cursor
    """
    conn = sqlite3.connect(BasicConfig.DB_PATH)
    cursor = conn.cursor()

    # Getting database version
    if check_version:
        try:
            cursor.execute('SELECT version '
                           'FROM db_version;')
            row = cursor.fetchone()
            version = row[0]
        except sqlite3.OperationalError:
            # If this exception is thrown it's because db_version does not exist.
            # Database is from 2.x or 3.0 beta releases
            try:
                cursor.execute('SELECT type '
                               'FROM experiment;')
                # If type field exists, it's from 2.x
                version = -1
            except sqlite3.Error:
                # If raises and error , it's from 3.0 beta releases
                version = 0

        # If database version is not the expected, update database....
        if version < CURRENT_DATABASE_VERSION:
            if not _update_database(version, cursor):
                raise DbException('Database version could not be updated')

        # ... or ask for autosubmit upgrade
        elif version > CURRENT_DATABASE_VERSION:
            Log.critical('Database version is not compatible with this autosubmit version. Please execute pip install '
                         'autosubmit --upgrade')
            raise DbException('Database version not compatible')

    return conn, cursor


def close_conn(conn, cursor):
    """
    Commits changes and close connection to database

    :param conn: connection to close
    :type conn: sqlite3.Connection
    :param cursor: cursor to close
    :type cursor: sqlite3.Cursor
    """
    conn.commit()
    cursor.close()
    conn.close()
    return


def save_experiment(name, description, version):
    """
    Stores experiment in database

    :param version:
    :type version: str
    :param name: experiment's name
    :type name: str
    :param description: experiment's description
    :type description: str
    """
    if not check_db():
        return False
    try:
        (conn, cursor) = open_conn()
    except DbException as e:
        Log.error('Connection to database could not be established: {0}', e.message)
        return False
    try:
        cursor.execute('INSERT INTO experiment (name, description, autosubmit_version) VALUES (:name, :description, '
                       ':version)',
                       {'name': name, 'description': description, 'version': version})
    except sqlite3.IntegrityError as e:
        close_conn(conn, cursor)
        Log.error('Could not register experiment: {0}'.format(e))
        return False

    conn.commit()
    close_conn(conn, cursor)
    return True


def check_experiment_exists(name, error_on_inexistence=True):
    """
    Checks if exist an experiment with the given name.

    :param error_on_inexistence: if True, adds an error log if experiment does not exists
    :type error_on_inexistence: bool
    :param name: Experiment name
    :type name: str
    :return: If experiment exists returns true, if not returns false
    :rtype: bool
    """
    if not check_db():
        return False
    try:
        (conn, cursor) = open_conn()
    except DbException as e:
        Log.error('Connection to database could not be established: {0}', e.message)
        return False
    conn.isolation_level = None

    # SQLite always return a unicode object, but we can change this
    # behaviour with the next sentence
    conn.text_factory = str
    cursor.execute('select name from experiment where name=:name', {'name': name})
    row = cursor.fetchone()
    close_conn(conn, cursor)
    if row is None:
        if error_on_inexistence:
            Log.error('The experiment name "{0}" does not exist yet!!!', name)
        return False
    return True


def get_autosubmit_version(expid):
    """
    Get the minimun autosubmit version needed for the experiment

    :param expid: Experiment name
    :type expid: str
    :return: If experiment exists returns the autosubmit version for it, if not returns None
    :rtype: str
    """
    if not check_db():
        return False

    try:
        (conn, cursor) = open_conn()
    except DbException as e:
        Log.error('Connection to database could not be established: {0}', e.message)
        return False
    conn.isolation_level = None

    # SQLite always return a unicode object, but we can change this
    # behaviour with the next sentence
    conn.text_factory = str
    cursor.execute('SELECT autosubmit_version FROM experiment WHERE name=:expid', {'expid': expid})
    row = cursor.fetchone()
    close_conn(conn, cursor)
    if row is None:
        Log.error('The experiment "{0}" does not exist yet!!!', expid)
        return None
    return row[0]


def last_name_used(test=False, operational=False):
    """
    Gets last experiment identifier used

    :param test: flag for test experiments
    :type test: bool
    :param operational: flag for operational experiments
    :type test: bool
    :return: last experiment identifier used, 'empty' if there is none
    :rtype: str
    """
    if not check_db():
        return ''
    try:
        (conn, cursor) = open_conn()
    except DbException as e:
        Log.error('Connection to database could not be established: {0}', e.message)
        return ''
    conn.text_factory = str
    if test:
        cursor.execute('SELECT name '
                       'FROM experiment '
                       'WHERE rowid=(SELECT max(rowid) FROM experiment WHERE name LIKE "t%" AND '
                       'autosubmit_version IS NOT NULL AND '
                       'NOT (autosubmit_version LIKE "%3.0.0b%"))')
    elif operational:
        cursor.execute('SELECT name '
                       'FROM experiment '
                       'WHERE rowid=(SELECT max(rowid) FROM experiment WHERE name LIKE "o%" AND '
                       'autosubmit_version IS NOT NULL AND '
                       'NOT (autosubmit_version LIKE "%3.0.0b%"))')
    else:
        cursor.execute('SELECT name '
                       'FROM experiment '
                       'WHERE rowid=(SELECT max(rowid) FROM experiment WHERE name NOT LIKE "t%" AND '
                       'name NOT LIKE "o%" AND autosubmit_version IS NOT NULL AND '
                       'NOT (autosubmit_version LIKE "%3.0.0b%"))')
    row = cursor.fetchone()
    close_conn(conn, cursor)
    if row is None:
        return 'empty'

    # If starts by number (during 3.0 beta some jobs starting with numbers where created), returns empty.
    try:
        int(row[0][0])
        return 'empty'
    except ValueError:
        return row[0]


def delete_experiment(experiment_id):
    """
    Removes experiment from database

    :param experiment_id: experiment identifier
    :type experiment_id: str
    :return: True if delete is succesful
    :rtype: bool
    """
    if not check_db():
        return False
    if check_experiment_exists(experiment_id, False):
        return True
    try:
        (conn, cursor) = open_conn()
    except DbException as e:
        Log.error('Connection to database could not be established: {0}', e.message)
        return False
    cursor.execute('DELETE FROM experiment '
                   'WHERE name=:name', {'name': experiment_id})
    row = cursor.fetchone()
    if row is None:
        Log.debug('The experiment {0} has been deleted!!!', experiment_id)
    close_conn(conn, cursor)
    return True


def _update_database(version, cursor):
    Log.info("Autosubmit's database version is {0}. Current version is {1}. Updating...",
             version, CURRENT_DATABASE_VERSION)
    try:
        # For databases from Autosubmit 2
        if version <= -1:
            cursor.executescript('CREATE TABLE experiment_backup(id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT, '
                                 'name VARCHAR NOT NULL, type VARCHAR, autosubmit_version VARCHAR, '
                                 'description VARCHAR NOT NULL, model_branch VARCHAR, template_name VARCHAR, '
                                 'template_branch VARCHAR, ocean_diagnostics_branch VARCHAR);'
                                 'INSERT INTO experiment_backup (name,type,description,model_branch,template_name,'
                                 'template_branch,ocean_diagnostics_branch) SELECT name,type,description,model_branch,'
                                 'template_name,template_branch,ocean_diagnostics_branch FROM experiment;'
                                 'UPDATE experiment_backup SET autosubmit_version = "2";'
                                 'DROP TABLE experiment;'
                                 'ALTER TABLE experiment_backup RENAME TO experiment;')
        if version <= 0:
            # Autosubmit beta version. Create db_version table
            cursor.executescript('CREATE TABLE db_version(version INTEGER NOT NULL);'
                                 'INSERT INTO db_version (version) VALUES (1);'
                                 'ALTER TABLE experiment ADD COLUMN autosubmit_version VARCHAR;'
                                 'UPDATE experiment SET autosubmit_version = "3.0.0b" '
                                 'WHERE autosubmit_version NOT NULL;')
        cursor.execute('UPDATE db_version SET version={0};'.format(CURRENT_DATABASE_VERSION))
    except sqlite3.Error as e:
        Log.critical('Can not update database: {0}', e)
        return False
    Log.info("Update completed")
    return True


class DbException(Exception):
    """
    Exception class for database errors
    """

    def __init__(self, message):
        self.message = message
