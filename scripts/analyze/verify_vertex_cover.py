#! /usr/bin/env python3

"""
 checks to see whether a given solution is correct for a given vertex cover instance
 Usage: ./verify_vertex_cover.py [options] problem_instance < solution
        where problem_instance is a file in snap format and solution is one of
           - a list of vertices in the cover, one per line (default)
           - a single string of 0's and 1's, where a 1 in position i means i is in the cover
 Can be used as a filter, as in
    cat - | ./verify_vertex_cover [options] problem_instance
 and then paste the solution on the terminal
"""

import argparse
import sys

from graph import Graph, GraphReader
from debug_printer import debug_printer

def parse_arguments():
    parser = argparse.ArgumentParser(description="Takes a proposed vertex cover"
                                     + ", either as a vector of 0's and 1's,"
                                     + " or as a list of vertex numbers,"
                                     + " and checks whether the cover is"
                                     + " valid for the input graph."
                                     + " Usage: cat - | verify_vertex_cover ... "
                                     + "and paste the solution."
                                     + " The vector of 0's and 1's is 0-based, i.e.,"
                                     + " the first character is ignored if there is"
                                     + " no vertex with number 0") 

    parser.add_argument("input_file_path", help="a file in snap format")
    parser.add_argument("-L", "--vertex_list", action='store_true',
                        help="cover is a list of vertex numbers, one per line;\n default is a string of 0's and 1's")
    parser.add_argument("-U", "--undecided", action='store_true',
                        help="print undecided vertices and edges (x's in the input)")
    parser.add_argument("-UV", "--undecided_vertices", action='store_true',
                        help="print undecided vertices only (x's in the input)")
    parser.add_argument("-s", "--solution", action='store_true',
                        help="print the cover as a list of vertices (python format)")

    args = parser.parse_args()

    return args

# @return (i) the value of the cover represented by the input vertex_list,
# (ii) a list of vertices in the cover, and (iii) a string representing the
# status of each vertex; item (iii) is non-empty only if the vertex_list is a
# string of 0's, 1's and other symbols, e.g., x for undecided, and in that
# case the input is returned directly.
# This is a work-around to the original design for now.
# The purpose is debugging convenience in case other information about a
# partial solution is desired.
def ReadCover(file_stream, vertex_list):
    cover = set()
    status_string = ""
    value = 0
    if vertex_list:
        # each line is an integer representing a vertex
        for line in file_stream:
             cover.add(int(line))
             value += 1
    else:
        # line is a string of 0's and 1's; the i-th position is 1 iff vertex i is in the cover
        line = file_stream.readline().strip()
        status_string = line
        for i in range(len(line)):
            if line[i] == "1":
                # vertex numbering starts with 1, indexing of strings is 0-based
                cover.add(i)
                value += 1
    return value, cover, status_string

# @return (i) a list of undecided vertices - those marked x in the status
# string, and (ii) a list of tuples representing edges between pairs of
# undecided vertices
def get_undecided_graph(graph, status_string):
    undecided_vertices = []
    undecided_edges = []
    for v in graph.vertices:
        if v <= len(status_string) and status_string[v] == 'x':
            undecided_vertices.append(v)
    for (v,w) in graph.edges:
        if v <= len(status_string) and w <= len(status_string) \
           and status_string[v] == 'x' and status_string[w] == 'x':
            undecided_edges.append((v,w))
    return undecided_vertices, undecided_edges

def verify_vertex_cover(graph, vertex_cover):
    for (v,w) in graph.edges:
        if (v not in vertex_cover) and (w not in vertex_cover):
            return False
    return True

if __name__ == '__main__':
    args = parse_arguments()
    graph = GraphReader().read_graph(args.input_file_path)
    value, cover, status_string = ReadCover(sys.stdin, args.vertex_list)
    if args.undecided or args.undecided_vertices:
        undecided_vertices, undecided_edges = get_undecided_graph(graph, status_string)
    verified = verify_vertex_cover(graph, cover)
    if args.undecided or args.undecided_vertices:
        print("number_undecided =", len(undecided_vertices))
    if args.solution:
        print("cover =", cover)
    if args.undecided and len(undecided_vertices) > 0:
        print("undecided_vertices =", undecided_vertices)
        print("undecided_edges =", undecided_edges)
    elif args.undecided_vertices and len(undecided_vertices) > 0:
        print("undecided_vertices =", undecided_vertices)
    print("value =", value)
    if verified:
        print("Correct Solution")
    else:
        print("*** Incorrect Solution ***")

#  [Last modified: 2020 02 27 at 22:37:50 GMT]
