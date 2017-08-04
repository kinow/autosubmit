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
class SlurmWrapper(object):
    """Class to handle wrappers on SLURM platforms"""

    @classmethod
    def vertical(cls, filename, queue, project, wallclock, num_procs, job_scripts, dependency, **kwargs):
        return textwrap.dedent("""\
            #!/usr/bin/env python
            ###############################################################################
            #              {0}
            ###############################################################################
            #
            #SBATCH -J {0}
            {1}
            #SBATCH -A {2}
            #SBATCH -o {0}.out
            #SBATCH -e {0}.err
            #SBATCH -t {3}:00
            #SBATCH -n {4}
            {6}
            {7}
            #
            ###############################################################################

            import os
            import sys
            from threading import Thread
            from commands import getstatusoutput

            class JobThread(Thread):
                def __init__ (self, template, id_run):
                    Thread.__init__(self)
                    self.template = template
                    self.id_run = id_run

                def run(self):
                    out = str(self.template) + '.' + str(self.id_run) + '.out'
                    err = str(self.template) + '.' + str(self.id_run) + '.err'
                    command = "bash " + str(self.template) + ' ' + str(self.id_run) + ' ' + os.getcwd()
                    (self.status) = getstatusoutput(command + ' > ' + out + ' 2> ' + err)

            scripts = {5}

            for i in range(len(scripts)):
                current = JobThread(scripts[i], i)
                current.start()
                current.join()
                completed_filename = scripts[i].replace('.cmd', '_COMPLETED')
                completed_path = os.path.join(os.getcwd(), completed_filename)
                if os.path.exists(completed_path):
                    print "The job ", current.template," has been COMPLETED"
                else:
                    print "The job ", current.template," has FAILED"
                    os._exit(1)
            """.format(filename, cls.queue_directive(queue), project, wallclock, num_procs, str(job_scripts),
                       cls.dependency_directive(dependency),
                       '\n'.ljust(13).join(str(s) for s in kwargs['directives'])))

    @classmethod
    def horizontal(cls, filename, queue, project, wallclock, num_procs, _, job_scripts, dependency, **kwargs):
        return textwrap.dedent("""\
            #!/usr/bin/env python
            ###############################################################################
            #              {0}
            ###############################################################################
            #
            #SBATCH -J {0}
            {1}
            #SBATCH -A {2}
            #SBATCH -o {0}.out
            #SBATCH -e {0}.err
            #SBATCH -t {3}:00
            #SBATCH -n {4}
            {6}
            {7}
            #
            ###############################################################################

            import os
            import sys
            from threading import Thread
            from commands import getstatusoutput

            class JobThread(Thread):
                def __init__ (self, template, id_run):
                    Thread.__init__(self)
                    self.template = template
                    self.id_run = id_run

                def run(self):
                    out = str(self.template) + "." + str(self.id_run) + ".out"
                    err = str(self.template) + "." + str(self.id_run) + ".err"
                    command = "bash " + str(self.template) + " " + str(self.id_run) + " " + os.getcwd()
                    (self.status) = getstatusoutput(command + " > " + out + " 2> " + err)

            # Defining scripts to be run
            scripts = {5}

            # Initializing PIDs container
            pid_list = []

            # Initializing the scripts
            for i in range(len(scripts)):
                current = JobThread(scripts[i], i)
                pid_list.append(current)
                current.start()

            # Waiting until all scripts finish
            for pid in pid_list:
                pid.join()
                completed_filename = scripts[i].replace('.cmd', '_COMPLETED')
                completed_path = os.path.join(os.getcwd(), completed_filename)
                if os.path.exists(completed_path):
                    print "The job ", pid.template," has been COMPLETED"
                else:
                    print "The job ", pid.template," has FAILED"
            """.format(filename, cls.queue_directive(queue), project, wallclock, num_procs, str(job_scripts),
                       cls.dependency_directive(dependency),
                       '\n'.ljust(13).join(str(s) for s in kwargs['directives'])))

    @classmethod
    def dependency_directive(cls, dependency):
        return '#' if dependency is None else '#SBATCH --dependency=afterok:{0}'.format(dependency)

    @classmethod
    def queue_directive(cls, queue):
        return '#' if queue == '' else '#SBATCH --qos={0}'.format(queue)