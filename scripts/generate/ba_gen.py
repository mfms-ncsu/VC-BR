#! /usr/bin/env python3

"""
ba_gen.py - a generator of a Barabasi-Albert graph given number of
vertices and desired average degree
"""

import argparse
import sys
import random
import networkx as nx

def parse_arguments():
    parser = argparse.ArgumentParser(description="Creates a random Barabasi-Albert graph"
                                     + " Vertices are numbered starting at 0.")
    parser.add_argument("num_vertices", help="number of vertices", type=int)
    parser.add_argument("avg_deg", help="desired average degree (integer)", type=int)
    parser.add_argument("-o", "--output", help="output file name; stdout if not given")
    parser.add_argument("-s", "--seed", type=int, help="seed for random generator;"
                        + " internal random seed if missing")
    args = parser.parse_args()
    return args

def write_graph(out_stream, G, seed):
    out_stream.write("# created by {}\n".format(" ".join(sys.argv)))
    out_stream.write("# {} {} {}\n".format(nx.number_of_nodes(G), nx.number_of_edges(G), seed))
    edge_list = nx.generate_edgelist(G, data=False)
    for output_line in edge_list:
        out_stream.write("{}\n".format(output_line))

if __name__ == '__main__':
    args = parse_arguments()
    random.seed(args.seed)
    if args.output:
        out_stream = open(args.output, 'w')
    else:
        out_stream = sys.stdout
    attachment_edges = args.avg_deg // 2
    G = nx.barabasi_albert_graph(args.num_vertices, attachment_edges)
    write_graph(out_stream, G, args.seed)

#  [Last modified: 2021 06 01 at 18:55:56 GMT]
