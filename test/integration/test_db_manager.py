from unittest import TestCase

import os
from mock import Mock
from mock import patch
from autosubmit.database.db_manager import DbManager


class TestDbManager(TestCase):

    def setUp(self):
        self.db_manager = DbManager('', 'test-db', 1)
        self.db_manager.connect()

    def tearDown(self):
        self.db_manager.drop()

    def test_after_create_table_command_then_it_returns_0_rows(self):
        table_name = 'test'
        self.db_manager.create_table(table_name, ['field1', 'field2'])
        count = self.db_manager.count(table_name)
        self.assertEquals(0, count)

    def test_after_3_inserts_into_a_table_then_it_has_3_rows(self):
        table_name = 'test'
        columns = ['field1', 'field2']
        self.db_manager.create_table(table_name, columns)
        for i in xrange(3):
            self.db_manager.insert(table_name, columns, ['dummy', 'dummy'])
        count = self.db_manager.count(table_name)
        self.assertEquals(3, count)
