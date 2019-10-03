#! /usr/bin/env python3

"""
wcg_gen.py - generates dense graphs with small vertex covers by expanding a construction
             that shows the greedy heuristic to have arbitrarily bad approximation ratio
"""

from argparse import ArgumentParser
from argparse import RawTextHelpFormatter # to allow newlines in help messages
import sys
import math
import random

def parse_arguments():
    parser = ArgumentParser(formatter_class=RawTextHelpFormatter,
                                     description =
                                     "Generates a graph based on a bipartite graph"
                                     + " used to show poor approximation by a"
                                     + " greedy vertex cover algorithm."
    )
    parser.add_argument("core", type = int,
                        help = "number of cover vertices in the original construction")
    parser.add_argument("multiplicity", type = int,
                        help = "number of copies of the core;"
                        + " so min cover has size core * multiplicity")
    parser.add_argument("-r", "--random", help = "number of random non-bipartite edges"
                        + " to add;\n default is to create a cycle that includes all vertices"
                        + " on one or both sides")
    parser.add_argument("-e", "--extra", help = "where to put extra edges;"
                        + "\n 'c' = cover side (default),"
                        + "\n 'u' = other side,"
                        + "\n 'b' = both sides")
    parser.add_argument("-o", "--output", help = "output file name;"
                        + " a standardized name if '_'; stdout if not given"
                        + "\n standardized name has form wcg-xy_ttt_mm_eeee_ss.snap"
                        + "\n where x is 'c' (cycle) or 'r' (random)"
                        + "\n       y is the '-e' option"
                        + "\n       ttt is the number of vertices in the core"
                        + "\n       mm is the multiplicity"
                        + "\n       eeee is the number of extra edges (num vertices if cycle)"
                        + "\n       ss is the random seed (omitted in case of cycle)"
    )
    parser.add_argument("-s", "--seed", type=int, help="seed for random generator;"
                        + " internal random seed if missing")
    args = parser.parse_args()
    return args

"""
The label of each vertex is a tuple of the form (0,i,j) or (1,k,l)
In the original bipartite construction, if the are t vertices in the core,
(0,i,j) vertices are grouped into sets U_i,
        i = 1 to t, where |U_i| = floor(t/i), j = 1 to |U_i|;
(1,k,l) vertices have k = 1 to t and l = 1 to multiplicity
(0,i,j) is adjacent to (1,k,l) if ceiling(k/i) = j (for all l)

Two global dictionaries are used during generation (key = label for each):
      _vertex_number is the vertex number to be used in the output file
      _adj_list is a *set* of labels of adjacent vertices
      by convention, only one copy of each edge is stored in an adjacency list:
      an edge is stored in the adj list of the lexicographically smaller vertex
"""
_vertex_number = {}
_adj_list = {}

def init_vertices():
    """
    initialize the two data structures so that they have entries for the vertices:
    numbers can be assigned directly
    all adjacency lists are originally empty sets
    """
    n = 0                       # number of vertices so far, also used to number vertices
    # first the U_i vertices
    for i in range(1, _args.core + 1):
        for j in range(1, _args.core // i + 1):
            n += 1
            _vertex_number[(0,i,j)] = n
            _adj_list[(0,i,j)] = set({})
    # then the others
    for k in range(1, _args.core + 1):
        for ell in range(0, _args.multiplicity):
            n += 1
            _vertex_number[(1,k,ell)] = n
            _adj_list[(1,k,ell)] = set({})

def add_edge(v_1, v_2):
    """
    add the edge to the adjacency list of the lexicographically smaller vertex
    """
    if v_2 < v_1:               # swap vertices so that v_1 < v_2
        tmp = v_1; v_1 = v_2; v_2 = tmp
    _adj_list[v_1].add(v_2)

def add_bipartite_edges():
    """
    adds edges based on the original bipartite construction
    """
    for i in range(1, _args.core + 1):
        for j in range(1, _args.core // i + 1):
            for k in range(1, _args.core + 1):
                for ell in range(0, _args.multiplicity):
                    if math.ceil(k / i) == j:
                        add_edge((0,i,j), (1,k,ell))

def add_cover_cycle_edges():
    """
    creates a cycle that includes all vertices in the min cover
    """
    for ell in range(0, _args.multiplicity):
        for k in range(1, _args.core):
            add_edge((1,k,ell), (1,k+1,ell))
        add_edge((1,_args.core,ell), (1,1,(ell+1) % _args.multiplicity))
    
if __name__ == '__main__':
    global _args
    _args = parse_arguments()
    init_vertices()
    add_bipartite_edges()
    add_cover_cycle_edges()
    print("_vertex_number =", _vertex_number)
    print("_adj_list =", _adj_list)

#  [Last modified: 2019 10 03 at 15:40:51 GMT]
