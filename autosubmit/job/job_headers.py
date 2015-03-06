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


class PsHeader:
    """Class to handle the Ps headers of a job"""

    SERIAL = textwrap.dedent("""
            #!/bin/bash
            ###############################################################################
            #                   %TASKTYPE% %EXPID% EXPERIMENT
            ###############################################################################
            """)

    PARALLEL = textwrap.dedent("""
            #!/bin/bash
            ###############################################################################
            #                   %TASKTYPE% %EXPID% EXPERIMENT
            ###############################################################################
            """)


class ArHeader:
    """Class to handle the Archer headers of a job"""

    SERIAL = textwrap.dedent("""
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

    PARALLEL = textwrap.dedent("""
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


class BscHeader:
    """Class to handle the BSC headers of a job"""

    SERIAL = textwrap.dedent("""
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

    PARALLEL = textwrap.dedent("""
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
            #@ tasks_per_node   = %TASKSNODE%
            #@ tracing          = %TRACING%
            #
            ###############################################################################
            """)

   
class EcHeader:
    """Class to handle the ECMWF headers of a job"""

    SERIAL = textwrap.dedent("""
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

    PARALLEL = textwrap.dedent("""\
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


class EcCcaHeader:
    """Class to handle the ECMWF headers of a job"""

    SERIAL = textwrap.dedent("""
             #!/bin/bash
             ###############################################################################
             #                   %TASKTYPE% %EXPID% EXPERIMENT
             ###############################################################################
             #
             #PBS -N %JOBNAME%
             #PBS -q ns
             #PBS -l walltime=%WALLCLOCK_SETUP%:00
             #PBS -l EC_billing_account=%HPCPROJ%
             #
             ###############################################################################

            """)

    PARALLEL = textwrap.dedent("""\
             #!/bin/bash
             ###############################################################################
             #                   %TASKTYPE% %EXPID% EXPERIMENT
             ###############################################################################
             #
             #PBS -N %JOBNAME%
             #PBS -q np
             #PBS -l EC_total_tasks=%NUMPROC_SIM%
             #PBS -l EC_threads_per_task=%NUMTHREAD_SIM%
             #PBS -l EC_tasks_per_node=%NUMTASK_SIM%
             #PBS -l walltime=%WALLCLOCK_SIM%:00
             #PBS -l EC_billing_account=%HPCPROJ%
             #
             ###############################################################################
            """)


class HtHeader:
    """Class to handle the Hector headers of a job"""

    SERIAL = textwrap.dedent("""
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

    PARALLEL = textwrap.dedent("""
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


class ItHeader:
    """Class to handle the Ithaca headers of a job"""

    SERIAL = textwrap.dedent("""
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

    PARALLEL = textwrap.dedent("""
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


class LgHeader:
    """Class to handle the Lindgren headers of a job"""

    SERIAL = textwrap.dedent("""\
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

    PARALLEL = textwrap.dedent("""\
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

    SERIAL = textwrap.dedent("""\
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

    PARALLEL = textwrap.dedent("""\
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
