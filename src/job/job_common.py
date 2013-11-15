#!/usr/bin/env python

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
	SIMULATION are for multiprocessor jobs
	POSTPROCESSING are single processor jobs
	ClEANING are archiving job---> dealing with large transfer of data on tape
	INITIALISATION are jobs which transfer data from tape to disk
	LOCALSETUP are for source code preparation local jobs
	REMOTESETUP are for soruce code compilation jobs
	TRANSFER are for downloading data jobs"""
	LOCALSETUP = 6
	REMOTESETUP = 5
	INITIALISATION = 4
	SIMULATION = 3
	POSTPROCESSING = 2
	CLEANING = 1
	TRANSFER = 0
