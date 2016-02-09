import networkx as nx


def silly_graph():
    g = nx.MultiDiGraph()
    g.add_nodes_from(range(0, 3))
    g.add_edge(0, 1, reads="0", prints="0", erases=True)
    g.add_edge(1, 2, reads='1', prints='', erases=False)
    g.add_edge(1, 2, reads='0', prints='', erases=True)
    g.add_edge(2, 0, reads='0', prints='', erases=False)
    return g


def id_transducer():
    g = nx.MultiDiGraph()
    g.add_node(0)
    g.add_edge(0, 0, reads='0', prints='0', erases=True)
    g.add_edge(0, 0, reads='1', prints='1', erases=True)
    return g


def unreachable_state():
    g = id_transducer()
    g.add_node(1)
    g.add_edge(1, 1, reads='0', prints='0', erases=True)
    g.add_edge(1, 0, reads='1', prints='0', erases=False)
    return g
