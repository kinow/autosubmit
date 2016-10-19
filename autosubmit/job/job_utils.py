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
