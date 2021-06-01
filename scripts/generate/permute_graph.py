#! /usr/bin/env python3

"""
creates a given number of copies of a graph in snap format;
the vertices are randomly renumbered and edges put in random order in each copy
"""

import argparse
import random
from copy import deepcopy
from time import gmtime, strftime

EXTENSION = ".snap"

def parse_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument("-o", "--output", dest = "output_folder", default = ".",
                        help = "Output folder for permutation files (default: current folder)")
    parser.add_argument("-n", "--number", dest = "number", default = 30, help = "Number of permutations to generate")
    parser.add_argument("-c", "--compact", action='store_true', help="create graphs with contiguous vertex numbers starting at 1")
    parser.add_argument("input_file", help="input file in snap format to permute")
    return parser.parse_args()

_comments = []

# @return list of edges of the graph and a list of vertex ids
def get_edges(file_name):
    global _comments
    edges = [] 
    largest_id = 0
    with open(file_name) as f:
        vertex_ids = []
        for line in f:
            if len(line.strip()) > 0:
                if line.split()[0] == "#" or line.split()[0][0] == '#':
                    # first token is # or first character of first token is #
                    _comments.append(line)
                elif len(line) > 1:
                    edge = [int(e) for e in line.strip('\n').split()]
                    if edge[0] != edge[1]:
                        edges.append(edge)
                    if edge[0] not in vertex_ids:
                        vertex_ids.append(edge[0])
                    if edge[1] not in vertex_ids:
                        vertex_ids.append(edge[1])
    return edges, vertex_ids

def create_permutation_files(mapping, edges, directory, base_name, number):
    new_file = directory + '/' + base_name + "-{:02d}".format(number) + EXTENSION
    with open(new_file, 'w') as f:
        date_and_time_string = strftime("%Y-%m-%d %X", gmtime())
        for comment in _comments:
            f.write(comment)
        f.write("#  permuted {}, using permute_graph.py, instance {:02d}\n".format(date_and_time_string, number))
        for edge in edges:
            f.write("{} {}\n".format(mapping[edge[0]], mapping[edge[1]]))
    map_file = directory + '/' + base_name + "-{:02d}".format(number) + '.map'
    with open(map_file, 'w') as f:
        f.write("# mapping file for {}-{:02d}EXTENSION, created {}\n".format(base_name, number, date_and_time_string))
        for original, mapped in mapping.items():
            f.write("{} {}\n".format(mapped, original))

# @return a dictionary that maps each new (permuted) vertex id to its original counterpart
def create_mapping(original_vertices, permuted_vertices):
    mapping = {}
    for i, j in zip(original_vertices, permuted_vertices):
        mapping[i] = j
    return mapping

if __name__ == '__main__':
    args = parse_arguments()
    print("reading original graph")
    edges, vertex_ids = get_edges(args.input_file)
    base_name = '.'.join(args.input_file.split("/")[-1].split(".")[:-1])
    if args.compact:
        permuted_ids = list(range(1, len(vertex_ids) + 1))
    else:
        permuted_ids = deepcopy(vertex_ids)
    mapping = create_mapping(vertex_ids, permuted_ids)
    create_permutation_files(mapping, edges, args.output_folder, base_name, 0)
    print("creating permutations")
    for i in range(1, int(args.number)):
        print("creating permutation %d" % i)
        random.shuffle(permuted_ids)
        mapping = create_mapping(vertex_ids, permuted_ids)
        random.shuffle(edges)
        create_permutation_files(mapping, edges, args.output_folder, base_name, i)

    print("done with ", args.input_file.split("/")[-1], "number of instances", args.number)
    print(" in directory", args.output_folder)

#  [Last modified: 2020 01 10 at 18:19:57 GMT]
