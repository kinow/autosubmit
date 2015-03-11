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

import datetime
import time
import calendar
from dateutil.relativedelta import *

from autosubmit.config.log import Log


"""In this python script there are tools to manipulate the dates and make mathematical operations between them """


def add_time(string_date, total_size, chunk_unit, cal):
    if chunk_unit == 'year':
        return add_years(string_date, total_size)
    elif chunk_unit == 'month':
        return add_months(string_date, total_size, cal)
    elif chunk_unit == 'day':
        return add_days(string_date, total_size, cal)
    elif chunk_unit == 'hour':
        return add_hours(string_date, total_size, cal)
    else:
        Log.critical('Chunk unit not valid: {0}'.format(chunk_unit))


def add_years(string_date, number_of_years):
    date = time.strptime(string_date, '%Y%m%d')
    delta = relativedelta(years=number_of_years)
    result = datetime.date(date.tm_year, date.tm_mon, date.tm_mday) + delta
    return result


def add_months(string_date, number_of_months, cal):
    date = time.strptime(string_date, '%Y%m%d')
    delta = relativedelta(months=number_of_months)
    result = datetime.date(date.tm_year, date.tm_mon, date.tm_mday) + delta
    if cal == 'noleap':
        if result.month == 2 and result.day == 29:
            result = datetime.date(result.year, 2, 28)
    return result


def add_days(string_date, number_of_days, cal):
    date = time.strptime(string_date, '%Y%m%d')
    delta = relativedelta(days=number_of_days)
    result = datetime.date(date.tm_year, date.tm_mon, date.tm_mday) + delta
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
    return result


def add_hours(string_date, number_of_months, cal):
    date = time.strptime(string_date, '%Y%m%d')
    delta = relativedelta(hours=number_of_months)
    result = datetime.date(date.tm_year, date.tm_mon, date.tm_mday) + delta
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
    return result


def subs_dates(start_date, end_date, cal):
    start = time.strptime(start_date, '%Y%m%d')
    end = time.strptime(end_date, '%Y%m%d')
    start_datetime = datetime.date(start.tm_year, start.tm_mon, start.tm_mday)
    end_datetime = datetime.date(end.tm_year, end.tm_mon, end.tm_mday)
    result = end_datetime - start_datetime
    if cal == 'noleap':
        year = start_datetime.year
        if start_datetime.month > 2:
            year += 1

        while year <= end_datetime.year:
            if calendar.isleap(year):
                if end_datetime.year == year and end_datetime < datetime.date(year, 2, 29):
                    year += 1
                    continue
                result -= datetime.timedelta(days=1)
            year += 1
    return result.days


def chunk_start_date(string_date, chunk, chunk_length, chunk_unit, cal):
    chunk_1 = chunk - 1
    total_months = chunk_1 * chunk_length
    result = add_time(string_date, total_months, chunk_unit, cal)
    start_date = "%s%02d%02d" % (result.year, result.month, result.day)
    return start_date


def chunk_end_date(start_date, chunk_length, chunk_unit, cal):
    result = add_time(start_date, chunk_length, chunk_unit, cal)
    end_date = "%s%02d%02d" % (result.year, result.month, result.day)
    return end_date


def running_days(start_date, end_date, cal):
    return subs_dates(start_date, end_date, cal)


def previous_days(string_date, start_date, cal):
    return subs_dates(string_date, start_date, cal)


def previous_day(string_date, cal):
    date_1 = add_days(string_date, -1, cal)
    string_date_1 = "%s%02d%02d" % (date_1.year, date_1.month, date_1.day)
    return string_date_1


def chunk_start_month(string_date):
    date = time.strptime(string_date, '%Y%m%d')
    result = date.tm_mon
    return result


def chunk_start_year(string_date):
    date = time.strptime(string_date, '%Y%m%d')
    result = date.tm_year
    return result


####################
# Main Program
####################
def main():
    string_date = '19600201'
    cal = 'noleap'
    start_date = chunk_start_date(string_date, 1, 28, 'day', cal)
    Log.info(start_date)
    end_date = chunk_end_date(start_date, 28, 'day', cal)
    Log.info(end_date)
    Log.info(running_days(start_date, end_date, cal))
    Log.info(running_days(string_date, end_date, cal))
    Log.info(previous_days(string_date, start_date, cal))
    Log.info("year: {0}".format(chunk_start_year(string_date)))
    Log.info("month: {0}".format(chunk_start_month(string_date)))
    Log.info("yesterday: %s " % previous_day(string_date, cal))


if __name__ == "__main__":
    main()
