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
In this python script there are tools to manipulate the dates and make mathematical
operations between them.
"""

import datetime
import calendar
from dateutil.relativedelta import *

from autosubmit.config.log import Log


def add_time(date, total_size, chunk_unit, cal):
    """
    Adds given time to a date

    :param date: base date
    :type date: datetime.datetime
    :param total_size: time to add
    :type total_size: int
    :param chunk_unit: unit of time to add
    :type chunk_unit: str
    :param cal: calendar to use
    :type cal: str
    :return: result of adding time to base date
    :rtype: datetime.datetime
    """
    if chunk_unit == 'year':
        return add_years(date, total_size)
    elif chunk_unit == 'month':
        return add_months(date, total_size, cal)
    elif chunk_unit == 'day':
        return add_days(date, total_size, cal)
    elif chunk_unit == 'hour':
        return add_hours(date, total_size, cal)
    else:
        Log.critical('Chunk unit not valid: {0}'.format(chunk_unit))


def add_years(date, number_of_years):
    """
    Adds years to a date

    :param date: base date
    :type date: datetime.datetime
    :param number_of_years: number of years to add
    :type number_of_years: int
    :return: base date plus added years
    :rtype: date
    """
    return date + relativedelta(years=number_of_years)


def add_months(date, number_of_months, cal):
    """
    Adds months to a date

    :param date: base date
    :type date: datetime.datetime
    :param number_of_months: number of months to add
    :type number_of_months: int
    :param cal: calendar to use
    :type cal: str
    :return: base date plus added months
    :rtype: date
    """
    result = date + relativedelta(months=number_of_months)
    if cal == 'noleap':
        if result.month == 2 and result.day == 29:
            result = result - relativedelta(days=1)
    return result


def add_days(date, number_of_days, cal):
    """
    Adds days to a date

    :param date: base date
    :type date: datetime.datetime
    :param number_of_days: number of days to add
    :type number_of_days: int
    :param cal: calendar to use
    :type cal: str
    :return: base date plus added days
    :rtype: date
    """
    result = date + relativedelta(days=number_of_days)
    if cal == 'noleap':
        year = date.tm_year
        if date.tm_mon > 2:
            year += 1

        while year <= result.year:
            if calendar.isleap(year):
                if result.year == year and result < datetime.date(year, 2, 29):
                    year += 1
                    continue
                result += relativedelta(days=1)
            year += 1
        if result.month == 2 and result.day == 29:
            result += relativedelta(days=1)
    return result


def sub_days(date, number_of_days, cal):
    """
    Substract days to a date

    :param date: base date
    :type date: datetime.datetime
    :param number_of_days: number of days to substract
    :type number_of_days: int
    :param cal: calendar to use
    :type cal: str
    :return: base date minus substracted days
    :rtype: datetime.datetime
    """
    result = date - relativedelta(days=number_of_days)
    if cal == 'noleap':
        year = date.tm_year
        if date.tm_mon <= 2:
            year -= 1

        while year >= result.year:
            if calendar.isleap(year):
                if result.year == year and result > datetime.date(year, 2, 29):
                    year -= 1
                    continue
                result -= relativedelta(days=1)
            year -= 1
        if result.month == 2 and result.day == 29:
            result -= relativedelta(days=1)
    return result


def add_hours(date, number_of_hours, cal):
    """
    Adds hours to a date

    :param date: base date
    :type date: datetime.datetime
    :param number_of_hours: number of hours to add
    :type number_of_hours: int
    :param cal: calendar to use
    :type cal: str
    :return: base date plus added hours
    :rtype: date
    """
    result = date + relativedelta(hours=number_of_hours)
    if cal == 'noleap':
        year = date.tm_year
        if date.tm_mon > 2:
            year += 1

        while year <= result.year:
            if calendar.isleap(year):
                if result.year == year and result < datetime.date(year, 2, 29):
                    year += 1
                    continue
                result += relativedelta(days=1)
            year += 1
        if result.month == 2 and result.day == 29:
            result += relativedelta(days=1)
    return result


def subs_dates(start_date, end_date, cal):
    """
    Gets days between start_date and end_date

    :param start_date: interval's start date
    :type start_date: datetime.datetime
    :param end_date: interval's end date
    :type end_date: datetime.datetime
    :param cal: calendar to use
    :type cal: str
    :return: interval length in days
    :rtype: int
    """
    result = end_date - start_date
    if cal == 'noleap':
        year = start_date.year
        if start_date.month > 2:
            year += 1

        while year <= end_date.year:
            if calendar.isleap(year):
                if end_date.year == year and end_date < datetime.date(year, 2, 29):
                    year += 1
                    continue
                result -= datetime.timedelta(days=1)
            year += 1
    return result.days


def chunk_start_date(date, chunk, chunk_length, chunk_unit, cal):
    """
    Gets chunk's interval start date

    :param date: start date for member
    :type date: datetime.datetime
    :param chunk: number of chunk
    :type chunk: int
    :param chunk_length: length of chunks
    :type chunk_length: int
    :param chunk_unit: chunk length unit
    :type chunk_unit: str
    :param cal: calendar to use
    :type cal: str
    :return: chunk's start date
    :rtype: datetime.datetime
    """
    chunk_1 = chunk - 1
    total_months = chunk_1 * chunk_length
    result = add_time(date, total_months, chunk_unit, cal)
    return result


def chunk_end_date(start_date, chunk_length, chunk_unit, cal):
    """
    Gets chunk interval end date

    :param start_date: chunk's start date
    :type start_date: datetime.datetime
    :param chunk_length: length of the chunks
    :type chunk_length: int
    :param chunk_unit: chunk length unit
    :type chunk_unit: str
    :param cal: calendar to use
    :type cal: str
    :return: chunk's end date
    :rtype: datetime.datetime
    """
    return add_time(start_date, chunk_length, chunk_unit, cal)


def previous_day(date, cal):
    """
    Gets previous day

    :param date: base date
    :type date: datetime.datetime
    :param cal: calendar to use
    :type cal: str
    :return: base date minus one day
    :rtype: datetime.datetime
    """
    return sub_days(date, 1, cal)


def parse_date(string_date):
    """
    Parses a string into a datetime object

    :param string_date: string to parse
    :type string_date: str
    :rtype: datetime.datetime
    """
    if string_date is None:
        return None
    length = len(string_date)
    if length == 6:
        return datetime.datetime.strptime(string_date, "%Y%m")
    if length == 8:
        return datetime.datetime.strptime(string_date, "%Y%m%d")
    elif length == 10:
        return datetime.datetime.strptime(string_date, "%Y%m%d%H")
    elif length == 12:
        return datetime.datetime.strptime(string_date, "%Y%m%d%H%M")


def date2str(date, date_format=''):
    """
    Converts a datetime object to a str

    :param date: date to convert
    :type date: datetime.datetime
    :rtype: str
    """
    if date is None:
        return ''
    if date_format == 'H':
        return date.strftime("%Y%m%d%H")
    elif date_format == 'M':
        return date.strftime("%Y%m%d%H%M")
    else:
        return date.strftime("%Y%m%d")


####################
# Main Program
####################
def main():
    string_date = datetime.datetime(2010, 5, 1, 12)
    cal = 'noleap'
    start_date = chunk_start_date(string_date, 1, 1, 'month', cal)
    Log.info(start_date)
    end_date = chunk_end_date(start_date, 1, 'month', cal)
    Log.info(end_date)
    Log.info("yesterday: {0} ", previous_day(string_date, cal))


if __name__ == "__main__":
    main()
