#!/usr/bin/env python

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

def get_job_package_code(job_name):
    """
    Finds the package code and retrieves it. None if no package.

    :param BasicConfig: Basic configuration 
    :type BasicConfig: Configuration Object
    :param expid: Experiment Id
    :type expid: String
    :param current_job_name: Name of job
    :type current_jobs: string
    :return: package code, None if not found
    :rtype: int or None
    """
    try:
        packages_wrapper = JobPackagePersistence(os.path.join(self.basic_conf.LOCAL_ROOT_DIR, self.expid, "pkl"),"job_packages_" + self.expid).load(wrapper=True)
        packages_wrapper_plus = JobPackagePersistence(os.path.join(self.basic_conf.LOCAL_ROOT_DIR, self.expid, "pkl"),"job_packages_" + self.expid).load(wrapper=False)
        if (packages_wrapper or packages_wrapper_plus):
            packages = packages_wrapper if len(packages_wrapper) > len(packages_wrapper_plus) else packages_wrapper_plus
            for exp, package_name, _job_name in packages:
                if job_name == _job_name:
                    code = int(package_name.split("_")[2])
                    return code            
    except:
        pass
    return 0

class Dependency(object):
    """
    Class to manage the metadata related with a dependency

    """

    def __init__(self, section, distance=None, running=None, sign=None, delay=-1, splits=None, select_chunks=list()):
        self.section = section
        self.distance = distance
        self.running = running
        self.sign = sign
        self.delay = delay
        self.splits = splits
        self.select_chunks_dest = list()
        self.select_chunks_orig = list()
        for chunk_relation in select_chunks:
            self.select_chunks_dest.append(chunk_relation[0])
            if len(chunk_relation) > 1:
                self.select_chunks_orig.append(chunk_relation[1])
            else:
                self.select_chunks_orig.append([])
