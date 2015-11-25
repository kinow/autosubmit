from unittest import TestCase

from autosubmit.date.chunk_date_lib import *
from datetime import datetime


class TestChunkDateLib(TestCase):

    def test_add_time(self):
        self.assertEqual(add_time(datetime(2000, 1, 1), 1, 'month', 'standard'), datetime(2000, 2, 1))
        self.assertEqual(add_time(datetime(2000, 1, 1), 1, 'day', 'standard'), datetime(2000, 1, 2))
        self.assertEqual(add_time(datetime(2000, 1, 1), 1, 'hour', 'standard'), datetime(2000, 1, 1, 1))

        # Testing noleap calendar
        self.assertEqual(add_time(datetime(2000, 2, 28), 1, 'day', 'noleap'), datetime(2000, 3, 1))
        self.assertEqual(add_time(datetime(2000, 2, 28), 1, 'day', 'standard'), datetime(2000, 2, 29))

    def test_add_years(self):
        self.assertEqual(add_years(datetime(2000, 1, 1), 1), datetime(2001, 1, 1))

    def test_add_months(self):
        self.assertEqual(add_months(datetime(2000, 1, 1), 1, 'standard'), datetime(2000, 2, 1))
        self.assertEqual(add_months(datetime(2000, 1, 29), 1, 'standard'), datetime(2000, 2, 29))
        self.assertEqual(add_months(datetime(2000, 1, 29), 1, 'noleap'), datetime(2000, 2, 28))

    def test_add_days(self):
        self.assertEqual(add_days(datetime(2000, 1, 1), 1, 'standard'), datetime(2000, 1, 2))
        self.assertEqual(add_days(datetime(2000, 2, 28), 1, 'standard'), datetime(2000, 2, 29))
        self.assertEqual(add_days(datetime(2000, 2, 28), 1, 'noleap'), datetime(2000, 3, 1))

    def test_add_hours(self):
        self.assertEqual(add_hours(datetime(2000, 1, 1), 24, 'standard'), datetime(2000, 1, 2))
        self.assertEqual(add_hours(datetime(2000, 1, 1, 23), 1, 'standard'), datetime(2000, 1, 2))
        self.assertEqual(add_hours(datetime(2000, 2, 28), 24, 'standard'), datetime(2000, 2, 29))
        self.assertEqual(add_hours(datetime(2000, 2, 28), 24, 'noleap'), datetime(2000, 3, 1))

    def test_subs_days(self):
        self.assertEqual(sub_days(datetime(2000, 1, 2), 1, 'standard'), datetime(2000, 1, 1))
        self.assertEqual(sub_days(datetime(2000, 3, 1), 1, 'standard'), datetime(2000, 2, 29))
        self.assertEqual(sub_days(datetime(2000, 3, 1), 1, 'noleap'), datetime(2000, 2, 28))

    def test_subs_dates(self):
        self.assertEqual(subs_dates(datetime(2000, 1, 1), datetime(2000, 1, 2), 'standard'), 1)
        self.assertEqual(subs_dates(datetime(2000, 1, 2), datetime(2000, 1, 1), 'standard'), -1)
        self.assertEqual(subs_dates(datetime(2000, 2, 28), datetime(2000, 3, 1), 'standard'), 2)
        self.assertEqual(subs_dates(datetime(2000, 2, 28), datetime(2000, 3, 1), 'noleap'), 1)

    def test_chunk_start_date(self):
        self.assertEqual(chunk_start_date(datetime(2000, 1, 1), 1, 1, 'month', 'standard'),
                             datetime(2000, 1, 1))
        self.assertEqual(chunk_start_date(datetime(2000, 1, 1), 3, 1, 'month', 'standard'),
                             datetime(2000, 3, 1))
        self.assertEqual(chunk_start_date(datetime(2000, 1, 1), 1, 3, 'month', 'standard'),
                             datetime(2000, 1, 1))
        self.assertEqual(chunk_start_date(datetime(2000, 1, 1), 3, 3, 'month', 'standard'),
                             datetime(2000, 7, 1))

        self.assertEqual(chunk_start_date(datetime(2000, 1, 1), 1, 1, 'day', 'standard'),
                             datetime(2000, 1, 1))
        self.assertEqual(chunk_start_date(datetime(2000, 1, 1), 3, 1, 'day', 'standard'),
                             datetime(2000, 1, 3))
        self.assertEqual(chunk_start_date(datetime(2000, 1, 1), 1, 3, 'day', 'standard'),
                             datetime(2000, 1, 1))
        self.assertEqual(chunk_start_date(datetime(2000, 1, 1), 3, 3, 'day', 'standard'),
                             datetime(2000, 1, 7))

        self.assertEqual(chunk_start_date(datetime(2000, 1, 1), 1, 1, 'hour', 'standard'),
                             datetime(2000, 1, 1))
        self.assertEqual(chunk_start_date(datetime(2000, 1, 1), 3, 1, 'hour', 'standard'),
                             datetime(2000, 1, 1, 2))
        self.assertEqual(chunk_start_date(datetime(2000, 1, 1), 1, 3, 'hour', 'standard'),
                             datetime(2000, 1, 1))
        self.assertEqual(chunk_start_date(datetime(2000, 1, 1), 3, 3, 'hour', 'standard'),
                             datetime(2000, 1, 1, 6))

    def test_chunk_end_date(self):
        self.assertEqual(chunk_end_date(datetime(2000, 1, 1), 1, 'month', 'standard'),
                             datetime(2000, 2, 1))
        self.assertEqual(chunk_end_date(datetime(2000, 1, 1), 3, 'month', 'standard'),
                             datetime(2000, 4, 1))

        self.assertEqual(chunk_end_date(datetime(2000, 1, 1), 1, 'day', 'standard'),
                             datetime(2000, 1, 2))
        self.assertEqual(chunk_end_date(datetime(2000, 1, 1), 3, 'day', 'standard'),
                             datetime(2000, 1, 4))

        self.assertEqual(chunk_end_date(datetime(2000, 1, 1), 1, 'hour', 'standard'),
                             datetime(2000, 1, 1, 1))
        self.assertEqual(chunk_end_date(datetime(2000, 1, 1), 3, 'hour', 'standard'),
                             datetime(2000, 1, 1, 3))

    def test_previous_date(self):
        self.assertEqual(previous_day(datetime(2000, 1, 2), 'standard'), datetime(2000, 1, 1))
        self.assertEqual(previous_day(datetime(2000, 3, 1), 'standard'), datetime(2000, 2, 29))
        self.assertEqual(previous_day(datetime(2000, 3, 1), 'noleap'), datetime(2000, 2, 28))

    def test_parse_date(self):
        self.assertEqual(parse_date(''), None)
        self.assertEqual(parse_date('2000'), datetime(2000, 1, 1))
        self.assertEqual(parse_date('200001'), datetime(2000, 1, 1))
        self.assertEqual(parse_date('20000101'), datetime(2000, 1, 1))
        self.assertEqual(parse_date('2000010100'), datetime(2000, 1, 1))
        self.assertEqual(parse_date('200001010000'), datetime(2000, 1, 1))

        with self.assertRaises(ValueError):
            parse_date('200014')
        with self.assertRaises(ValueError):
            parse_date('20000230')
        with self.assertRaises(ValueError):
            parse_date('200')

    def test_date2str(self):
        self.assertEqual(date2str(None), '')
        self.assertEqual(date2str(datetime(2000, 1, 1)), '20000101')
        self.assertEqual(date2str(datetime(2000, 1, 1), 'H'), '2000010100')
        self.assertEqual(date2str(datetime(2000, 1, 1), 'M'), '200001010000')


