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
            from datetime import datetime

            class JobThread(Thread):
                def __init__ (self, template, id_run):
                    Thread.__init__(self)
                    self.template = template
                    self.id_run = id_run

                def run(self):
                    jobname = self.template.replace('.cmd', '')
                    os.system("echo $(date +%s) > "+jobname+"_STAT")
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
                    print datetime.now(), "The job ", current.template," has been COMPLETED"
                else:
                    print datetime.now(), "The job ", current.template," has FAILED"
                    #os._exit(1)
                    sys.exit()
            """.format(filename, cls.queue_directive(queue), project, wallclock, num_procs, str(job_scripts),
                       cls.dependency_directive(dependency),
                       '\n'.ljust(13).join(str(s) for s in kwargs['directives'])))

    @classmethod
    def horizontal(cls, filename, queue, project, wallclock, num_procs, _, job_scripts, dependency, **kwargs):
        wrapper_script = textwrap.dedent("""\
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
            from datetime import datetime

            class JobThread(Thread):
                def __init__ (self, template, id_run):
                    Thread.__init__(self)
                    self.template = template
                    self.id_run = id_run

                def run(self):
                    jobname = self.template.replace('.cmd', '')
                    os.system("echo $(date +%s) > "+jobname+"_STAT")
                    out = str(self.template) + "." + str(self.id_run) + ".out"
                    err = str(self.template) + "." + str(self.id_run) + ".err"
                    command = "bash " + str(self.template) + " " + str(self.id_run) + " " + os.getcwd()
                    (self.status) = getstatusoutput(command + " > " + out + " 2> " + err)
            
            # Getting the list of allocated nodes
            os.system("scontrol show hostnames $SLURM_JOB_NODELIST > node_list")
            os.system("mkdir -p machinefiles")
            
            # Defining scripts to be run
            scripts = {5}

            # Initializing PIDs container
            pid_list = []
            
            with open('node_list', 'r') as file:
                 all_nodes = file.read()
            
            all_nodes = all_nodes.split("_NEWLINE_")
            all_cores = []
            for node in all_nodes:
               for n in range(48):
                  all_cores.append(node)

            # Initializing the scripts
            for i in range(len(scripts)):
                job = scripts[i]
                total_cores = ({4} / len(scripts))
                machines = str()
                for idx in range(total_cores):
                        node = all_cores.pop(0)
                        if node:
                                machines += node +"_NEWLINE_"
    
                machines = "_NEWLINE_".join([s for s in machines.split("_NEWLINE_") if s])
                with open("machinefiles/machinefile_"+job.replace(".cmd", ''), "w") as machinefile:
                    machinefile.write(machines)

                current = JobThread(scripts[i], i)
                pid_list.append(current)
                current.start()

            # Waiting until all scripts finish
            for pid in pid_list:
                pid.join()
                completed_filename = scripts[i].replace('.cmd', '_COMPLETED')
                completed_path = os.path.join(os.getcwd(), completed_filename)
                if os.path.exists(completed_path):
                    print datetime.now(), "The job ", pid.template," has been COMPLETED"
                else:
                    print datetime.now(), "The job ", pid.template," has FAILED"
            """.format(filename, cls.queue_directive(queue), project, wallclock, num_procs, str(job_scripts),
                       cls.dependency_directive(dependency),
                       '\n'.ljust(13).join(str(s) for s in kwargs['directives'])))

        wrapper_script = wrapper_script.replace("_NEWLINE_", '\\n')
        return wrapper_script

    @classmethod
    def hybrid(cls, filename, queue, project, wallclock, num_procs, job_scripts, dependency, jobs_resources=dict(),  **kwargs):
        wrapper_script = textwrap.dedent("""\
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
            {8}
            #
            ###############################################################################

            import os
            import sys
            from threading import Thread
            from commands import getstatusoutput
            from datetime import datetime
            
            class JobThread(Thread):
                def __init__ (self, template, id_run):
                    Thread.__init__(self)
                    self.template = template
                    self.id_run = id_run
                
                def run(self):
                    jobname = self.template.replace('.cmd', '')
                    os.system("echo $(date +%s) > "+jobname+"_STAT")
                    out = str(self.template) + "." + str(self.id_run) + ".out"
                    err = str(self.template) + "." + str(self.id_run) + ".err"
                    command = "bash " + str(self.template) + " " + str(self.id_run) + " " + os.getcwd()
                    (self.status) = getstatusoutput(command + " > " + out + " 2> " + err)

            class JobListThread(Thread):
                def __init__ (self, jobs_list, id_run):
                    Thread.__init__(self)
                    self.jobs_list = jobs_list
                    self.id_run = id_run

                def run(self):
                    for i in range(len(self.jobs_list)):
                        job = self.jobs_list[i]
                        current = JobThread(job, self.id_run)
                        current.start()
                        current.join()
                        completed_filename = job.replace('.cmd', '_COMPLETED')
                        completed_path = os.path.join(os.getcwd(), completed_filename)
                        if os.path.exists(completed_path):
                            print datetime.now(), "The job ", job," has been COMPLETED"
                        else:
                            print datetime.now(), "The job ", job," has FAILED"
                            #os._exit(1)
                            sys.exit()
            
            # Getting the list of allocated nodes
            os.system("scontrol show hostnames $SLURM_JOB_NODELIST > node_list")
            os.system("mkdir -p machinefiles")
                                             
            # Defining scripts to be run
            scripts = {5}
            
            jobs_resources = {7}
            
            with open('node_list', 'r') as file:
                all_nodes = file.read()
        
            all_nodes = all_nodes.split('_NEWLINE_')
            total_cores = int({4})
            
            all_cores = []
            idx = 0
            while total_cores > 0:
                if processors_per_node > 0:
                    processors_per_node -= 1
                    total_cores -= 1
                    all_cores.append(all_nodes[idx])
                else:
                    idx += 1
                    processors_per_node = int(jobs_resources['PROCESSORS_PER_NODE'])
            
            processors_per_node = int(jobs_resources['PROCESSORS_PER_NODE'])

            # Initializing PIDs container
            pid_list = []

            # Initializing the scripts
            id = 0
            for job_list in scripts:
                member = job_list[0].split('_')[2]
                total_cores = ({4} / len(scripts))
                machines = str()
                   
                for idx in range(total_cores):
                    node = all_cores.pop(0)
                    if node:
                            machines += node +"_NEWLINE_"

                machines = "_NEWLINE_".join([s for s in machines.split("_NEWLINE_") if s])
                with open("machinefiles/machinefile_"+member, "w") as machinefile:
                    machinefile.write(machines)
                        
                current = JobListThread(job_list, id)
                pid_list.append(current)
                current.start()
                id += 1

            # Waiting until all scripts finish
            for i in range(len(pid_list)):
                pid = pid_list[i]
                pid.join()
                                        
            """.format(filename, cls.queue_directive(queue), project, wallclock, num_procs, str(job_scripts),
                           cls.dependency_directive(dependency), str(jobs_resources),
                           '\n'.ljust(13).join(str(s) for s in kwargs['directives'])))
        wrapper_script = wrapper_script.replace("_NEWLINE_", '\\n')
        return wrapper_script

    @classmethod
    def hybrid_crossdate(cls, filename, queue, project, wallclock, num_procs, job_scripts, dependency, jobs_resources=dict(), **kwargs):
        wrapper_script = textwrap.dedent("""\
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
                {8}
                #
                ###############################################################################

                import os
                import sys
                from threading import Thread
                from commands import getstatusoutput
                from datetime import datetime
                from math import ceil

                class JobThread(Thread):
                    def __init__ (self, template, id_run):
                        Thread.__init__(self)
                        self.template = template
                        self.id_run = id_run

                    def run(self):
                        jobname = self.template.replace('.cmd', '')
                        os.system("echo $(date +%s) > "+jobname+"_STAT")
                        out = str(self.template) + "." + str(self.id_run) + ".out"
                        err = str(self.template) + "." + str(self.id_run) + ".err"
                        command = "bash " + str(self.template) + " " + str(self.id_run) + " " + os.getcwd()
                        (self.status) = getstatusoutput(command + " > " + out + " 2> " + err)

                class JobListThread(Thread):
                    def __init__ (self, jobs_list, id_run, nodes):
                        Thread.__init__(self)
                        self.jobs_list = jobs_list
                        self.id_run = id_run
                        self.nodes = nodes

                    def run(self):
                        pid_list = []
                        all_cores = []
                        
                        jobs_resources = {7}
                        processors_per_node = int(jobs_resources['PROCESSORS_PER_NODE'])
                        total_cores = int({4})
                        
                        idx = 0
                        while total_cores > 0:
                            if processors_per_node > 0:
                                processors_per_node -= 1
                                total_cores -= 1
                                all_cores.append(self.nodes[idx])
                            else:
                                idx += 1
                                processors_per_node = int(jobs_resources['PROCESSORS_PER_NODE'])
                        
                        processors_per_node = int(jobs_resources['PROCESSORS_PER_NODE'])
                        
                        for i in range(len(self.jobs_list)):
                            job = self.jobs_list[i]
                            jobname = job.split('_')[-1]
                            section = jobname.replace('.cmd', '')
                            
                            machines = str()
                            
                            cores = int(jobs_resources[section]['PROCESSORS'])
                            tasks = int(jobs_resources[section]['TASKS'])
                            nodes = int(ceil(int(cores)/float(tasks)))
                            
                            while nodes > 0:
                                while cores > 0:
                                    node = all_cores.pop(0)
                                    if node:
                                        machines += node +"_NEWLINE_"
                                        cores -= 1
                                for rest in range(processors_per_node-tasks):
                                    all_cores.pop(0)
                                nodes -= 1
                                                    
                            machines = "_NEWLINE_".join([s for s in machines.split("_NEWLINE_") if s])
                            with open("machinefiles/machinefile_"+job.replace(".cmd", ''), "w") as machinefile:
                                machinefile.write(machines)
                            
                            current = JobThread(job, i)
                            pid_list.append(current)
                            current.start()
                                
                        for i in range(len(pid_list)):
                            pid = pid_list[i]
                            pid.join()
                            job = self.jobs_list[i]
                            print job
                            completed_filename = job.replace('.cmd', '_COMPLETED')
                            completed_path = os.path.join(os.getcwd(), completed_filename)
                            if os.path.exists(completed_path):
                                print datetime.now(), "The job ", job," has been COMPLETED"
                            else:
                                print datetime.now(), "The job ", job," has FAILED"
                                sys.exit()

                # Getting the list of allocated nodes
                os.system("scontrol show hostnames $SLURM_JOB_NODELIST > node_list")
                os.system("mkdir -p machinefiles")

                # Defining scripts to be run
                scripts = {5}

                with open('node_list', 'r') as file:
                    all_nodes = file.read()

                all_nodes = all_nodes.split('_NEWLINE_')
                
                for index, job_list in enumerate(scripts):
                    current = JobListThread(job_list, index, all_nodes)
                    current.start()
                    current.join()
                    print datetime.now(), "List ", str(index+1)," has finished"

                """.format(filename, cls.queue_directive(queue), project, wallclock, num_procs, str(job_scripts),
                           cls.dependency_directive(dependency), str(jobs_resources),
                           '\n'.ljust(13).join(str(s) for s in kwargs['directives'])))
        wrapper_script = wrapper_script.replace("_NEWLINE_", '\\n')
        return wrapper_script

    @classmethod
    def dependency_directive(cls, dependency):
        return '#' if dependency is None else '#SBATCH --dependency=afterok:{0}'.format(dependency)

    @classmethod
    def queue_directive(cls, queue):
        return '#' if queue == '' else '#SBATCH --qos={0}'.format(queue)