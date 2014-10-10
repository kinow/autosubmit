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

class Template:
	"""Class to handle the template code snippet of a job.
	At the moment contains 7 templates:
	WRAPPING are for bundle of jobs to execute with python wrapper
	SIMULATION are for multiprocessor jobs
	POSTPROCESSING are single processor jobs
	ClEANING are archiving job---> dealing with large transfer of data on tape
	INITIALISATION are jobs which transfer data from tape to disk
	LOCALSETUP are for source code preparation local jobs
	REMOTESETUP are for soruce code compilation jobs
	TRANSFER are for downloading data jobs"""
	WRAPPING = textwrap.dedent("""\
			%AS-HEADER-REM%

			#scriptname1 scriptname2 ...
			jobs="%JOBS%"
			scratch=%SCRATCH_DIR%
			project=%HPCPROJ%
			user=%HPCUSER%
			expid=%EXPID%
			remote_log_dir=${scratch}/${project}/${user}/${expid}/LOG_${expid}

			for template in $jobs; 
			do 
				touch ${remote_log_dir}/${template}.cmd
				bash ${remote_log_dir}/${template}.cmd > ${remote_log_dir}/${template}_${LSB_JOBID}.out 2> ${remote_log_dir}/${template}_${LSB_JOBID}.err
				echo "bash "${remote_log_dir}"/"${template}".cmd > "${remote_log_dir}"/"${template}"_"${LSB_JOBID}".out 2> "${remote_log_dir}"/"${template}"_${LSB_JOBID}"".err"
				echo "Status from "${template}" is "
			done
			
			%AS-TAILER-REM%""")

	LOCALSETUP = textwrap.dedent("""\
			%AS-HEADER-LOC%

			%AS-TAILER-LOC%""")
	
	REMOTESETUP = textwrap.dedent("""\
			%AS-HEADER-REM%
			
			%AS-TAILER-REM%""")


	INITIALISATION = textwrap.dedent("""\
			%AS-HEADER-REM%
			
			%AS-TAILER-REM%""")

	SIMULATION = textwrap.dedent("""\
			%AS-HEADER-REM%
			
			%AS-TAILER-REM%""")

	POSTPROCESSING = textwrap.dedent("""\
			%AS-HEADER-REM%
			
			%AS-TAILER-REM%""")

	CLEANING = textwrap.dedent("""\
			%AS-HEADER-REM%
			
			%AS-TAILER-REM%""")

	TRANSFER = textwrap.dedent("""\
			%AS-HEADER-LOC%
			
			%AS-TAILER-LOC%""")


class StatisticsSnippet:
	"""Class to handle the statistics snippet of a job"""

	AS_HEADER = textwrap.dedent("""\
			echo "header"
			""")
	AS_TAILER = textwrap.dedent("""\
			echo "tailer"
			""")


class PsHeader:
	"""Class to handle the Ps headers of a job"""
	
	HEADER_LOCALSETUP = textwrap.dedent("""\
			#!/bin/bash
	 		###############################################################################
	 		#                   %%TASKTYPE%% %%TEMPLATE_NAME%% EXPERIMENT
	 		###############################################################################""")

	HEADER_LOCALTRANS = textwrap.dedent("""\
			#!/bin/bash
	 		###############################################################################
	 		#                   %%TASKTYPE%% %%TEMPLATE_NAME%% EXPERIMENT
	 		###############################################################################""")

	
class ArHeader:
	"""Class to handle the Archer headers of a job"""

	HEADER_WRP = textwrap.dedent("""\
			#!/bin/sh
	 		###############################################################################
	 		#                   %%TASKTYPE%% %%TEMPLATE_NAME%% EXPERIMENT
	 		###############################################################################
	 		#
	 		#PBS -N %%JOBNAME%%
	 		#PBS -l select=%%NUMPROC%%
	 		#PBS -l walltime=%%WALLCLOCK%%:00
	 		#PBS -A %%HPCPROJ%%
	 		#
	 		###############################################################################""")


	HEADER_REMOTESETUP = textwrap.dedent("""\
			#!/bin/sh
	 		###############################################################################
	 		#                   %%TASKTYPE%% %%TEMPLATE_NAME%% EXPERIMENT
	 		###############################################################################
	 		#
	 		#PBS -N %%JOBNAME%%
	 		#PBS -l select=serial=true:ncpus=1
	 		#PBS -l walltime=%%WALLCLOCK%%:00
	 		#PBS -A %%HPCPROJ%%
	 		#
	 		###############################################################################""")

	HEADER_INI = textwrap.dedent("""\
			#!/bin/sh
	 		###############################################################################
	 		#                   %%TASKTYPE%% %%TEMPLATE_NAME%% EXPERIMENT
	 		###############################################################################
	 		#
	 		#PBS -N %%JOBNAME%%
	 		#PBS -l select=serial=true:ncpus=1
	 		#PBS -l walltime=%%WALLCLOCK%%:00
	 		#PBS -A %%HPCPROJ%%
	 		#
	 		###############################################################################""")

	HEADER_SIM = textwrap.dedent("""\
			#!/bin/sh
			###############################################################################
	 		#                   %%TASKTYPE%% %%TEMPLATE_NAME%% EXPERIMENT
	 		###############################################################################
	 		#
	 		#PBS -N %%JOBNAME%%
	 		#PBS -l select=%%NUMPROC%%
	 		#PBS -l walltime=%%WALLCLOCK%%:00
	 		#PBS -A %%HPCPROJ%%
	 		#
	 		###############################################################################""")

	HEADER_POST = textwrap.dedent("""\
			#!/bin/sh
	 		###############################################################################
	 		#                   %%TASKTYPE%% %%TEMPLATE_NAME%% EXPERIMENT
	 		###############################################################################
	 		#
	 		#PBS -N %%JOBNAME%%
	 		#PBS -l select=serial=true:ncpus=1
	 		#PBS -l walltime=%%WALLCLOCK%%:00
	 		#PBS -A %%HPCPROJ%%
	 		#
	 		###############################################################################""")

	HEADER_CLEAN = textwrap.dedent("""\
			#!/bin/sh
	 		###############################################################################
	 		#                   %%TASKTYPE%% %%TEMPLATE_NAME%% EXPERIMENT
	 		###############################################################################
	 		#
	 		#PBS -N %%JOBNAME%%
	 		#PBS -l select=serial=true:ncpus=1
	 		#PBS -l walltime=%%WALLCLOCK%%:00
	 		#PBS -A %%HPCPROJ%%
	 		#
	 		###############################################################################""")

class BscHeader:
	"""Class to handle the BSC headers of a job"""

	HEADER_WRP = textwrap.dedent("""\
			#!/bin/ksh
 			###############################################################################
			#                     %%TASKTYPE%% %%TEMPLATE_NAME%% EXPERIMENT
			###############################################################################
			#
 			#@ job_name         = %%JOBNAME%%
 			#@ wall_clock_limit = %%WALLCLOCK%%
 			#@ output           = %%SCRATCH_DIR%%/%%HPCUSER%%/%%EXPID%%/LOG_%%EXPID%%/%%JOBNAME%%_%%j.out
 			#@ error            = %%SCRATCH_DIR%%/%%HPCUSER%%/%%EXPID%%/LOG_%%EXPID%%/%%JOBNAME%%_%%j.err
 			#@ total_tasks      = %%NUMTASK%%
 			#@ initialdir       = %%SCRATCH_DIR%%/%%HPCUSER%%/%%EXPID%%/
 			#@ class            = %%CLASS%%
 			#@ partition        = %%PARTITION%%
 			#@ features         = %%FEATURES%%
 			#
 			###############################################################################""")

	HEADER_REMOTESETUP = textwrap.dedent("""\
			#!/bin/ksh
 			###############################################################################
 			#                     %%TASKTYPE%% %%TEMPLATE_NAME%% EXPERIMENT
			###############################################################################
			#
 			#@ job_name         = %%JOBNAME%%
 			#@ wall_clock_limit = %%WALLCLOCK%%
 			#@ output           = %%SCRATCH_DIR%%/%%HPCUSER%%/%%EXPID%%/LOG_%%EXPID%%/%%JOBNAME%%_%%j.out
 			#@ error            = %%SCRATCH_DIR%%/%%HPCUSER%%/%%EXPID%%/LOG_%%EXPID%%/%%JOBNAME%%_%%j.err
 			#@ total_tasks      = %%NUMTASK%%
 			#@ initialdir       = %%SCRATCH_DIR%%/%%HPCUSER%%/%%EXPID%%/
 			#@ class            = %%CLASS%%
 			#@ partition        = %%PARTITION%%
 			#@ features         = %%FEATURES%%
 			#
 			###############################################################################""")

	HEADER_INI = textwrap.dedent("""\
			#!/bin/ksh
			###############################################################################
			#                     %%TASKTYPE%% %%TEMPLATE_NAME%% EXPERIMENT
			###############################################################################
			#
			#@ job_name         = %%JOBNAME%%
			#@ wall_clock_limit = %%WALLCLOCK%%
			#@ output           = %%SCRATCH_DIR%%/%%HPCUSER%%/%%EXPID%%/LOG_%%EXPID%%/%%JOBNAME%%_%%j.out
			#@ error            = %%SCRATCH_DIR%%/%%HPCUSER%%/%%EXPID%%/LOG_%%EXPID%%/%%JOBNAME%%_%%j.err
			#@ total_tasks      = %%NUMTASK%%
			#@ initialdir       = %%SCRATCH_DIR%%/%%HPCUSER%%/%%EXPID%%/
			#@ class            = %%CLASS%%
			#@ partition        = %%PARTITION%%
			#@ features         = %%FEATURES%%
			#
			###############################################################################""")

	HEADER_SIM = textwrap.dedent("""\
			#!/bin/ksh
			###############################################################################
			#                     %%TASKTYPE%% %%TEMPLATE_NAME%% EXPERIMENT
			###############################################################################
			#
			#@ job_name         = %%JOBNAME%%
			#@ wall_clock_limit = %%WALLCLOCK%%
			#@ output           = %%SCRATCH_DIR%%/%%HPCUSER%%/%%EXPID%%/LOG_%%EXPID%%/%%JOBNAME%%_%%j.out
			#@ error            = %%SCRATCH_DIR%%/%%HPCUSER%%/%%EXPID%%/LOG_%%EXPID%%/%%JOBNAME%%_%%j.err
			#@ total_tasks      = %%NUMTASK%%
			#@ initialdir       = %%SCRATCH_DIR%%/%%HPCUSER%%/%%EXPID%%/
			#@ tasks_per_node	= %%TASKSNODE%%
			#@ tracing			= %%TRACING%%
			#
			###############################################################################""")

	HEADER_POST = textwrap.dedent("""\
			#!/bin/ksh
			###############################################################################
			#                     %%TASKTYPE%% %%TEMPLATE_NAME%% EXPERIMENT
			###############################################################################
			#
			#@ job_name         = %%JOBNAME%%
			#@ wall_clock_limit = %%WALLCLOCK%%
			#@ output           = %%SCRATCH_DIR%%/%%HPCUSER%%/%%EXPID%%/LOG_%%EXPID%%/%%JOBNAME%%_%%j.out
			#@ error            = %%SCRATCH_DIR%%/%%HPCUSER%%/%%EXPID%%/LOG_%%EXPID%%/%%JOBNAME%%_%%j.err
			#@ total_tasks      = %%NUMTASK%%
			#@ initialdir       = %%SCRATCH_DIR%%/%%HPCUSER%%/%%EXPID%%/
			#@ tracing			 = %%TRACING%%
			#@ scratch          = %%SCRATCH%%
			#
			###############################################################################""")

	HEADER_CLEAN = textwrap.dedent("""\
			#!/bin/ksh
			###############################################################################
			#                     %%TASKTYPE%% %%TEMPLATE_NAME%% EXPERIMENT        
			###############################################################################
			#
			#@ job_name         = %%JOBNAME%%
			#@ wall_clock_limit = %%WALLCLOCK%%
			#@ output           = %%SCRATCH_DIR%%/%%HPCUSER%%/%%EXPID%%/LOG_%%EXPID%%/%%JOBNAME%%_%%j.out
			#@ error            = %%SCRATCH_DIR%%/%%HPCUSER%%/%%EXPID%%/LOG_%%EXPID%%/%%JOBNAME%%_%%j.err
			#@ total_tasks      = %%NUMTASK%%
			#@ initialdir       = %%SCRATCH_DIR%%/%%HPCUSER%%/%%EXPID%%/
			#@ tasks_per_node	= %%TASKSNODE%%
			#@ tracing			= %%TRACING%%
			#@ class            = %%CLASS%%
			#@ partition        = %%PARTITION%%
			#@ features         = %%FEATURES%%
			#
			###############################################################################""")

class EcHeader:
	"""Class to handle the ECMWF headers of a job"""

	HEADER_WRP = textwrap.dedent("""\
			#!/bin/ksh
			###############################################################################
			#                   %%TASKTYPE%% %%TEMPLATE_NAME%% EXPERIMENT
			###############################################################################
			#
			#@ shell            = /usr/bin/ksh 
			#@ class            = ns
			#@ job_type         = serial
			#@ job_name         = %%JOBNAME%%
			#@ output           = %%SCRATCH_DIR%%/%%HPCPROJ%%/%%HPCUSER%%/%%EXPID%%/LOG_%%EXPID%%/$(job_name).$(jobid).out 
			#@ error            = %%SCRATCH_DIR%%/%%HPCPROJ%%/%%HPCUSER%%/%%EXPID%%/LOG_%%EXPID%%/$(job_name).$(jobid).err 
			#@ notification     = error
			#@ resources        = ConsumableCpus(1) ConsumableMemory(1200mb)
			#@ wall_clock_limit = %%WALLCLOCK%%:00
			#@ queue
			#
			###############################################################################""")

	HEADER_REMOTESETUP = textwrap.dedent("""\
			#!/bin/ksh
			###############################################################################
			#                   %%TASKTYPE%% %%TEMPLATE_NAME%% EXPERIMENT
			###############################################################################
			#
			#@ shell            = /usr/bin/ksh 
			#@ class            = ns
			#@ job_type         = serial
			#@ job_name         = %%JOBNAME%%
			#@ output           = %%SCRATCH_DIR%%/%%HPCPROJ%%/%%HPCUSER%%/%%EXPID%%/LOG_%%EXPID%%/$(job_name).$(jobid).out 
			#@ error            = %%SCRATCH_DIR%%/%%HPCPROJ%%/%%HPCUSER%%/%%EXPID%%/LOG_%%EXPID%%/$(job_name).$(jobid).err 
			#@ notification     = error
			#@ resources        = ConsumableCpus(1) ConsumableMemory(1200mb)
			#@ wall_clock_limit = %%WALLCLOCK%%:00
			#@ queue
			#
			###############################################################################""")

	HEADER_INI = textwrap.dedent("""\
			#!/bin/ksh
			###############################################################################
			#                   %%TASKTYPE%% %%TEMPLATE_NAME%% EXPERIMENT
			###############################################################################
			#
			#@ shell            = /usr/bin/ksh 
			#@ class            = ns
			#@ job_type         = serial
			#@ job_name         = %%JOBNAME%%
			#@ output           = %%SCRATCH_DIR%%/%%HPCPROJ%%/%%HPCUSER%%/%%EXPID%%/LOG_%%EXPID%%/$(job_name).$(jobid).out 
			#@ error            = %%SCRATCH_DIR%%/%%HPCPROJ%%/%%HPCUSER%%/%%EXPID%%/LOG_%%EXPID%%/$(job_name).$(jobid).err 
			#@ notification     = error
			#@ resources        = ConsumableCpus(1) ConsumableMemory(1200mb)
			#@ wall_clock_limit = %%WALLCLOCK%%:00
			#@ queue
			#
			###############################################################################""")


	HEADER_SIM = textwrap.dedent("""\
			#!/bin/ksh
			###############################################################################
			#                   %%TASKTYPE%% %%TEMPLATE_NAME%% EXPERIMENT
			###############################################################################
			#
			#@ shell            = /usr/bin/ksh 
			#@ class            = np
			#@ job_type         = parallel
			#@ job_name         = %%JOBNAME%%
			#@ output           = %%SCRATCH_DIR%%/%%HPCPROJ%%/%%HPCUSER%%/%%EXPID%%/LOG_%%EXPID%%/$(job_name).$(jobid).out 
			#@ error            = %%SCRATCH_DIR%%/%%HPCPROJ%%/%%HPCUSER%%/%%EXPID%%/LOG_%%EXPID%%/$(job_name).$(jobid).err 
			#@ notification     = error
			#@ resources        = ConsumableCpus(1) ConsumableMemory(1200mb)
			#@ ec_smt           = no
			#@ total_tasks      = %%NUMPROC%% 
			#@ wall_clock_limit = %%WALLCLOCK%%:00
			#@ queue
			#
			###############################################################################""")

	HEADER_POST = textwrap.dedent("""\
			#!/bin/ksh
			###############################################################################
			#                   %%TASKTYPE%% %%TEMPLATE_NAME%% EXPERIMENT
			###############################################################################
			#
			#@ shell            = /usr/bin/ksh 
			#@ class            = np
			#@ job_type         = parallel
			#@ job_name         = %%JOBNAME%%
			#@ output           = %%SCRATCH_DIR%%/%%HPCPROJ%%/%%HPCUSER%%/%%EXPID%%/LOG_%%EXPID%%/$(job_name).$(jobid).out 
			#@ error            = %%SCRATCH_DIR%%/%%HPCPROJ%%/%%HPCUSER%%/%%EXPID%%/LOG_%%EXPID%%/$(job_name).$(jobid).err 
			#@ notification     = error
			#@ resources        = ConsumableCpus(1) ConsumableMemory(1200mb)
			#@ ec_smt           = no
			#@ total_tasks      = %%NUMPROC%% 
			#@ wall_clock_limit = %%WALLCLOCK%%:00
			#@ queue
			#
			###############################################################################""")

	HEADER_CLEAN = textwrap.dedent("""\
			#!/bin/ksh
			###############################################################################
			#                   %%TASKTYPE%% %%TEMPLATE_NAME%% EXPERIMENT
			###############################################################################
			#
			#@ shell            = /usr/bin/ksh 
			#@ class            = ns
			#@ job_type         = serial
			#@ job_name         = %%JOBNAME%%
			#@ output           = %%SCRATCH_DIR%%/%%HPCPROJ%%/%%HPCUSER%%/%%EXPID%%/LOG_%%EXPID%%/$(job_name).$(jobid).out 
			#@ error            = %%SCRATCH_DIR%%/%%HPCPROJ%%/%%HPCUSER%%/%%EXPID%%/LOG_%%EXPID%%/$(job_name).$(jobid).err 
			#@ notification     = error
			#@ resources        = ConsumableCpus(1) ConsumableMemory(1200mb)
			#@ wall_clock_limit = %%WALLCLOCK%%:00
			#@ queue
			#
			###############################################################################""")

class HtHeader:
	"""Class to handle the Hector headers of a job"""

	HEADER_WRP = textwrap.dedent("""\
			#!/bin/sh
			###############################################################################
			#                   %%TASKTYPE%% %%TEMPLATE_NAME%% EXPERIMENT
			###############################################################################
			#
			#PBS -N %%JOBNAME%%
			#PBS -l mppwidth=%%NUMPROC%%
			#PBS -l mppnppn=32
			#PBS -l walltime=%%WALLCLOCK%%:00
			#PBS -A %%HPCPROJ%%
			#
			###############################################################################""")

	HEADER_REMOTESETUP = textwrap.dedent("""\
			#!/bin/sh
			###############################################################################
			#                   %%TASKTYPE%% %%TEMPLATE_NAME%% EXPERIMENT
			###############################################################################
			#
			#PBS -N %%JOBNAME%%
			#PBS -q serial
			#PBS -l cput=%%WALLCLOCK%%:00
			#PBS -A %%HPCPROJ%%
			#
			###############################################################################""")

	HEADER_INI = textwrap.dedent("""\
			#!/bin/sh
			###############################################################################
			#                   %%TASKTYPE%% %%TEMPLATE_NAME%% EXPERIMENT
			###############################################################################
			#
			#PBS -N %%JOBNAME%%
			#PBS -q serial
			#PBS -l cput=%%WALLCLOCK%%:00
			#PBS -A %%HPCPROJ%%
			#
			###############################################################################""")

	HEADER_SIM = textwrap.dedent("""\
			#!/bin/sh
			###############################################################################
			#                   %%TASKTYPE%% %%TEMPLATE_NAME%% EXPERIMENT
			###############################################################################
			#
			#PBS -N %%JOBNAME%%
			#PBS -l mppwidth=%%NUMPROC%%
			#PBS -l mppnppn=32
			#PBS -l walltime=%%WALLCLOCK%%:00
			#PBS -A %%HPCPROJ%%
			#
			###############################################################################""")

	HEADER_POST = textwrap.dedent("""\
			#!/bin/sh
			###############################################################################
			#                   %%TASKTYPE%% %%TEMPLATE_NAME%% EXPERIMENT
			###############################################################################
			#
			#PBS -N %%JOBNAME%%
			#PBS -q serial
			#PBS -l cput=%%WALLCLOCK%%:00
			#PBS -A %%HPCPROJ%%
			#
			###############################################################################""")

	HEADER_CLEAN = textwrap.dedent("""\
			#!/bin/sh
			###############################################################################
			#                   %%TASKTYPE%% %%TEMPLATE_NAME%% EXPERIMENT
			###############################################################################
			#
			#PBS -N %%JOBNAME%%
			#PBS -q serial
			#PBS -l cput=%%WALLCLOCK%%:00
			#PBS -A %%HPCPROJ%%
			#
			###############################################################################""")

class ItHeader:
	"""Class to handle the Ithaca headers of a job"""

	HEADER_WRP = textwrap.dedent("""\
			#!/usr/bin/env python
			###############################################################################
			#                              %%TASKTYPE%%
			###############################################################################
			#$ -S /usr/bin/python
			#$ -N %%JOBNAME%%
			#$ -V
			#$ -cwd
			#$ -pe orte %%NUMPROC%%
			#
			###############################################################################
""")


	HEADER_REMOTESETUP = textwrap.dedent("""\
			#!/bin/sh
			###############################################################################
			#                   %%TASKTYPE%% %%TEMPLATE_NAME%% EXPERIMENT
			###############################################################################
			#   
			#$ -S /bin/sh
			#$ -N %%JOBNAME%%
			#$ -e %%SCRATCH_DIR%%/%%HPCPROJ%%/%%HPCUSER%%/%%EXPID%%/LOG_%%EXPID%%/
			#$ -o %%SCRATCH_DIR%%/%%HPCPROJ%%/%%HPCUSER%%/%%EXPID%%/LOG_%%EXPID%%/
			#$ -V
			#$ -l h_rt=%%WALLCLOCK%%:00
			#
			###############################################################################
""")

	HEADER_INI = textwrap.dedent("""\
			#!/bin/sh
			###############################################################################
			#                   %%TASKTYPE%% %%TEMPLATE_NAME%% EXPERIMENT
			###############################################################################
			#   
			#$ -S /bin/sh
			#$ -N %%JOBNAME%%
			#$ -e %%SCRATCH_DIR%%/%%HPCPROJ%%/%%HPCUSER%%/%%EXPID%%/LOG_%%EXPID%%/
			#$ -o %%SCRATCH_DIR%%/%%HPCPROJ%%/%%HPCUSER%%/%%EXPID%%/LOG_%%EXPID%%/
			#$ -V
			#$ -l h_rt=%%WALLCLOCK%%:00
			#
			###############################################################################
""")

	HEADER_SIM = textwrap.dedent("""\
			#!/bin/sh
			###############################################################################
			#                   %%TASKTYPE%% %%TEMPLATE_NAME%% EXPERIMENT
			###############################################################################
			#   
			#$ -S /bin/sh
			#$ -N %%JOBNAME%%
			#$ -e %%SCRATCH_DIR%%/%%HPCPROJ%%/%%HPCUSER%%/%%EXPID%%/LOG_%%EXPID%%/
			#$ -o %%SCRATCH_DIR%%/%%HPCPROJ%%/%%HPCUSER%%/%%EXPID%%/LOG_%%EXPID%%/
			#$ -V
			#$ -l h_rt=%%WALLCLOCK%%:00
			#$ -pe orte %%NUMPROC%% 
			#
			###############################################################################
""")

	HEADER_POST = textwrap.dedent("""\
			#!/bin/sh
			###############################################################################
			#                   %%TASKTYPE%% %%TEMPLATE_NAME%% EXPERIMENT
			###############################################################################
			#   
			#$ -S /bin/sh
			#$ -N %%JOBNAME%%
			#$ -e %%SCRATCH_DIR%%/%%HPCPROJ%%/%%HPCUSER%%/%%EXPID%%/LOG_%%EXPID%%/
			#$ -o %%SCRATCH_DIR%%/%%HPCPROJ%%/%%HPCUSER%%/%%EXPID%%/LOG_%%EXPID%%/
			#$ -V
			#$ -l h_rt=%%WALLCLOCK%%:00
			#
			###############################################################################
""")

	HEADER_CLEAN = textwrap.dedent("""\
			#!/bin/sh
			###############################################################################
			#                   %%TASKTYPE%% %%TEMPLATE_NAME%% EXPERIMENT
			###############################################################################
			#   
			#$ -S /bin/sh
			#$ -N %%JOBNAME%%
			#$ -e %%SCRATCH_DIR%%/%%HPCPROJ%%/%%HPCUSER%%/%%EXPID%%/LOG_%%EXPID%%/
			#$ -o %%SCRATCH_DIR%%/%%HPCPROJ%%/%%HPCUSER%%/%%EXPID%%/LOG_%%EXPID%%/
			#$ -V
			#$ -l h_rt=%%WALLCLOCK%%:00
			#
			###############################################################################
""")

class LgHeader:
	"""Class to handle the Lindgren headers of a job"""

	HEADER_WRP = textwrap.dedent("""\
			#!/bin/sh
			###############################################################################
			#                         %%TASKTYPE%% %%TEMPLATE_NAME%% EXPERIMENT
			###############################################################################
			#
			#!/bin/sh --login
			#PBS -N %%JOBNAME%%
			#PBS -l mppwidth=%%NUMPROC%%
			#PBS -l mppnppn=%%NUMTASK%%
			#PBS -l walltime=%%WALLCLOCK%%
			#PBS -e %%SCRATCH_DIR%%/%%HPCPROJ%%/%%HPCUSER%%/%%EXPID%%/LOG_%%EXPID%%
			#PBS -o %%SCRATCH_DIR%%/%%HPCPROJ%%/%%HPCUSER%%/%%EXPID%%/LOG_%%EXPID%%
			#
			###############################################################################
""")

	HEADER_REMOTESETUP = textwrap.dedent("""\
			#!/bin/sh
			###############################################################################
			#                         %%TASKTYPE%% %%TEMPLATE_NAME%% EXPERIMENT
			###############################################################################
			#
			#!/bin/sh --login
			#PBS -N %%JOBNAME%%
			#PBS -l mppwidth=%%NUMPROC%%
			#PBS -l mppnppn=%%NUMTASK%%
			#PBS -l walltime=%%WALLCLOCK%%
			#PBS -e %%SCRATCH_DIR%%/%%HPCPROJ%%/%%HPCUSER%%/%%EXPID%%/LOG_%%EXPID%%
			#PBS -o %%SCRATCH_DIR%%/%%HPCPROJ%%/%%HPCUSER%%/%%EXPID%%/LOG_%%EXPID%%
			#
			###############################################################################
""")

	HEADER_INI = textwrap.dedent("""\
			#!/bin/sh
			###############################################################################
			#                         %%TASKTYPE%% %%TEMPLATE_NAME%% EXPERIMENT
			###############################################################################
			#
			#!/bin/sh --login
			#PBS -N %%JOBNAME%%
			#PBS -l mppwidth=%%NUMPROC%%
			#PBS -l mppnppn=%%NUMTASK%%
			#PBS -l walltime=%%WALLCLOCK%%
			#PBS -e %%SCRATCH_DIR%%/%%HPCPROJ%%/%%HPCUSER%%/%%EXPID%%/LOG_%%EXPID%%
			#PBS -o %%SCRATCH_DIR%%/%%HPCPROJ%%/%%HPCUSER%%/%%EXPID%%/LOG_%%EXPID%%
			#
			###############################################################################
""")

	HEADER_SIM = textwrap.dedent("""\
			#!/bin/sh
			###############################################################################
			#                         %%TASKTYPE%% %%TEMPLATE_NAME%% EXPERIMENT
			###############################################################################
			#
			#!/bin/sh --login
			#PBS -N %%JOBNAME%%
			#PBS -l mppwidth=%%NUMPROC%%
			#PBS -l mppnppn=%%NUMTASK%%
			#PBS -l walltime=%%WALLCLOCK%%
			#PBS -e %%SCRATCH_DIR%%/%%HPCPROJ%%/%%HPCUSER%%/%%EXPID%%/LOG_%%EXPID%%
			#PBS -o %%SCRATCH_DIR%%/%%HPCPROJ%%/%%HPCUSER%%/%%EXPID%%/LOG_%%EXPID%%
			#
			###############################################################################
""")

	HEADER_POST = textwrap.dedent("""\
			#!/bin/sh
			###############################################################################
			#                         %%TASKTYPE%% %%TEMPLATE_NAME%% EXPERIMENT
			###############################################################################
			#
			#!/bin/sh --login
			#PBS -N %%JOBNAME%%
			#PBS -l mppwidth=%%NUMPROC%%
			#PBS -l mppnppn=%%NUMTASK%%
			#PBS -l walltime=%%WALLCLOCK%%
			#PBS -e %%SCRATCH_DIR%%/%%HPCPROJ%%/%%HPCUSER%%/%%EXPID%%/LOG_%%EXPID%%
			#PBS -o %%SCRATCH_DIR%%/%%HPCPROJ%%/%%HPCUSER%%/%%EXPID%%/LOG_%%EXPID%%
			#
			###############################################################################
""")

	HEADER_CLEAN = textwrap.dedent("""\
			#!/bin/sh
			###############################################################################
			#                         %%TASKTYPE%% %%TEMPLATE_NAME%% EXPERIMENT
			###############################################################################
			#
			#!/bin/sh --login
			#PBS -N %%JOBNAME%%
			#PBS -l mppwidth=%%NUMPROC%%
			#PBS -l mppnppn=%%NUMTASK%%
			#PBS -l walltime=%%WALLCLOCK%%
			#PBS -e %%SCRATCH_DIR%%/%%HPCPROJ%%/%%HPCUSER%%/%%EXPID%%/LOG_%%EXPID%%
			#PBS -o %%SCRATCH_DIR%%/%%HPCPROJ%%/%%HPCUSER%%/%%EXPID%%/LOG_%%EXPID%%
			#
			###############################################################################
""")

class MnHeader:
	"""Class to handle the MareNostrum 3 headers of a job"""

	HEADER_WRP = textwrap.dedent("""\
			#!/bin/sh
			###############################################################################
			#                              %%TASKTYPE%%
			###############################################################################
			#
			#BSUB -J %%JOBNAME%%
			#BSUB -oo %%SCRATCH_DIR%%/%%HPCPROJ%%/%%HPCUSER%%/%%EXPID%%/LOG_%%EXPID%%/%%JOBNAME%%_%%J.out 
			#BSUB -eo %%SCRATCH_DIR%%/%%HPCPROJ%%/%%HPCUSER%%/%%EXPID%%/LOG_%%EXPID%%/%%JOBNAME%%_%%J.err
			#BSUB -W %%WALLCLOCK%%
			#BSUB -n %%NUMPROC%%
			#BSUB -R "span[ptile=16]"
			#
	 		###############################################################################""")

	HEADER_REMOTESETUP = textwrap.dedent("""\
			#!/bin/sh
			###############################################################################
			#                   %%TASKTYPE%% %%TEMPLATE_NAME%% EXPERIMENT
			###############################################################################
			#
			#BSUB -J %%JOBNAME%%
			#BSUB -oo %%SCRATCH_DIR%%/%%HPCPROJ%%/%%HPCUSER%%/%%EXPID%%/LOG_%%EXPID%%/%%JOBNAME%%_%%J.out 
			#BSUB -eo %%SCRATCH_DIR%%/%%HPCPROJ%%/%%HPCUSER%%/%%EXPID%%/LOG_%%EXPID%%/%%JOBNAME%%_%%J.err
			#BSUB -W %%WALLCLOCK%%
			#BSUB -n %%NUMPROC%%
			#BSUB -R "span[ptile=16]"
			#
	 		###############################################################################""")

	HEADER_INI = textwrap.dedent("""\
			#!/bin/sh
			###############################################################################
			#                   %%TASKTYPE%% %%TEMPLATE_NAME%% EXPERIMENT
			###############################################################################
			#
			#BSUB -J %%JOBNAME%%
			#BSUB -oo %%SCRATCH_DIR%%/%%HPCPROJ%%/%%HPCUSER%%/%%EXPID%%/LOG_%%EXPID%%/%%JOBNAME%%_%%J.out 
			#BSUB -eo %%SCRATCH_DIR%%/%%HPCPROJ%%/%%HPCUSER%%/%%EXPID%%/LOG_%%EXPID%%/%%JOBNAME%%_%%J.err
			#BSUB -W %%WALLCLOCK%%
			#BSUB -n %%NUMPROC%%
			#BSUB -R "span[ptile=16]"
			#
	 		###############################################################################""")

	HEADER_SIM = textwrap.dedent("""\
			#!/bin/sh
			###############################################################################
			#                   %%TASKTYPE%% %%TEMPLATE_NAME%% EXPERIMENT
			###############################################################################
			#
			#BSUB -J %%JOBNAME%%
			#BSUB -oo %%SCRATCH_DIR%%/%%HPCPROJ%%/%%HPCUSER%%/%%EXPID%%/LOG_%%EXPID%%/%%JOBNAME%%_%%J.out 
			#BSUB -eo %%SCRATCH_DIR%%/%%HPCPROJ%%/%%HPCUSER%%/%%EXPID%%/LOG_%%EXPID%%/%%JOBNAME%%_%%J.err
			#BSUB -W %%WALLCLOCK%%
			#BSUB -n %%NUMPROC%%
			#BSUB -R "span[ptile=16]"
			#
	 		###############################################################################""")

	HEADER_POST = textwrap.dedent("""\
			#!/bin/sh
			###############################################################################
			#                   %%TASKTYPE%% %%TEMPLATE_NAME%% EXPERIMENT
			###############################################################################
			#
			#BSUB -J %%JOBNAME%%
			#BSUB -oo %%SCRATCH_DIR%%/%%HPCPROJ%%/%%HPCUSER%%/%%EXPID%%/LOG_%%EXPID%%/%%JOBNAME%%_%%J.out 
			#BSUB -eo %%SCRATCH_DIR%%/%%HPCPROJ%%/%%HPCUSER%%/%%EXPID%%/LOG_%%EXPID%%/%%JOBNAME%%_%%J.err
			#BSUB -W %%WALLCLOCK%%
			#BSUB -n %%NUMPROC%%
			#BSUB -R "span[ptile=16]"
			#BSUB -x
			#
	 		###############################################################################""")

	HEADER_CLEAN = textwrap.dedent("""\
			#!/bin/sh
			###############################################################################
			#                   %%TASKTYPE%% %%TEMPLATE_NAME%% EXPERIMENT
			###############################################################################
			#
			#BSUB -J %%JOBNAME%%
			#BSUB -oo %%SCRATCH_DIR%%/%%HPCPROJ%%/%%HPCUSER%%/%%EXPID%%/LOG_%%EXPID%%/%%JOBNAME%%_%%J.out 
			#BSUB -eo %%SCRATCH_DIR%%/%%HPCPROJ%%/%%HPCUSER%%/%%EXPID%%/LOG_%%EXPID%%/%%JOBNAME%%_%%J.err
			#BSUB -W %%WALLCLOCK%%
			#BSUB -n %%NUMPROC%%
			#BSUB -R "span[ptile=16]"
			#
	 		###############################################################################""")
