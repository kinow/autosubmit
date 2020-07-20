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

import os
import sys
import string
import time
import pickle
import textwrap
import traceback
import sqlite3
import copy
from datetime import datetime
# from networkx import DiGraph

#DB_FILE_AS_TIMES = "/esarchive/autosubmit/as_times.db"


def get_structure(exp_id, structures_path):
    """
    Creates file of database and table of experiment structure if it does not exist. Returns current structure.

    :return: Map from experiment name source to name destination  
    :rtype: Dictionary Key: String, Value: List(of String)
    """
    try:
        #pkl_path = os.path.join(exp_path, exp_id, "pkl")
        if os.path.exists(structures_path):
            db_structure_path = os.path.join(
                structures_path, "structure_" + exp_id + ".db")
            if not os.path.exists(db_structure_path):
                open(db_structure_path, "w")
            # print(db_structure_path)
            conn = create_connection(db_structure_path)
            create_table_query = textwrap.dedent(
                '''CREATE TABLE
            IF NOT EXISTS experiment_structure (
            e_from text NOT NULL,
            e_to text NOT NULL,
            UNIQUE(e_from,e_to)
            );''')
            create_table(conn, create_table_query)
            current_table = _get_exp_structure(db_structure_path)
            # print("Current table: ")
            # print(current_table)
            current_table_structure = dict()
            for item in current_table:
                _from, _to = item
                if _from not in current_table_structure.keys():
                    current_table_structure[_from] = list()
                if _to not in current_table_structure.keys():
                    current_table_structure[_to] = list()
                current_table_structure[_from].append(_to)
            if (len(current_table_structure.keys()) > 0):
                # print("Return structure")
                return current_table_structure
            else:
                return None
        else:
            # pkl folder not found
            raise Exception("Structures folder not found " +
                            str(structures_path))
    except Exception as exp:
        print(traceback.format_exc())


def create_connection(db_file):
    """ 
    Create a database connection to the SQLite database specified by db_file.  
    :param db_file: database file name  
    :return: Connection object or None
    """
    try:
        conn = sqlite3.connect(db_file)
        return conn
    except:
        return None


def create_table(conn, create_table_sql):
    """ create a table from the create_table_sql statement
    :param conn: Connection object
    :param create_table_sql: a CREATE TABLE statement
    :return:
    """
    try:
        c = conn.cursor()
        c.execute(create_table_sql)
    except Exception as e:
        print(e)


def _get_exp_structure(path):
    """
    Get all registers from experiment_status.\n
    :return: row content: exp_id, name, status, seconds_diff  
    :rtype: 4-tuple (int, str, str, int)
    """
    try:
        conn = create_connection(path)
        conn.text_factory = str
        cur = conn.cursor()
        cur.execute(
            "SELECT e_from, e_to FROM experiment_structure")
        rows = cur.fetchall()
        return rows
    except Exception as exp:
        print(traceback.format_exc())
        return dict()


def save_structure(graph, exp_id, structures_path):
    """
    Saves structure if path is valid
    """
    #pkl_path = os.path.join(exp_path, exp_id, "pkl")
    if os.path.exists(structures_path):
        db_structure_path = os.path.join(
            structures_path, "structure_" + exp_id + ".db")
        # with open(db_structure_path, "w"):
        conn = None
        if os.path.exists(db_structure_path):
            conn = create_connection(db_structure_path)
            _delete_table_content(conn)
        else:
            open(db_structure_path, "w")
            conn = create_connection(db_structure_path)
        if conn:
            for u, v in graph.edges():
                # save
                _create_edge(conn, u, v)
                #print("Created edge " + str(u) + str(v))
            conn.commit()
    else:
        # pkl folder not found
        raise Exception("pkl folder not found " + str(structures_path))


def _create_edge(conn, u, v):
    """
    Create edge
    """
    try:
        sql = ''' INSERT INTO experiment_structure(e_from, e_to) VALUES(?,?) '''
        cur = conn.cursor()
        cur.execute(sql, (u, v))
        # return cur.lastrowid
    except sqlite3.Error as e:
        print("Error on Insert : " + str(type(e).__name__))


def _delete_table_content(conn):
    """
    Deletes table content
    """
    try:
        sql = ''' DELETE FROM experiment_structure '''
        cur = conn.cursor()
        cur.execute(sql)
        conn.commit()
    except sqlite3.Error as e:
        print(traceback.format_exc())
        print("Error on Delete : " + str(type(e).__name__))
