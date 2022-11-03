#!/usr/bin/env python3

# Copyright 2017-2020 Earth Sciences Department, BSC-CNS

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

import networkx
import os

from networkx.algorithms.dag import is_directed_acyclic_graph
from networkx import DiGraph
from networkx import dfs_edges
from networkx import NetworkXError
from autosubmit.job.job_package_persistence import JobPackagePersistence
from autosubmitconfigparser.config.basicconfig import BasicConfig
from typing import Dict


def transitive_reduction(graph):
    try:
        return networkx.algorithms.dag.transitive_reduction(graph)
    except Exception as exp:
        if not is_directed_acyclic_graph(graph):
            raise NetworkXError(
                "Transitive reduction only uniquely defined on directed acyclic graphs.")
        reduced_graph = DiGraph()
        reduced_graph.add_nodes_from(graph.nodes())
        for u in graph:
            u_edges = set(graph[u])
            for v in graph[u]:
                u_edges -= {y for x, y in dfs_edges(graph, v)}
            reduced_graph.add_edges_from((u, v) for v in u_edges)
        return reduced_graph

def get_job_package_code(expid, job_name):
    # type: (str, str) -> int
    """
    Finds the package code and retrieves it. None if no package.

    :param job_name:
    :param expid: Experiment ID
    :type expid: String

    :return: package code, None if not found
    :rtype: int or None
    """
    try:
        basic_conf = BasicConfig()
        basic_conf.read()
        packages_wrapper = JobPackagePersistence(os.path.join(basic_conf.LOCAL_ROOT_DIR, expid, "pkl"),"job_packages_" + expid).load(wrapper=True)
        packages_wrapper_plus = JobPackagePersistence(os.path.join(basic_conf.LOCAL_ROOT_DIR, expid, "pkl"),"job_packages_" + expid).load(wrapper=False)
        if packages_wrapper or packages_wrapper_plus:
            packages = packages_wrapper if len(packages_wrapper) > len(packages_wrapper_plus) else packages_wrapper_plus
            for exp, package_name, _job_name in packages:
                if job_name == _job_name:
                    code = int(package_name.split("_")[2])
                    return code            
    except Exception as e:
        pass
    return 0


class Dependency(object):
    """
    Class to manage the metadata related with a dependency

    """

    def __init__(self, section, distance=None, running=None, sign=None, delay=-1, splits=None,relationships=None):
        self.section = section
        self.distance = distance
        self.running = running
        self.sign = sign
        self.delay = delay
        self.splits = splits
        self.relationships = relationships


class SimpleJob(object):
    """
    A simple replacement for jobs
    """

    def __init__(self, name, tmppath, statuscode):
        self.name = name
        self._tmp_path = tmppath
        self.status = statuscode


class SubJob(object):
    """
    Class to manage package times
    """

    def __init__(self, name, package=None, queue=0, run=0, total=0, status="UNKNOWN"):
        self.name = name
        self.package = package
        self.queue = queue
        self.run = run
        self.total = total
        self.status = status
        self.transit = 0
        self.parents = list()
        self.children = list()


class SubJobManager(object):
    """
    Class to manage list of SubJobs
    """

    def __init__(self, subjoblist, job_to_package=None, package_to_jobs=None, current_structure=None):
        self.subjobList = subjoblist
        # print("Number of jobs in SubManager : {}".format(len(self.subjobList)))
        self.job_to_package = job_to_package
        self.package_to_jobs = package_to_jobs
        self.current_structure = current_structure
        self.subjobindex = dict()
        self.subjobfixes = dict()
        self.process_index()
        self.process_times()

    def process_index(self):
        """
        Builds a dictionary of jobname -> SubJob object. 
        """
        for subjob in self.subjobList:
            self.subjobindex[subjob.name] = subjob

    def process_times(self):
        """
        """
        if self.job_to_package and self.package_to_jobs:
            if self.current_structure and len(list(self.current_structure.keys())) > 0:
                # Structure exists
                new_queues = dict()
                fixes_applied = dict()
                for package in self.package_to_jobs:
                    # SubJobs in Package
                    local_structure = dict()
                    # SubJob Name -> SubJob Object
                    local_index = dict()
                    subjobs_in_package = [x for x in self.subjobList if x.package ==
                                                package]
                    local_jobs_in_package = [job for job in subjobs_in_package]
                    # Build index
                    for sub in local_jobs_in_package:
                        local_index[sub.name] = sub
                    # Build structure
                    for sub_job in local_jobs_in_package:
                        # If job in current_structure, store children names in dictionary
                        # local_structure: Job Name -> Children (if present in the Job package)
                        local_structure[sub_job.name] = [v for v in self.current_structure[sub_job.name]
                                                         if v in self.package_to_jobs[package]] if sub_job.name in self.current_structure else list()
                        # Assign children to SubJob in local_jobs_in_package
                        sub_job.children = local_structure[sub_job.name]
                        # Assign sub_job Name as a parent of each of its children
                        for child in local_structure[sub_job.name]:
                            local_index[child].parents.append(sub_job.name)

                    # Identify root as the job with no parents in the package
                    roots = [sub for sub in local_jobs_in_package if len(
                        sub.parents) == 0]

                    # While roots exists (consider pop)
                    while len(roots) > 0:
                        sub = roots.pop(0)
                        if len(sub.children) > 0:
                            for sub_children_name in sub.children:
                                if sub_children_name not in new_queues:
                                    # Add children to root to continue the sequence of fixes
                                    roots.append(
                                        local_index[sub_children_name])
                                    fix_size = max(self.subjobindex[sub.name].queue +
                                                   self.subjobindex[sub.name].run, 0)
                                    # fixes_applied.setdefault(sub_children_name, []).append(fix_size) # If we care about repetition
                                    # Retain the greater fix size
                                    if fix_size > fixes_applied.get(sub_children_name, 0):
                                        fixes_applied[sub_children_name] = fix_size
                                    fixed_queue_time = max(
                                        self.subjobindex[sub_children_name].queue - fix_size, 0)
                                    new_queues[sub_children_name] = fixed_queue_time
                                    # print(new_queues[sub_name])

                for key, value in new_queues.items():
                    self.subjobindex[key].queue = value
                    # print("{} : {}".format(key, value))
                for name in fixes_applied:
                    self.subjobfixes[name] = fixes_applied[name]

            else:
                # There is no structure
                for package in self.package_to_jobs:
                    # Filter only jobs in the current package
                    filtered = [x for x in self.subjobList if x.package ==
                                      package]
                    # Order jobs by total time (queue + run)
                    filtered = sorted(
                        filtered, key=lambda x: x.total, reverse=False)
                    # Sizes of fixes
                    fixes_applied = dict()
                    if len(filtered) > 1:
                        temp_index = 0
                        filtered[0].transit = 0
                        # Reverse for
                        for i in range(len(filtered) - 1, 0, -1):
                            # Assume that the total time of the next job is always smaller than
                            # the queue time of the current job
                            # because the queue time of the current also considers the
                            # total time of the previous (next because of reversed for) job by default
                            # Confusing? It is.
                            # Assign to transit the adjusted queue time
                            filtered[i].transit = max(filtered[i].queue -
                                                      filtered[i - 1].total, 0)

                        # Positive or zero transit time
                        positive = len(
                            [job for job in filtered if job.transit >= 0])

                        if positive > 1:
                            for i in range(0, len(filtered)):
                                if filtered[i].transit >= 0:
                                    temp_index = i
                                    if i > 0:
                                        # Only consider after the first job
                                        filtered[i].queue = max(filtered[i].queue -
                                                                filtered[i - 1].total, 0)
                                        fixes_applied[filtered[i].name] = filtered[i - 1].total
                                else:
                                    filtered[i].queue = max(filtered[i].queue -
                                                            filtered[temp_index].total, 0)
                                    fixes_applied[filtered[i].name] = filtered[temp_index].total
                                # it is starting of level

                    for sub in filtered:
                        self.subjobindex[sub.name].queue = sub.queue
                        # print("{} : {}".format(sub.name, sub.queue))
                    for name in fixes_applied:
                        self.subjobfixes[name] = fixes_applied[name]

    def get_subjoblist(self):
        """
        Returns the list of SubJob objects with their corrected queue times
        in the case of jobs that belong to a wrapper.
        """
        return self.subjobList

    def get_collection_of_fixes_applied(self):
        # type: () -> Dict[str, int]
        """
        """
        return self.subjobfixes