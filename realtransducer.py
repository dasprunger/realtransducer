import ast
import networkx as nx
import itertools as it
from cycleword import PeriodicBinary


INPUT_ALPHABET = ['0', '1']
OUTPUT_ALPHABET = ['0', '1']
READS = 'reads'
PRINTS = 'prints'
ERASES = 'erases'


def generate_inputs(bits=5):
    for i in it.product("01", repeat=bits):
        yield "".join(i)


def check_cycle_for_print(g, cy):
    edge_prints = []
    for idx in range(-1, len(cy)-1):
        edges = g[cy[idx]][cy[idx+1]].values()
        ep = all([e[PRINTS] is not None for e in edges])
        edge_prints.append(ep)

    return any(edge_prints)


def next_edge(graph, node, character):
    return [e for e in graph.edges(node, data=True) if e[2][READS] == character][0]


def find_loop_pb(graph, node, character):
    nodes, prints = [], []
    next_node = node

    while next_node not in nodes:
        nodes.append(next_node)
        ne = next_edge(graph, node, character)
        next_node = ne[1]
        prints.append(ne[2][PRINTS])
    else:
        idx = nodes.index(next_node)
        initial = "".join(prints[0:idx])
        period = "".join(prints[idx:])
        pb = PeriodicBinary(initial, period)
        graph.node[node][character] = pb
        return pb


def forall_loop_pb(graph):
    for node in graph.nodes():
        for character in INPUT_ALPHABET:
            find_loop_pb(graph, node, character)


class RealTransducer(object):
    graph = None

    def __init__(self, graph):
        #  A real transducer is a multigraph where...
        if isinstance(graph, nx.MultiDiGraph):
            g = graph
        else:
            raise ValueError("Real transducer must be based on a multidigraph.")

        #  The nodes are an initial segment of the integers
        if g.nodes() != range(0, len(g.nodes())):
            raise ValueError("Node set of transducer is not initial segment of the integers.")

        #  Every edge has a read value in the input alphabet, a boolean erases value, and may have a print value
        for edge in g.edges(data=True):
            edge_data = edge[2]
            if READS not in edge_data or PRINTS not in edge_data or ERASES not in edge_data:
                raise ValueError("Edge missing required value.")
            if edge_data[READS] not in INPUT_ALPHABET:
                raise ValueError("Edge reads character not in input alphabet.")
            if edge_data[PRINTS] != '' and edge_data[PRINTS] not in OUTPUT_ALPHABET:
                raise ValueError("Edge has bad print value.")
            if not isinstance(edge_data[ERASES], bool):
                raise ValueError("Erases is not a bool value.")

        #  For each node, the read values on the outgoing edges form the input alphabet exactly.
        for node in g.nodes():
            read_values = [x[2][READS] for x in g.edges(node, data=True)]
            if len(read_values) != len(INPUT_ALPHABET):
                raise ValueError("Incorrect number of outgoing edges.")
            if set(read_values) != set(INPUT_ALPHABET):
                raise ValueError("Outgoing edge read values don't match input alphabet.")

        #  Every cycle must have a print value
        for cycle in nx.simple_cycles(g):
            if not check_cycle_for_print(g, cycle):
                raise ValueError("Printless cycle")

        #  For simplicity we assume everything is reachable from the initial node.
        reachable = [nx.has_path(g, 0, n) for n in g.nodes()]
        if not all(reachable):
            raise ValueError("Unreachable states.")

        forall_loop_pb(g)
        self.graph = graph

        #  Inputs 10000 and 01111 must yield the same print
        for node in g.nodes():
            behavior_zero = self.evaluate(PeriodicBinary("0", "1"), start_state=node)
            behavior_one = self.evaluate(PeriodicBinary("1", "0"), start_state=node)

            if behavior_one != behavior_zero:
                raise ValueError("Unequal behavior on different representatives")

    def _single_char_eval(self, char, start_state=0):
        output_blocks = []
        visited_nodes = []
        current_node = start_state
        while current_node not in visited_nodes:
            visited_nodes.append(current_node)
            ne = next_edge(self.graph, current_node, char)
            output_blocks.append(ne[2][PRINTS])
            current_node = ne[1]
            if ne[2][ERASES]:
                return "".join(output_blocks), current_node
        idx = visited_nodes.index(current_node)
        initial = "".join(output_blocks[0:idx])
        period = "".join(output_blocks[idx:])
        return PeriodicBinary(initial, period), current_node

    def _finite_frag_eval(self, finite_input, start_state=0):
        output = ''
        current_node = start_state
        while finite_input:
            next_output, current_node = self._single_char_eval(finite_input[0], current_node)
            if isinstance(next_output, PeriodicBinary):
                return next_output.prepend(output), current_node
            else:
                output += next_output
                finite_input = finite_input[1:]
        return output, current_node

    def evaluate(self, input_object, start_state=0):
        if isinstance(input_object, str):
            return self.evaluate(PeriodicBinary(input_object, "0"), start_state=start_state)
        elif isinstance(input_object, PeriodicBinary):
            initial_output, current_node = self._finite_frag_eval(input_object.initial, start_state=start_state)
            if isinstance(initial_output, PeriodicBinary):
                return initial_output

            output_blocks = []
            nodes_times_period = []
            dig_gen = enumerate(it.cycle(input_object.period))
            read_pos, read_char = dig_gen.next()
            read_pos %= len(input_object.period)
            while (current_node, read_pos) not in nodes_times_period:
                nodes_times_period.append((current_node, read_pos))
                next_output, current_node = self._finite_frag_eval(read_char, start_state=current_node)
                if isinstance(next_output, PeriodicBinary):
                    return next_output.prepend(initial_output + "".join(output_blocks))
                else:
                    output_blocks.append(next_output)
                read_pos, read_char = dig_gen.next()
                read_pos %= len(input_object.period)
            idx = nodes_times_period.index((current_node, read_pos))
            initial_output += "".join(output_blocks[0:idx])
            periodic_output = "".join(output_blocks[idx:])
            return PeriodicBinary(initial_output, periodic_output)

    def initial_behavior(self, bits=10):
        behavior = []
        for input_string in generate_inputs(bits):
            behavior.append(self.evaluate(input_string))
        return behavior

    @staticmethod
    def init_from_string(num_nodes_string, edge_list_string):
        g = nx.MultiDiGraph()
        g.add_nodes_from(range(0, int(num_nodes_string)))
        edge_list = ast.literal_eval(edge_list_string)
        for edge in edge_list:
            g.add_edge(edge[0], edge[1], reads=edge[2][READS], prints=edge[2][PRINTS], erases=edge[2][ERASES])
        return RealTransducer(g)

    def is_bisimilar_to(self, other):
        if not isinstance(other, RealTransducer):
            return False
        if self.graph.order() == 0 and other.graph.order() == 0:
            return True
        elif self.graph.order() == 0 or other.graph.order() == 0:
            return False

        verified_relation = []
        next_relation = [(0, 0)]
        while next_relation:
            pair = next_relation[0]
            here_node_data = [x[1] for x in self.graph.nodes(data=True) if x[0] == pair[0]][0]
            other_node_data = [x[1] for x in other.graph.nodes(data=True) if x[0] == pair[1]][0]

            if here_node_data["0"] != other_node_data["0"] or here_node_data["1"] != other_node_data["1"]:
                return False
            for char in INPUT_ALPHABET:
                here_transition = next_edge(self.graph, pair[0], char)
                other_transition = next_edge(other.graph, pair[1], char)
                if here_transition[2][ERASES] != other_transition[2][ERASES] or here_transition[2][PRINTS] != other_transition[2][PRINTS]:
                    return False

                next_pair = (here_transition[1], other_transition[1])
                if next_pair not in verified_relation and next_pair not in next_relation:
                    next_relation.append(next_pair)
            verified_relation.append(pair)
            next_relation.remove(pair)
        return True


def test_on_inputs(t1, t2, bits=5, verbose=False):
    same = True
    for input_string in generate_inputs(bits):
        output1 = t1.evaluate(input_string)
        output2 = t2.evaluate(input_string)
        if verbose:
            print "On %s: %s vs %s" % (input_string, str(output1), str(output2))
        if output1 != output2:
            same = False
    if verbose:
        if not same:
            print "Machines differ on some input"
        else:
            print "Machines match (so far...)"
    return same


