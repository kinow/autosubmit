from unittest import TestCase

from autosubmit.date.chunk_date_lib import *
from datetime import datetime


class TestChunkDateLib(TestCase):

    def test_add_time(self):
        TestCase.assertEqual(self, add_time(datetime(2000, 1, 1), 1, 'month', 'standard'), datetime(2000, 2, 1))
        TestCase.assertEqual(self, add_time(datetime(2000, 1, 1), 1, 'day', 'standard'), datetime(2000, 1, 2))
        TestCase.assertEqual(self, add_time(datetime(2000, 1, 1), 1, 'hour', 'standard'), datetime(2000, 1, 1, 1))

        # Testing noleap calendar
        TestCase.assertEqual(self, add_time(datetime(2000, 2, 28), 1, 'day', 'noleap'), datetime(2000, 3, 1))
        TestCase.assertEqual(self, add_time(datetime(2000, 2, 28), 1, 'day', 'standard'), datetime(2000, 2, 29))

    def test_add_years(self):
        TestCase.assertEqual(self, add_years(datetime(2000, 1, 1), 1), datetime(2001, 1, 1))

    def test_add_months(self):
        TestCase.assertEqual(self, add_months(datetime(2000, 1, 1), 1, 'standard'), datetime(2000, 2, 1))
        TestCase.assertEqual(self, add_months(datetime(2000, 1, 29), 1, 'standard'), datetime(2000, 2, 29))
        TestCase.assertEqual(self, add_months(datetime(2000, 1, 29), 1, 'noleap'), datetime(2000, 2, 28))

    def test_add_days(self):
        TestCase.assertEqual(self, add_days(datetime(2000, 1, 1), 1, 'standard'), datetime(2000, 1, 2))
        TestCase.assertEqual(self, add_days(datetime(2000, 2, 28), 1, 'standard'), datetime(2000, 2, 29))
        TestCase.assertEqual(self, add_days(datetime(2000, 2, 28), 1, 'noleap'), datetime(2000, 3, 1))

    def test_add_hours(self):
        TestCase.assertEqual(self, add_hours(datetime(2000, 1, 1), 24, 'standard'), datetime(2000, 1, 2))
        TestCase.assertEqual(self, add_hours(datetime(2000, 1, 1, 23), 1, 'standard'), datetime(2000, 1, 2))
        TestCase.assertEqual(self, add_hours(datetime(2000, 2, 28), 24, 'standard'), datetime(2000, 2, 29))
        TestCase.assertEqual(self, add_hours(datetime(2000, 2, 28), 24, 'noleap'), datetime(2000, 3, 1))

    def test_subs_days(self):
        TestCase.assertEqual(self, sub_days(datetime(2000, 1, 2), 1, 'standard'), datetime(2000, 1, 1))
        TestCase.assertEqual(self, sub_days(datetime(2000, 3, 1), 1, 'standard'), datetime(2000, 2, 29))
        TestCase.assertEqual(self, sub_days(datetime(2000, 3, 1), 1, 'noleap'), datetime(2000, 2, 28))

    def test_subs_dates(self):
        TestCase.assertEqual(self, subs_dates(datetime(2000, 1, 1), datetime(2000, 1, 2), 'standard'), 1)
        TestCase.assertEqual(self, subs_dates(datetime(2000, 1, 2), datetime(2000, 1, 1), 'standard'), -1)
        TestCase.assertEqual(self, subs_dates(datetime(2000, 2, 28), datetime(2000, 3, 1), 'standard'), 2)
        TestCase.assertEqual(self, subs_dates(datetime(2000, 2, 28), datetime(2000, 3, 1), 'noleap'), 1)

    def test_chunk_start_date(self):
        TestCase.assertEqual(self, chunk_start_date(datetime(2000, 1, 1), 1, 1, 'month', 'standard'),
                             datetime(2000, 1, 1))
        TestCase.assertEqual(self, chunk_start_date(datetime(2000, 1, 1), 3, 1, 'month', 'standard'),
                             datetime(2000, 3, 1))
        TestCase.assertEqual(self, chunk_start_date(datetime(2000, 1, 1), 1, 3, 'month', 'standard'),
                             datetime(2000, 1, 1))
        TestCase.assertEqual(self, chunk_start_date(datetime(2000, 1, 1), 3, 3, 'month', 'standard'),
                             datetime(2000, 7, 1))

        TestCase.assertEqual(self, chunk_start_date(datetime(2000, 1, 1), 1, 1, 'day', 'standard'),
                             datetime(2000, 1, 1))
        TestCase.assertEqual(self, chunk_start_date(datetime(2000, 1, 1), 3, 1, 'day', 'standard'),
                             datetime(2000, 1, 3))
        TestCase.assertEqual(self, chunk_start_date(datetime(2000, 1, 1), 1, 3, 'day', 'standard'),
                             datetime(2000, 1, 1))
        TestCase.assertEqual(self, chunk_start_date(datetime(2000, 1, 1), 3, 3, 'day', 'standard'),
                             datetime(2000, 1, 7))

        TestCase.assertEqual(self, chunk_start_date(datetime(2000, 1, 1), 1, 1, 'hour', 'standard'),
                             datetime(2000, 1, 1))
        TestCase.assertEqual(self, chunk_start_date(datetime(2000, 1, 1), 3, 1, 'hour', 'standard'),
                             datetime(2000, 1, 1, 2))
        TestCase.assertEqual(self, chunk_start_date(datetime(2000, 1, 1), 1, 3, 'hour', 'standard'),
                             datetime(2000, 1, 1))
        TestCase.assertEqual(self, chunk_start_date(datetime(2000, 1, 1), 3, 3, 'hour', 'standard'),
                             datetime(2000, 1, 1, 6))

    def test_chunk_end_date(self):
        TestCase.assertEqual(self, chunk_end_date(datetime(2000, 1, 1), 1, 'month', 'standard'),
                             datetime(2000, 2, 1))
        TestCase.assertEqual(self, chunk_end_date(datetime(2000, 1, 1), 3, 'month', 'standard'),
                             datetime(2000, 4, 1))

        TestCase.assertEqual(self, chunk_end_date(datetime(2000, 1, 1), 1, 'day', 'standard'),
                             datetime(2000, 1, 2))
        TestCase.assertEqual(self, chunk_end_date(datetime(2000, 1, 1), 3, 'day', 'standard'),
                             datetime(2000, 1, 4))

        TestCase.assertEqual(self, chunk_end_date(datetime(2000, 1, 1), 1, 'hour', 'standard'),
                             datetime(2000, 1, 1, 1))
        TestCase.assertEqual(self, chunk_end_date(datetime(2000, 1, 1), 3, 'hour', 'standard'),
                             datetime(2000, 1, 1, 3))
