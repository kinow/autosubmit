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


class Status:
	"""Class to handle the status of a job"""
	WAITING = 0
	READY = 1
	SUBMITTED = 2 
	QUEUING = 3
	RUNNING = 4
	COMPLETED = 5
	FAILED = -1
	UNKNOWN = -2
	SUSPENDED = -3
	def retval(self, value):
		return getattr(self, value)

class Type:
	"""Class to handle the type of a job.
	At the moment contains 7 types:
	WRAPPING are for bundle of jobs to execute with python wrapper
	SIMULATION are for multiprocessor jobs
	POSTPROCESSING are single processor jobs
	ClEANING are archiving job---> dealing with large transfer of data on tape
	INITIALISATION are jobs which transfer data from tape to disk
	LOCALSETUP are for source code preparation local jobs
	REMOTESETUP are for soruce code compilation jobs
	TRANSFER are for downloading data jobs"""
	WRAPPING = 7
	LOCALSETUP = 6
	REMOTESETUP = 5
	INITIALISATION = 4
	SIMULATION = 3
	POSTPROCESSING = 2
	CLEANING = 1
	TRANSFER = 0
	LOCALPOST = -1
	PLOT = -2
