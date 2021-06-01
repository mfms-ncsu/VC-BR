#! /usr/bin/env python3

"""
extracts an induced subgraph from a graph in snap format
"""

import argparse
import sys
from time import gmtime, strftime

def parse_arguments():
    parser = argparse.ArgumentParser(description="takes a list of space-separated"
                                     + " vertex numbers from stdin"
                                     + " and a file with a graph in snap format"
                                     + " as input;"
                                     + " outputs an induced subgraph to stdout")
    parser.add_argument("input_file",
                        help="input file in snap format from which to extract subgraph"
                        + " corresponding to list of vertex numbers in standard input")
    parser.add_argument("-k", "--keep_original", action='store_true',
                        help="keep original vertex numbers")
    return parser.parse_args()

_comments = []

# @return a list of vertices from the file stream
def get_vertices(file_stream):
    vertices = []
    for line in file_stream:
        numbers_on_line = line.split()
        vertices.extend([int(v) for v in numbers_on_line])
    return vertices

# @return list of edges of the graph and a list of vertex ids
def get_edges(file_stream):
    global _comments
    vertex_ids = []
    edges = [] 
    largest_id = 0
    for line in file_stream:
        if line.split()[0] == '#':
            _comments.append(line)
        else:
            edge = [int(e) for e in line.strip().split()]
            edges.append(edge)
            if edge[0] not in vertex_ids:
                vertex_ids.append(edge[0])
            if edge[1] not in vertex_ids:
                vertex_ids.append(edge[1])
    return edges, vertex_ids

# @return a dictionary that maps original vertex ids to new ones
def create_mapping(original_vertices, subgraph_vertices):
    mapping = {}
    for i, j in zip(original_vertices, subgraph_vertices):
        mapping[i] = j
    return mapping

# prints date, time, the list of (original) vertices in the subgraph, and the
# original comments
def print_header(output_stream, vertex_ids):
    date_and_time_string = strftime("%Y-%m-%d %X", gmtime())
    output_stream.write("# induced subgraph of {}\n#  created {}, with vertices\n".format(_input_file,date_and_time_string))
    output_stream.write("#")
    for vertex in vertex_ids:
        output_stream.write(" {}".format(vertex))
    output_stream.write("\n")
    if len(_comments) > 0:
        output_stream.write("# original comments -\n")
        for comment in _comments:
            output_stream.write(comment)

# @return true if both endpoints of edge are in subgraph_vertices
def both_endpoints(edge, subgraph_vertices):
    if edge[0] in subgraph_vertices and edge[1] in subgraph_vertices:
        return True
    else:
        return False

# @return a list representing the subset of edges both endpoints of which are
# subgraph_vertices
def extract_subgraph_edges(edges, subgraph_vertices):
    subgraph_edges = []
    for edge in edges:
        if both_endpoints(edge, subgraph_vertices):
            subgraph_edges.append(edge)
    return subgraph_edges

# writes the induced subgraph to the output stream with renumbered vertices;
# for each edge (v,w) in edges the output edge is (mapping[v],mapping[w])
def print_graph(output_stream, edges, mapping):
    for edge in edges:
        v = edge[0]
        w = edge[1]
        if args.keep_original:
            output_stream.write("{} {}\n".format(v, w))
        else:
            output_stream.write("{} {}\n".format(mapping[v], mapping[w]))
            
if __name__ == '__main__':
    global _input_file
    global args
    args = parse_arguments()
    _input_file = args.input_file
    subgraph_vertices = get_vertices(sys.stdin)
    file_stream = open(_input_file, "r")
    edges, vertex_ids = get_edges(file_stream)
    new_ids = list(range(1, len(subgraph_vertices) + 1))
    mapping = create_mapping(subgraph_vertices, new_ids)
    subgraph_edges = extract_subgraph_edges(edges, subgraph_vertices)
    print_header(sys.stdout, subgraph_vertices)
    print_graph(sys.stdout, subgraph_edges, mapping)

#  [Last modified: 2019 09 17 at 21:31:49 GMT]
