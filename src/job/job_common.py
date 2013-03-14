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
	def retval(self, value):
		return getattr(self, value)

class Type:
	"""Class to handle the type of a job.
	At the moment contains only 4 types:
	SIMULATION are for multiprocessor jobs
	POSTPROCESSING are single processor jobs
	ClEANING are archiving job---> dealing with large transfer of data on tape
	INITIALISATION are jobs which transfer data from tape to disk"""
	TRANSFER = 6
	LOCALSETUP = 5
	REMOTESETUP = 4
	SIMULATION = 3
	POSTPROCESSING = 2
	CLEANING = 1
	INITIALISATION = 0
