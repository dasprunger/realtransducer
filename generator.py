import itertools as it
import networkx as nx
import copy
import realtransducer as rt


def generate_targets(nodes, alphabet):
    return it.product(nodes, repeat=len(nodes)*len(alphabet))


def generate_base_graphs(num_nodes, alphabet='01'):
    target_list_gen = generate_targets(range(0, num_nodes), alphabet)
    for target_list in target_list_gen:
        graph = nx.MultiDiGraph()
        graph.add_nodes_from(range(0, num_nodes))
        for idx, target in enumerate(target_list):
            graph.add_edge(idx/len(alphabet), target, reads=str(idx % len(alphabet)))

        #  For simplicity we assume everything is reachable from the initial node.
        reachable = [nx.has_path(graph, 0, n) for n in graph.nodes()]
        if not all(reachable):
            continue
        else:
            yield graph


def generate_decorations(num_edges, output_alphabet=('', '0', '1')):
    return it.product(it.product(output_alphabet, (True, False)), repeat=num_edges)


def generate_transducers(num_nodes, alphabet='01'):
    for base_graph in generate_base_graphs(num_nodes, alphabet=alphabet):
        for decorations in generate_decorations(base_graph.size()):
            decorated_graph = copy.deepcopy(base_graph)
            for idx, edge in enumerate(decorated_graph.edges_iter(data=True)):
                edge[2]["prints"] = decorations[idx][0]
                edge[2]["erases"] = decorations[idx][1]

            try:
                t = rt.RealTransducer(decorated_graph)
            except ValueError:
                continue
            else:
                yield t


def save_transducers():
    count = 1
    for size in range(1, 10):
        gt = generate_transducers(size)
        for transducer in gt:
            if count >= 10000:
                return
            with open("examples/%s.txt" % str(count), 'w') as f:
                f.write(str(len(transducer.graph)) + "\n")
                f.write(str(transducer.graph.edges(data=True)))
            count += 1


def generate_inputs(bits=5):
    for i in it.product("01", repeat=bits):
        yield "".join(i)


def get_example_transducer(number):
    with open("examples/%s.txt" % str(number), "r") as f:
        first = f.readline()
        second = f.readline()
    return rt.RealTransducer.init_from_string(first, second)


def find_behavior_of_examples():
    behaviors = []
    count = 0
    for i in xrange(1, 10000):
        t = get_example_transducer(i)
        behavior = t.initial_behavior(bits=5)
        if behavior in behaviors:
            idx = behaviors.index(behavior)
            with open('behaviors/beh%s.txt' % str(idx).zfill(2), 'a') as f:
                f.write("machine # %s\n" % str(i))
        else:
            with open('behaviors/beh%s.txt' % str(count).zfill(2), 'w') as f:
                for idx, input_string in enumerate(generate_inputs(bits=5)):
                    f.write("%s |--> %s\n" % (input_string, behavior[idx]))
                f.write("\nmachine # %s\n" % str(i))
            behaviors.append(behavior)
            count += 1


def find_minimal_machines():
    behaviors = []
    count = 0
    for size in range(1, 10):
        for t in generate_transducers(size):
            if count >= 100:
                return
            behavior = t.initial_behavior(bits=5)
            if behavior in behaviors:
                continue
            else:
                with open('minimal/%s.txt' % str(count).zfill(3), 'w') as f:
                    f.write(str(len(t.graph)) + "\n")
                    f.write(str(t.graph.edges(data=True)) + "\n\n")
                    for idx, input_string in enumerate(generate_inputs(bits=5)):
                        f.write("%s |--> %s\n" % (input_string, behavior[idx]))
                behaviors.append(behavior)
                count += 1

