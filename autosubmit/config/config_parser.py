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
import sys
from os import path
from ConfigParser import SafeConfigParser

from pyparsing import nestedExpr

from autosubmit.config.log import Log

invalid_values = False


def check_values(key, value, valid_values):
    global invalid_values

    if value.lower() not in valid_values:
        Log.error("Invalid value %s: %s", key, value)
        invalid_values = True



