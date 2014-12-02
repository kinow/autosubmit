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

import textwrap

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

class Template:
	"""Class to handle the template code snippet of a job.
	At the moment contains 7 templates:
	SIMULATION are for multiprocessor jobs
	POSTPROCESSING are single processor jobs
	ClEANING are archiving job---> dealing with large transfer of data on tape
	INITIALISATION are jobs which transfer data from tape to disk
	LOCALSETUP are for source code preparation local jobs
	REMOTESETUP are for soruce code compilation jobs
	TRANSFER are for downloading data jobs"""

	LOCALSETUP = textwrap.dedent("""\
			""")
			
	REMOTESETUP = textwrap.dedent("""\
			""")

	INITIALISATION = textwrap.dedent("""\
			""")

	SIMULATION = textwrap.dedent("""\
			""")

	POSTPROCESSING = textwrap.dedent("""\
			""")

	CLEANING = textwrap.dedent("""\
			""")

	TRANSFER = textwrap.dedent("""\
			""")

	def read_localsetup_file(self, filename):
		self.LOCALSETUP = file(filename, 'r').read()

	def read_remotesetup_file(self, filename):
		self.REMOTESETUP = file(filename, 'r').read()

	def read_initialisation_file(self, filename):
		self.INITIALISATION = file(filename, 'r').read()

	def read_simulation_file(self, filename):
		self.SIMULATION = file(filename, 'r').read()

	def read_postprocessing_file(self, filename):
		self.POSTPROCESSING = file(filename, 'r').read()

	def read_cleaning_file(self, filename):
		self.CLEANING = file(filename, 'r').read()

	def read_transfer_file(self, filename):
		self.TRANSFER = file(filename, 'r').read()


class StatisticsSnippet:
	"""Class to handle the statistics snippet of a job"""

	AS_HEADER_LOC = textwrap.dedent("""\

			###################
			# Autosubmit header
			###################

			set -xuve
			job_name_ptrn=/cfu/autosubmit/%EXPID%/tmp/LOG_%EXPID%/%JOBNAME%
			job_cmd_stamp=$(stat -c %Z $job_name_ptrn.cmd)
			job_start_time=$(date +%s)

			""")

	AS_TAILER_LOC = textwrap.dedent("""\

			###################
			# Autosubmit tailer
			###################

			job_end_time=$(date +%s)
			job_run_time=$((job_end_time - job_start_time))
			errfile_ptrn="\.e"
			failed_jobs=0
			set +e; ls -1 ${job_name_ptrn}* | grep $errfile_ptrn
			if [[ $? -eq 0 ]]; then
			 failed_jobs=$(($(ls -1 ${job_name_ptrn}* | grep $errfile_ptrn | wc -l) - 1))
			 failed_errfiles=$(ls -1 ${job_name_ptrn}* | grep $errfile_ptrn | head -n $failed_jobs)
			fi; set -e
			failed_jobs_rt=0
			for failed_errfile in $failed_errfiles; do
			 failed_errfile_stamp=$(stat -c %Z $failed_errfile)
			 failed_jobs_rt=$((failed_jobs_rt + $((failed_errfile_stamp - $(grep "job_start_time=" $failed_errfile | head -n 2 | tail -n 1 | cut -d '=' -f 2)))))
			done
			echo "$job_end_time 0 $job_run_time $failed_jobs 0 $failed_jobs_rt" > ${job_name_ptrn}_COMPLETED
			""")
			
	AS_HEADER_REM = textwrap.dedent("""\

			###################
			# Autosubmit header
			###################

			set -xuve
			job_name_ptrn=%SCRATCH_DIR%/%HPCPROJ%/%HPCUSER%/%EXPID%/LOG_%EXPID%/%JOBNAME%
			job_cmd_stamp=$(stat -c %Z $job_name_ptrn.cmd)
			job_start_time=$(date +%s)
			job_queue_time=$((job_start_time - job_cmd_stamp))

			""")

	AS_TAILER_REM = textwrap.dedent("""\
	
			###################
			# Autosubmit tailer
			###################
			
			job_end_time=$(date +%s)
			job_run_time=$((job_end_time - job_start_time))
			case %HPCARCH% in
			 ithaca)       errfile_created="TRUE"; errfile_ptrn="\.e" ;;
			 marenostrum)  errfile_created="TRUE"; errfile_ptrn="\.err" ;;
			 marenostrum3) errfile_created="TRUE"; errfile_ptrn="\.err" ;;
			 ecmwf)        errfile_created="TRUE"; errfile_ptrn="\.err" ;;
			 hector)       errfile_created="FALSE"; errfile_ptrn="\.e" ;;
			 lindgren)     errfile_created="FALSE"; errfile_ptrn="\.e" ;;
			 jaguar)       errfile_created="FALSE"; errfile_ptrn="\.e" ;;
			 archer)       errfile_created="FALSE"; errfile_ptrn="\.e" ;;
			 *) echo "!!! %HPCARCH% is not valid platform !!!"; exit 1 ;;
			esac
			failed_jobs=0; failed_errfiles=""
			set +e; ls -1 ${job_name_ptrn}* | grep $errfile_ptrn
			if [[ $? -eq 0 ]]; then
			 case $errfile_created in 
			  TRUE)
				failed_jobs=$(($(ls -1 ${job_name_ptrn}* | grep $errfile_ptrn | wc -l) - 1))
				failed_errfiles=$(ls -1 ${job_name_ptrn}* | grep $errfile_ptrn | head -n $failed_jobs)
			  ;;
			  FALSE)
				failed_jobs=$(ls -1 ${job_name_ptrn}* | grep $errfile_ptrn | wc -l)
				failed_errfiles=$(ls -1 ${job_name_ptrn}* | grep $errfile_ptrn)
			  ;;
			  *) "!!! $errfile_created is not valid errfile_created option !!!"; exit 1 ;;
			 esac
			fi; set -e
			failed_jobs_qt=0; failed_jobs_rt=0
			for failed_errfile in $failed_errfiles; do
			 failed_errfile_stamp=$(stat -c %Z $failed_errfile)
			 failed_jobs_qt=$((failed_jobs_qt + $(grep "job_queue_time=" $failed_errfile | head -n 2 | tail -n 1 | cut -d '=' -f 2)))
			 failed_jobs_rt=$((failed_jobs_rt + $((failed_errfile_stamp - $(grep "job_start_time=" $failed_errfile | head -n 2 | tail -n 1 | cut -d '=' -f 2)))))
			done
			echo "$job_end_time $job_queue_time $job_run_time $failed_jobs $failed_jobs_qt $failed_jobs_rt" > ${job_name_ptrn}_COMPLETED
			""")


class PsHeader:
	"""Class to handle the Ps headers of a job"""
	
	HEADER_LOCALSETUP = textwrap.dedent("""\
			#!/bin/bash
			###############################################################################
			#                   %TASKTYPE% %EXPID% EXPERIMENT
			###############################################################################
			""")

	HEADER_LOCALTRANS = textwrap.dedent("""\
			#!/bin/bash
			###############################################################################
			#                   %TASKTYPE% %EXPID% EXPERIMENT
			###############################################################################
			""")

	
class ArHeader:
	"""Class to handle the Archer headers of a job"""

	HEADER_REMOTESETUP = textwrap.dedent("""\
			#!/bin/sh
			###############################################################################
			#                   %TASKTYPE% %EXPID% EXPERIMENT
			###############################################################################
			#
			#PBS -N %JOBNAME%
			#PBS -l select=serial=true:ncpus=1
			#PBS -l walltime=%WALLCLOCK%:00
			#PBS -A %HPCPROJ%
			#
			###############################################################################
			""")

	HEADER_INI = textwrap.dedent("""\
			#!/bin/sh
			###############################################################################
			#                   %TASKTYPE% %EXPID% EXPERIMENT
			###############################################################################
			#
			#PBS -N %JOBNAME%
			#PBS -l select=serial=true:ncpus=1
			#PBS -l walltime=%WALLCLOCK%:00
			#PBS -A %HPCPROJ%
			#
			###############################################################################
			""")

	HEADER_SIM = textwrap.dedent("""\
			#!/bin/sh
			###############################################################################
			#                   %TASKTYPE% %EXPID% EXPERIMENT
			###############################################################################
			#
			#PBS -N %JOBNAME%
			#PBS -l select=%NUMPROC%
			#PBS -l walltime=%WALLCLOCK%:00
			#PBS -A %HPCPROJ%
			#
			###############################################################################
			""")

	HEADER_POST = textwrap.dedent("""\
			#!/bin/sh
			###############################################################################
			#                   %TASKTYPE% %EXPID% EXPERIMENT
			###############################################################################
			#
			#PBS -N %JOBNAME%
			#PBS -l select=serial=true:ncpus=1
			#PBS -l walltime=%WALLCLOCK%:00
			#PBS -A %HPCPROJ%
			#
			###############################################################################
			""")

	HEADER_CLEAN = textwrap.dedent("""\
			#!/bin/sh
			###############################################################################
			#                   %TASKTYPE% %EXPID% EXPERIMENT
			###############################################################################
			#
			#PBS -N %JOBNAME%
			#PBS -l select=serial=true:ncpus=1
			#PBS -l walltime=%WALLCLOCK%:00
			#PBS -A %HPCPROJ%
			#
			###############################################################################
			""")

class BscHeader:
	"""Class to handle the BSC headers of a job"""
	
	HEADER_REMOTESETUP = textwrap.dedent("""\
			#!/bin/ksh
			###############################################################################
			#                     %TASKTYPE% %EXPID% EXPERIMENT
			###############################################################################
			#
			#@ job_name         = %JOBNAME%
			#@ wall_clock_limit = %WALLCLOCK%
			#@ output           = %SCRATCH_DIR%/%HPCUSER%/%EXPID%/LOG_%EXPID%/%JOBNAME%_%j.out
			#@ error            = %SCRATCH_DIR%/%HPCUSER%/%EXPID%/LOG_%EXPID%/%JOBNAME%_%j.err
			#@ total_tasks      = %NUMTASK%
			#@ initialdir       = %SCRATCH_DIR%/%HPCUSER%/%EXPID%/
			#@ class            = %CLASS%
			#@ partition        = %PARTITION%
			#@ features         = %FEATURES%
			#
			###############################################################################
			""")

	HEADER_INI = textwrap.dedent("""\
			#!/bin/ksh
			###############################################################################
			#                     %TASKTYPE% %EXPID% EXPERIMENT
			###############################################################################
			#
			#@ job_name         = %JOBNAME%
			#@ wall_clock_limit = %WALLCLOCK%
			#@ output           = %SCRATCH_DIR%/%HPCUSER%/%EXPID%/LOG_%EXPID%/%JOBNAME%_%j.out
			#@ error            = %SCRATCH_DIR%/%HPCUSER%/%EXPID%/LOG_%EXPID%/%JOBNAME%_%j.err
			#@ total_tasks      = %NUMTASK%
			#@ initialdir       = %SCRATCH_DIR%/%HPCUSER%/%EXPID%/
			#@ class            = %CLASS%
			#@ partition        = %PARTITION%
			#@ features         = %FEATURES%
			#
			###############################################################################
			""")

	HEADER_SIM = textwrap.dedent("""\
			#!/bin/ksh
			###############################################################################
			#                     %TASKTYPE% %EXPID% EXPERIMENT
			###############################################################################
			#
			#@ job_name         = %JOBNAME%
			#@ wall_clock_limit = %WALLCLOCK%
			#@ output           = %SCRATCH_DIR%/%HPCUSER%/%EXPID%/LOG_%EXPID%/%JOBNAME%_%j.out
			#@ error            = %SCRATCH_DIR%/%HPCUSER%/%EXPID%/LOG_%EXPID%/%JOBNAME%_%j.err
			#@ total_tasks      = %NUMTASK%
			#@ initialdir       = %SCRATCH_DIR%/%HPCUSER%/%EXPID%/
			#@ tasks_per_node	= %TASKSNODE%
			#@ tracing			= %TRACING%
			#
			###############################################################################
			""")

	HEADER_POST = textwrap.dedent("""\
			#!/bin/ksh
			###############################################################################
			#                     %TASKTYPE% %EXPID% EXPERIMENT
			###############################################################################
			#
			#@ job_name         = %JOBNAME%
			#@ wall_clock_limit = %WALLCLOCK%
			#@ output           = %SCRATCH_DIR%/%HPCUSER%/%EXPID%/LOG_%EXPID%/%JOBNAME%_%j.out
			#@ error            = %SCRATCH_DIR%/%HPCUSER%/%EXPID%/LOG_%EXPID%/%JOBNAME%_%j.err
			#@ total_tasks      = %NUMTASK%
			#@ initialdir       = %SCRATCH_DIR%/%HPCUSER%/%EXPID%/
			#@ tracing			 = %TRACING%
			#@ scratch          = %SCRATCH%
			#
			###############################################################################
			""")

	HEADER_CLEAN = textwrap.dedent("""\
			#!/bin/ksh
			###############################################################################
			#                     %TASKTYPE% %EXPID% EXPERIMENT        
			###############################################################################
			#
			#@ job_name         = %JOBNAME%
			#@ wall_clock_limit = %WALLCLOCK%
			#@ output           = %SCRATCH_DIR%/%HPCUSER%/%EXPID%/LOG_%EXPID%/%JOBNAME%_%j.out
			#@ error            = %SCRATCH_DIR%/%HPCUSER%/%EXPID%/LOG_%EXPID%/%JOBNAME%_%j.err
			#@ total_tasks      = %NUMTASK%
			#@ initialdir       = %SCRATCH_DIR%/%HPCUSER%/%EXPID%/
			#@ tasks_per_node	= %TASKSNODE%
			#@ tracing			= %TRACING%
			#@ class            = %CLASS%
			#@ partition        = %PARTITION%
			#@ features         = %FEATURES%
			#
			###############################################################################
			""")

class EcHeader:
	"""Class to handle the ECMWF headers of a job"""

	HEADER_REMOTESETUP = textwrap.dedent("""\
			#!/bin/ksh
			###############################################################################
			#                   %TASKTYPE% %EXPID% EXPERIMENT
			###############################################################################
			#
			#@ shell            = /usr/bin/ksh 
			#@ class            = ns
			#@ job_type         = serial
			#@ job_name         = %JOBNAME%
			#@ output           = %SCRATCH_DIR%/%HPCPROJ%/%HPCUSER%/%EXPID%/LOG_%EXPID%/$(job_name).$(jobid).out 
			#@ error            = %SCRATCH_DIR%/%HPCPROJ%/%HPCUSER%/%EXPID%/LOG_%EXPID%/$(job_name).$(jobid).err 
			#@ notification     = error
			#@ resources        = ConsumableCpus(1) ConsumableMemory(1200mb)
			#@ wall_clock_limit = %WALLCLOCK%:00
			#@ queue
			#
			###############################################################################
			""")

	HEADER_INI = textwrap.dedent("""\
			#!/bin/ksh
			###############################################################################
			#                   %TASKTYPE% %EXPID% EXPERIMENT
			###############################################################################
			#
			#@ shell            = /usr/bin/ksh 
			#@ class            = ns
			#@ job_type         = serial
			#@ job_name         = %JOBNAME%
			#@ output           = %SCRATCH_DIR%/%HPCPROJ%/%HPCUSER%/%EXPID%/LOG_%EXPID%/$(job_name).$(jobid).out 
			#@ error            = %SCRATCH_DIR%/%HPCPROJ%/%HPCUSER%/%EXPID%/LOG_%EXPID%/$(job_name).$(jobid).err 
			#@ notification     = error
			#@ resources        = ConsumableCpus(1) ConsumableMemory(1200mb)
			#@ wall_clock_limit = %WALLCLOCK%:00
			#@ queue
			#
			###############################################################################
			""")


	HEADER_SIM = textwrap.dedent("""\
			#!/bin/ksh
			###############################################################################
			#                   %TASKTYPE% %EXPID% EXPERIMENT
			###############################################################################
			#
			#@ shell            = /usr/bin/ksh 
			#@ class            = np
			#@ job_type         = parallel
			#@ job_name         = %JOBNAME%
			#@ output           = %SCRATCH_DIR%/%HPCPROJ%/%HPCUSER%/%EXPID%/LOG_%EXPID%/$(job_name).$(jobid).out 
			#@ error            = %SCRATCH_DIR%/%HPCPROJ%/%HPCUSER%/%EXPID%/LOG_%EXPID%/$(job_name).$(jobid).err 
			#@ notification     = error
			#@ resources        = ConsumableCpus(1) ConsumableMemory(1200mb)
			#@ ec_smt           = no
			#@ total_tasks      = %NUMPROC% 
			#@ wall_clock_limit = %WALLCLOCK%:00
			#@ queue
			#
			###############################################################################
			""")

	HEADER_POST = textwrap.dedent("""\
			#!/bin/ksh
			###############################################################################
			#                   %TASKTYPE% %EXPID% EXPERIMENT
			###############################################################################
			#
			#@ shell            = /usr/bin/ksh 
			#@ class            = np
			#@ job_type         = parallel
			#@ job_name         = %JOBNAME%
			#@ output           = %SCRATCH_DIR%/%HPCPROJ%/%HPCUSER%/%EXPID%/LOG_%EXPID%/$(job_name).$(jobid).out 
			#@ error            = %SCRATCH_DIR%/%HPCPROJ%/%HPCUSER%/%EXPID%/LOG_%EXPID%/$(job_name).$(jobid).err 
			#@ notification     = error
			#@ resources        = ConsumableCpus(1) ConsumableMemory(1200mb)
			#@ ec_smt           = no
			#@ total_tasks      = %NUMPROC% 
			#@ wall_clock_limit = %WALLCLOCK%:00
			#@ queue
			#
			###############################################################################
			""")

	HEADER_CLEAN = textwrap.dedent("""\
			#!/bin/ksh
			###############################################################################
			#                   %TASKTYPE% %EXPID% EXPERIMENT
			###############################################################################
			#
			#@ shell            = /usr/bin/ksh 
			#@ class            = ns
			#@ job_type         = serial
			#@ job_name         = %JOBNAME%
			#@ output           = %SCRATCH_DIR%/%HPCPROJ%/%HPCUSER%/%EXPID%/LOG_%EXPID%/$(job_name).$(jobid).out 
			#@ error            = %SCRATCH_DIR%/%HPCPROJ%/%HPCUSER%/%EXPID%/LOG_%EXPID%/$(job_name).$(jobid).err 
			#@ notification     = error
			#@ resources        = ConsumableCpus(1) ConsumableMemory(1200mb)
			#@ wall_clock_limit = %WALLCLOCK%:00
			#@ queue
			#
			###############################################################################
			""")

class HtHeader:
	"""Class to handle the Hector headers of a job"""

	HEADER_REMOTESETUP = textwrap.dedent("""\
			#!/bin/sh
			###############################################################################
			#                   %TASKTYPE% %EXPID% EXPERIMENT
			###############################################################################
			#
			#PBS -N %JOBNAME%
			#PBS -q serial
			#PBS -l cput=%WALLCLOCK%:00
			#PBS -A %HPCPROJ%
			#
			###############################################################################
			""")

	HEADER_INI = textwrap.dedent("""\
			#!/bin/sh
			###############################################################################
			#                   %TASKTYPE% %EXPID% EXPERIMENT
			###############################################################################
			#
			#PBS -N %JOBNAME%
			#PBS -q serial
			#PBS -l cput=%WALLCLOCK%:00
			#PBS -A %HPCPROJ%
			#
			###############################################################################
			""")

	HEADER_SIM = textwrap.dedent("""\
			#!/bin/sh
			###############################################################################
			#                   %TASKTYPE% %EXPID% EXPERIMENT
			###############################################################################
			#
			#PBS -N %JOBNAME%
			#PBS -l mppwidth=%NUMPROC%
			#PBS -l mppnppn=32
			#PBS -l walltime=%WALLCLOCK%:00
			#PBS -A %HPCPROJ%
			#
			###############################################################################
			""")

	HEADER_POST = textwrap.dedent("""\
			#!/bin/sh
			###############################################################################
			#                   %TASKTYPE% %EXPID% EXPERIMENT
			###############################################################################
			#
			#PBS -N %JOBNAME%
			#PBS -q serial
			#PBS -l cput=%WALLCLOCK%:00
			#PBS -A %HPCPROJ%
			#
			###############################################################################
			""")

	HEADER_CLEAN = textwrap.dedent("""\
			#!/bin/sh
			###############################################################################
			#                   %TASKTYPE% %EXPID% EXPERIMENT
			###############################################################################
			#
			#PBS -N %JOBNAME%
			#PBS -q serial
			#PBS -l cput=%WALLCLOCK%:00
			#PBS -A %HPCPROJ%
			#
			###############################################################################
			""")

class ItHeader:
	"""Class to handle the Ithaca headers of a job"""

	HEADER_REMOTESETUP = textwrap.dedent("""\
			#!/bin/sh
			###############################################################################
			#                   %TASKTYPE% %EXPID% EXPERIMENT
			###############################################################################
			#   
			#$ -S /bin/sh
			#$ -N %JOBNAME%
			#$ -e %SCRATCH_DIR%/%HPCPROJ%/%HPCUSER%/%EXPID%/LOG_%EXPID%/
			#$ -o %SCRATCH_DIR%/%HPCPROJ%/%HPCUSER%/%EXPID%/LOG_%EXPID%/
			#$ -V
			#$ -l h_rt=%WALLCLOCK%:00
			#
			###############################################################################
			""")

	HEADER_INI = textwrap.dedent("""\
			#!/bin/sh
			###############################################################################
			#                   %TASKTYPE% %EXPID% EXPERIMENT
			###############################################################################
			#   
			#$ -S /bin/sh
			#$ -N %JOBNAME%
			#$ -e %SCRATCH_DIR%/%HPCPROJ%/%HPCUSER%/%EXPID%/LOG_%EXPID%/
			#$ -o %SCRATCH_DIR%/%HPCPROJ%/%HPCUSER%/%EXPID%/LOG_%EXPID%/
			#$ -V
			#$ -l h_rt=%WALLCLOCK%:00
			#
			###############################################################################
			""")

	HEADER_SIM = textwrap.dedent("""\
			#!/bin/sh
			###############################################################################
			#                   %TASKTYPE% %EXPID% EXPERIMENT
			###############################################################################
			#   
			#$ -S /bin/sh
			#$ -N %JOBNAME%
			#$ -e %SCRATCH_DIR%/%HPCPROJ%/%HPCUSER%/%EXPID%/LOG_%EXPID%/
			#$ -o %SCRATCH_DIR%/%HPCPROJ%/%HPCUSER%/%EXPID%/LOG_%EXPID%/
			#$ -V
			#$ -l h_rt=%WALLCLOCK%:00
			#$ -pe orte %NUMPROC% 
			#
			###############################################################################
			""")

	HEADER_POST = textwrap.dedent("""\
			#!/bin/sh
			###############################################################################
			#                   %TASKTYPE% %EXPID% EXPERIMENT
			###############################################################################
			#   
			#$ -S /bin/sh
			#$ -N %JOBNAME%
			#$ -e %SCRATCH_DIR%/%HPCPROJ%/%HPCUSER%/%EXPID%/LOG_%EXPID%/
			#$ -o %SCRATCH_DIR%/%HPCPROJ%/%HPCUSER%/%EXPID%/LOG_%EXPID%/
			#$ -V
			#$ -l h_rt=%WALLCLOCK%:00
			#
			###############################################################################
			""")

	HEADER_CLEAN = textwrap.dedent("""\
			#!/bin/sh
			###############################################################################
			#                   %TASKTYPE% %EXPID% EXPERIMENT
			###############################################################################
			#   
			#$ -S /bin/sh
			#$ -N %JOBNAME%
			#$ -e %SCRATCH_DIR%/%HPCPROJ%/%HPCUSER%/%EXPID%/LOG_%EXPID%/
			#$ -o %SCRATCH_DIR%/%HPCPROJ%/%HPCUSER%/%EXPID%/LOG_%EXPID%/
			#$ -V
			#$ -l h_rt=%WALLCLOCK%:00
			#
			###############################################################################
			""")

class LgHeader:
	"""Class to handle the Lindgren headers of a job"""

	HEADER_REMOTESETUP = textwrap.dedent("""\
			#!/bin/sh
			###############################################################################
			#                         %TASKTYPE% %EXPID% EXPERIMENT
			###############################################################################
			#
			#!/bin/sh --login
			#PBS -N %JOBNAME%
			#PBS -l mppwidth=%NUMPROC%
			#PBS -l mppnppn=%NUMTASK%
			#PBS -l walltime=%WALLCLOCK%
			#PBS -e %SCRATCH_DIR%/%HPCPROJ%/%HPCUSER%/%EXPID%/LOG_%EXPID%
			#PBS -o %SCRATCH_DIR%/%HPCPROJ%/%HPCUSER%/%EXPID%/LOG_%EXPID%
			#
			###############################################################################
			""")

	HEADER_INI = textwrap.dedent("""\
			#!/bin/sh
			###############################################################################
			#                         %TASKTYPE% %EXPID% EXPERIMENT
			###############################################################################
			#
			#!/bin/sh --login
			#PBS -N %JOBNAME%
			#PBS -l mppwidth=%NUMPROC%
			#PBS -l mppnppn=%NUMTASK%
			#PBS -l walltime=%WALLCLOCK%
			#PBS -e %SCRATCH_DIR%/%HPCPROJ%/%HPCUSER%/%EXPID%/LOG_%EXPID%
			#PBS -o %SCRATCH_DIR%/%HPCPROJ%/%HPCUSER%/%EXPID%/LOG_%EXPID%
			#
			###############################################################################
			""")

	HEADER_SIM = textwrap.dedent("""\
			#!/bin/sh
			###############################################################################
			#                         %TASKTYPE% %EXPID% EXPERIMENT
			###############################################################################
			#
			#!/bin/sh --login
			#PBS -N %JOBNAME%
			#PBS -l mppwidth=%NUMPROC%
			#PBS -l mppnppn=%NUMTASK%
			#PBS -l walltime=%WALLCLOCK%
			#PBS -e %SCRATCH_DIR%/%HPCPROJ%/%HPCUSER%/%EXPID%/LOG_%EXPID%
			#PBS -o %SCRATCH_DIR%/%HPCPROJ%/%HPCUSER%/%EXPID%/LOG_%EXPID%
			#
			###############################################################################
			""")

	HEADER_POST = textwrap.dedent("""\
			#!/bin/sh
			###############################################################################
			#                         %TASKTYPE% %EXPID% EXPERIMENT
			###############################################################################
			#
			#!/bin/sh --login
			#PBS -N %JOBNAME%
			#PBS -l mppwidth=%NUMPROC%
			#PBS -l mppnppn=%NUMTASK%
			#PBS -l walltime=%WALLCLOCK%
			#PBS -e %SCRATCH_DIR%/%HPCPROJ%/%HPCUSER%/%EXPID%/LOG_%EXPID%
			#PBS -o %SCRATCH_DIR%/%HPCPROJ%/%HPCUSER%/%EXPID%/LOG_%EXPID%
			#
			###############################################################################
			""")

	HEADER_CLEAN = textwrap.dedent("""\
			#!/bin/sh
			###############################################################################
			#                         %TASKTYPE% %EXPID% EXPERIMENT
			###############################################################################
			#
			#!/bin/sh --login
			#PBS -N %JOBNAME%
			#PBS -l mppwidth=%NUMPROC%
			#PBS -l mppnppn=%NUMTASK%
			#PBS -l walltime=%WALLCLOCK%
			#PBS -e %SCRATCH_DIR%/%HPCPROJ%/%HPCUSER%/%EXPID%/LOG_%EXPID%
			#PBS -o %SCRATCH_DIR%/%HPCPROJ%/%HPCUSER%/%EXPID%/LOG_%EXPID%
			#
			###############################################################################
			""")

class MnHeader:
	"""Class to handle the MareNostrum 3 headers of a job"""

	HEADER_REMOTESETUP = textwrap.dedent("""\
			#!/bin/sh
			###############################################################################
			#                   %TASKTYPE% %EXPID% EXPERIMENT
			###############################################################################
			#
			#BSUB -J %JOBNAME%
			#BSUB -oo %SCRATCH_DIR%/%HPCPROJ%/%HPCUSER%/%EXPID%/LOG_%EXPID%/%JOBNAME%_%J.out 
			#BSUB -eo %SCRATCH_DIR%/%HPCPROJ%/%HPCUSER%/%EXPID%/LOG_%EXPID%/%JOBNAME%_%J.err
			#BSUB -W %WALLCLOCK%
			#BSUB -n %NUMPROC%
			#BSUB -R "span[ptile=16]"
			#
			###############################################################################
			""")

	HEADER_INI = textwrap.dedent("""\
			#!/bin/sh
			###############################################################################
			#                   %TASKTYPE% %EXPID% EXPERIMENT
			###############################################################################
			#
			#BSUB -J %JOBNAME%
			#BSUB -oo %SCRATCH_DIR%/%HPCPROJ%/%HPCUSER%/%EXPID%/LOG_%EXPID%/%JOBNAME%_%J.out 
			#BSUB -eo %SCRATCH_DIR%/%HPCPROJ%/%HPCUSER%/%EXPID%/LOG_%EXPID%/%JOBNAME%_%J.err
			#BSUB -W %WALLCLOCK%
			#BSUB -n %NUMPROC%
			#BSUB -R "span[ptile=16]"
			#
			###############################################################################
			""")

	HEADER_SIM = textwrap.dedent("""\
			#!/bin/sh
			###############################################################################
			#                   %TASKTYPE% %EXPID% EXPERIMENT
			###############################################################################
			#
			#BSUB -J %JOBNAME%
			#BSUB -oo %SCRATCH_DIR%/%HPCPROJ%/%HPCUSER%/%EXPID%/LOG_%EXPID%/%JOBNAME%_%J.out 
			#BSUB -eo %SCRATCH_DIR%/%HPCPROJ%/%HPCUSER%/%EXPID%/LOG_%EXPID%/%JOBNAME%_%J.err
			#BSUB -W %WALLCLOCK%
			#BSUB -n %NUMPROC%
			#BSUB -R "span[ptile=16]"
			#
			###############################################################################
			""")

	HEADER_POST = textwrap.dedent("""\
			#!/bin/sh
			###############################################################################
			#                   %TASKTYPE% %EXPID% EXPERIMENT
			###############################################################################
			#
			#BSUB -J %JOBNAME%
			#BSUB -oo %SCRATCH_DIR%/%HPCPROJ%/%HPCUSER%/%EXPID%/LOG_%EXPID%/%JOBNAME%_%J.out 
			#BSUB -eo %SCRATCH_DIR%/%HPCPROJ%/%HPCUSER%/%EXPID%/LOG_%EXPID%/%JOBNAME%_%J.err
			#BSUB -W %WALLCLOCK%
			#BSUB -n %NUMPROC%
			#BSUB -R "span[ptile=16]"
			#BSUB -x
			#
			###############################################################################
			""")

	HEADER_CLEAN = textwrap.dedent("""\
			#!/bin/sh
			###############################################################################
			#                   %TASKTYPE% %EXPID% EXPERIMENT
			###############################################################################
			#
			#BSUB -J %JOBNAME%
			#BSUB -oo %SCRATCH_DIR%/%HPCPROJ%/%HPCUSER%/%EXPID%/LOG_%EXPID%/%JOBNAME%_%J.out 
			#BSUB -eo %SCRATCH_DIR%/%HPCPROJ%/%HPCUSER%/%EXPID%/LOG_%EXPID%/%JOBNAME%_%J.err
			#BSUB -W %WALLCLOCK%
			#BSUB -n %NUMPROC%
			#BSUB -R "span[ptile=16]"
			#
			###############################################################################
			""")
