from unittest import TestCase

import os
from mock import Mock
from mock import patch
from autosubmit.database.db_manager import DbManager


class TestDbManager(TestCase):
    def test_create_table_command_returns_a_valid_command(self):
        # arrange
        table_name = 'tests'
        table_fields = ['dummy1', 'dummy2', 'dummy3']
        expected_command = 'CREATE TABLE tests (dummy1, dummy2, dummy3)'

        # act
        command = DbManager.generate_create_table_command(table_name, table_fields)
        # assert
        self.assertEquals(expected_command, command)

    def test_insert_command_returns_a_valid_command(self):
        # arrange
        table_name = 'tests'
        columns = ['col1, col2, col3']
        values = ['dummy1', 'dummy2', 'dummy3']
        expected_command = 'INSERT INTO tests(col1, col2, col3) VALUES ("dummy1", "dummy2", "dummy3")'

        # act
        command = DbManager.generate_insert_command(table_name, columns, values)
        # assert
        self.assertEquals(expected_command, command)
