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
class LsfWrapper(object):
    """Class to handle wrappers on LSF platforms"""

    @classmethod
    def array(cls, filename, array_id, wallclock, num_procs, **kwargs):
        return textwrap.dedent("""\
            ###############################################################################
            #              {0}
            ###############################################################################
            #
            #
            #BSUB -J {0}{1}
            #BSUB -oo {0}.%I.out
            #BSUB -eo {0}.%I.err
            #BSUB -W {2}
            #BSUB -n {3}
            {4}
            #
            ###############################################################################

            SCRIPT=$(cat {0}.$LSB_JOBINDEX | awk 'NR==1')
            chmod +x $SCRIPT
            ./$SCRIPT
            """.format(filename, array_id, wallclock, num_procs,
                       '\n'.ljust(13).join(str(s) for s in kwargs['directives'])))

    @classmethod
    def vertical(cls, filename, queue, project, wallclock, num_procs, job_scripts, dependency, **kwargs):
        return textwrap.dedent("""\
            #!/usr/bin/env python
            ###############################################################################
            #              {0}
            ###############################################################################
            #
            #BSUB -J {0}
            #BSUB -q {1}
            #BSUB -P {2}
            #BSUB -oo {0}.out
            #BSUB -eo {0}.err
            #BSUB -W {3}
            #BSUB -n {4}
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
                    command = str(self.template) + ' ' + str(self.id_run) + ' ' + os.getcwd()
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
            """.format(filename, queue, project, wallclock, num_procs, str(job_scripts),
                       cls.dependency_directive(dependency),
                       '\n'.ljust(13).join(str(s) for s in kwargs['directives'])))

    @classmethod
    def horizontal(cls, filename, queue, project, wallclock, num_procs, num_jobs, job_scripts, dependency, **kwargs):
        return textwrap.dedent("""\
            #!/usr/bin/env python
            ###############################################################################
            #              {0}
            ###############################################################################
            #
            #BSUB -J {0}
            #BSUB -q {1}
            #BSUB -P {2}
            #BSUB -oo {0}.out
            #BSUB -eo {0}.err
            #BSUB -W {3}
            #BSUB -n {4}
            {7}
            {10}
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
                    command = str(self.template) + " " + str(self.id_run) + " " + os.getcwd()
                    (self.status) = getstatusoutput(command + " > " + out + " 2> " + err)

            # Splitting the original hosts file
            os.system("cat {8} | split -a 2 -d -l {5} - mlist-{9}-")

            # Defining scripts to be run
            scripts = {6}

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
            """.format(filename, queue, project, wallclock, num_procs, (int(num_procs) / num_jobs),
                       str(job_scripts), cls.dependency_directive(dependency), "${LSB_DJOB_HOSTFILE}",
                       "${LSB_JOBID}", '\n'.ljust(13).join(str(s) for s in kwargs['directives'])))

    @classmethod
    def dependency_directive(cls, dependency):
        return '#' if dependency is None else '#BSUB -w \'done("{0}")\' [-ti]'.format(dependency)
