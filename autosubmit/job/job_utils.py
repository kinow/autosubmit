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

import networkx

from networkx.algorithms.dag import is_directed_acyclic_graph
from networkx import DiGraph
from networkx import dfs_edges
from networkx import NetworkXError


def transitive_reduction(graph):
    if not is_directed_acyclic_graph(graph):
        raise NetworkXError("Transitive reduction only uniquely defined on directed acyclic graphs.")
    reduced_graph = DiGraph()
    reduced_graph.add_nodes_from(graph.nodes())
    for u in graph:
        u_edges = set(graph[u])
        for v in graph[u]:
            u_edges -= {y for x, y in dfs_edges(graph, v)}
        reduced_graph.add_edges_from((u, v) for v in u_edges)
    return reduced_graph


class Dependency(object):
    """
    Class to manage the metadata related with a dependency

    """

    def __init__(self, section, distance=None, running=None, sign=None):
        self.section = section
        self.distance = distance
        self.running = running
        self.sign = sign

