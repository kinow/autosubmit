#!/usr/bin/env python

# Copyright 2017 Earth Sciences Department, BSC-CNS

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


# TODO: Refactor with kwargs
# TODO: Project is not EC_billing_account, use budget
class EcWrapper(object):
    """Class to handle wrappers on ECMWF platform"""

    @classmethod
    def vertical(cls, filename, queue, project, wallclock, num_procs, job_scripts, dependency, **kwargs):
        return textwrap.dedent("""\
            #!/bin/bash
            ###############################################################################
            #              {0}
            ###############################################################################
            #
            #PBS -N {0}
            #PBS -q {1}
            #PBS -l EC_billing_account={2}
            #PBS -o {8}/LOG_{6}/{0}.out
            #PBS -e {8}/LOG_{6}/{0}.err
            #PBS -l walltime={3}:00
            #PBS -l EC_total_tasks={4}
            #PBS -l EC_hyperthreads=1
            {7}
            {9}
            #
            ###############################################################################

            # Function to execute each thread
            execute_script()
            {{
                out="$1.$2.out"
                err="$1.$2.err"
                bash $1 > $out 2> $err &
                pid=$!
            }}

            # Initializing variables
            scripts="{5}"
            i=0
            pids=""

            # Initializing the scripts
            for script in $scripts; do
                execute_script "$SCRATCH/{6}/LOG_{6}/$script" $i
                wait $pid
                if [ $? -eq 0 ]; then
                    echo "The job $script has been COMPLETED"
                else
                    echo "The job $script has FAILED"
                    exit 1
                fi
                i=$((i+1))
            done
            """.format(filename, queue, project, wallclock, num_procs,
                       ' '.join(str(s) for s in job_scripts), kwargs['expid'],
                       cls.dependency_directive(dependency), kwargs['rootdir'],
                       '\n'.ljust(13).join(str(s) for s in kwargs['directives'])))

    @classmethod
    def horizontal(cls, filename, queue, project, wallclock, num_procs, _, job_scripts, dependency, **kwargs):
        return textwrap.dedent("""\
            #!/bin/bash
            ###############################################################################
            #              {0}
            ###############################################################################
            #
            #PBS -N {0}
            #PBS -q {1}
            #PBS -l EC_billing_account={2}
            #PBS -o {8}/LOG_{6}/{0}.out
            #PBS -e {8}/LOG_{6}/{0}.err
            #PBS -l walltime={3}:00
            #PBS -l EC_total_tasks={4}
            #PBS -l EC_hyperthreads=1
            {7}
            {9}
            #
            ###############################################################################

            # Function to execute each thread
            execute_script()
            {{
                out="$1.$2.out"
                err="$1.$2.err"
                bash $1 > $out 2> $err &
                pid=$!
            }}

            # Initializing variables
            scripts="{5}"
            i=0
            pids=""

            # Initializing the scripts
            for script in $scripts; do
                execute_script "$SCRATCH/{6}/LOG_{6}/$script" $i
                pids+="$pid "
                i=$((i+1))
            done

            # Waiting until all scripts finish
            for pid in $pids; do
                wait $pid
                if [ $? -eq 0 ]; then
                    echo "The job $pid has been COMPLETED"
                else
                    echo "The job $pid has FAILED"
                fi
            done
            """.format(filename, queue, project, wallclock, num_procs,
                       ' '.join(str(s) for s in job_scripts), kwargs['expid'],
                       cls.dependency_directive(dependency), kwargs['rootdir'],
                       '\n'.ljust(13).join(str(s) for s in kwargs['directives'])))

    @classmethod
    def dependency_directive(cls, dependency):
        return '#' if dependency is None else '#PBS -v depend=afterok:{0}'.format(dependency)
