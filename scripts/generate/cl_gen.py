#! /usr/bin/env python3

"""
cl_gen.py - a generator of a Chung-Lu graph given various parameters relating to
            degree sequence generation; also has option of reading sequence from
            file or standard input
"""

import argparse
import sys
import random
import networkx as nx

def parse_arguments():
    parser = argparse.ArgumentParser(description="Creates a random Chung-Lu graph."
                                     + " Vertices are numbered starting at 0."
                                     + " If arguments relating to number of vertices and"
                                     + " degrees are missing,"
                                     + " the degree sequence is taken from"
                                     + " a file or standard input.")
    parser.add_argument("-o", "--output", help="output file name; stdout if not given")
    parser.add_argument("-i", "--input", help="input file name; stdin if not given")
    parser.add_argument("-s", "--seed", type=int, help="seed for random generator;"
                        + " internal random seed if missing")
    parser.add_argument("-d", "--avg_deg", help = "average degree (floating point)",
                        type = float)
    parser.add_argument("-md", "--min_deg",
                        help = "desired miminum degree of a vertex (default 1)",
                        type = int)
    parser.add_argument("-MD", "--max_deg",
                        help = "desired maximum degree of a vertex (default n-1)",
                        type = int)
    parser.add_argument("-n", "--num_vertices",
                        help = "number of vertices, must be present"
                        + " if degree arguments are specified (otherwise these are ignored)",
                        type = int)
    parser.add_argument("--dist", default="uniform",
                        help = "degree distribution, one of "
                        + "'uniform' (default)"
                        + ", 'spike' (very few vertices at the extremes, normal distrbution)"
                        )
    args = parser.parse_args()
    return args

def read_degrees(in_stream):
    degree_list = []
    for line in in_stream.readlines():
        degree_list.append(int(line.strip().split()[0]))
    return degree_list

def write_graph(out_stream, G, seed):
    out_stream.write("# Chung-Lu graph: vertices edges seed\n")
    out_stream.write("# {} {} {}\n".format(nx.number_of_nodes(G), nx.number_of_edges(G), seed))
    out_stream.write("# cl_gen {}\n".format(' '.join(sys.argv[1:])))
    edge_list = nx.generate_edgelist(G, data=False)
    for output_line in edge_list:
        out_stream.write("{}\n".format(output_line))

def uniform(n, min_deg, max_deg):
    """
    @return a list of n uniformly distributed random integers in interval [min_deg,max_deg]
    """
    degree_list = []
    for i in range(n):
        degree_list.append(random.randint(min_deg, max_deg))
    return degree_list

def spike(n, min_deg, max_deg, avg_deg):
    degree_list = (n - 2) * [avg_deg]
    degree_list.append(min_deg)
    degree_list.append(max_deg)
    return degree_list
          
if __name__ == '__main__':
    args = parse_arguments()
    random.seed(args.seed)
    if args.input:
        in_stream = open(args.input, 'r')
    else:
        in_stream = sys.stdin
    if args.output:
        out_stream = open(args.output, 'w')
    else:
        out_stream = sys.stdout
    if args.num_vertices:
        min_deg = 1
        if args.min_deg:
            min_deg = args.min_deg
        max_deg = args.num_vertices - 1
        if args.max_deg:
            max_deg = args.max_deg
        avg_deg = (min_deg + max_deg) / 2
        if args.avg_deg:
            avg_deg = args.avg_deg
        if args.dist == "uniform":
            degree_list = uniform(args.num_vertices, min_deg, max_deg)
        elif args.dist == "spike":
            degree_list = spike(args.num_vertices, min_deg, max_deg, avg_deg)
    else:
        sys.stderr.write("Warning: no degree info given, reading from file or stdin\n")
        degree_list = read_degrees(in_stream)
    G = nx.expected_degree_graph(degree_list, args.seed, False)
    write_graph(out_stream, G, args.seed)


#  [Last modified: 2021 06 01 at 19:23:09 GMT]
