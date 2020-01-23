#! /usr/bin/env python3

"""
wcg_gen.py - generates dense graphs with small vertex covers by expanding a construction
             that shows the greedy heuristic to have arbitrarily bad approximation ratio
"""

from argparse import ArgumentParser
from argparse import RawTextHelpFormatter # to allow newlines in help messages
import sys
import os
import math
import random

def date():
    date_pipe = os.popen( 'date -u "+%Y/%m/%d %H:%M"' )
    return date_pipe.readlines()[0].split()[0]

def parse_arguments():
    parser = ArgumentParser(formatter_class=RawTextHelpFormatter,
                                     description =
                                     "Generates graphs based on worst-case examples for a greedy heuristic;"
                                     + "\n multiplicity has to be > 1 to consistently get the bad behavior,"
                                     + "\n and min cover size must be core * multiplicity - see below."
    )
    parser.add_argument("core", type = int,
                        help = "number of cover vertices in the original construction")
    parser.add_argument("multiplicity", type = int,
                        help = "number of copies of the core;"
                        + "\n if '-e n [or c]' and '-r x,0',"
                        + "\n   min cover has size core * multiplicity")
    parser.add_argument("-r", "--random", help = "number of random non-bipartite edges"
                        + " to add,\n in addition to any cycle edges (see -e)"
                        + "\n format is 'c,u' where c is the number on the cover side"
                        + "\n                   and u the number on the other side"
                        )
    parser.add_argument("-s", "--seed", type=int, help="seed for random generator;"
                        + " internal random seed if missing")
    parser.add_argument("-e", "--extra", help = "where to put extra cycle edges;"
                        + "\n 'n' = neither side (bipartite graph, default)"
                        + "\n 'c' = cover side,"
                        + "\n 'u' = other side,"
                        + "\n 'b' = both sides",
                        default = 'n')
    parser.add_argument("-o", "--output", help = "output file name (stdout if not given);"
                        + "\na standardized name if '_' (underscore)"
                        + "\n standardized name has form wcg-xy_ttt_mm_eeee_ss.snap"
                        + "\n where x is 'c' (cycle) or 'r' (random)"
                        + "\n       y is the '-e' option"
                        + "\n       ttt is the number of vertices in the core"
                        + "\n       mm is the multiplicity"
                        + "\n       eeee is the number of extra edges (num vertices if cycle)"
                        + "\n       ss is the random seed (omitted in case of cycle)"
    )
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

"""
Two sets keep track of edges already added among edges in the cover
and among edges not in the cover; making these global allows for
random edge *in addition to* cycle edges
"""
_cover_side_edges = set()
_other_side_edges = set()

def init_vertices():
    """
    initialize the two data structures so that they have entries for the vertices:
    numbers can be assigned directly
    all adjacency lists are originally empty sets
    """
    n = 0                       # number of vertices so far, also used to number vertices
    # first the W vertices
    for k in range(1, _args.core + 1):
        for ell in range(0, _args.multiplicity):
            n += 1
            _vertex_number[(1,k,ell)] = n
            _adj_list[(1,k,ell)] = set()
    # then the U_i vertices
    for i in range(1, _args.core + 1):
        for j in range(1, _args.core // i + 1):
            n += 1
            _vertex_number[(0,i,j)] = n
            _adj_list[(0,i,j)] = set()

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
    num_edges = 0
    for i in range(1, _args.core + 1):
        for j in range(1, _args.core // i + 1):
            for k in range(1, _args.core + 1):
                for ell in range(0, _args.multiplicity):
                    if math.ceil(k / i) == j:
                        num_edges += 1
                        add_edge((0,i,j), (1,k,ell))
    return num_edges

def add_random_cover_side_edges(number_desired):
    """
    adds random edges between vertices in the original min cover
    """
    global _cover_side_edges
    number_added = 0
    while number_added < number_desired:
        ell_1 = random.choice(range(0, _args.multiplicity))
        ell_2 = random.choice(range(0, _args.multiplicity))
        k_1 = random.choice(range(1, _args.core + 1))
        k_2 = random.choice(range(1, _args.core + 1))
        if k_1 == k_2 and ell_1 == ell_2: continue
        if ((k_1,ell_1), (k_2,ell_2)) in _cover_side_edges: continue
        if ((k_2,ell_2), (k_1,ell_1)) in _cover_side_edges: continue
        add_edge((1,k_1,ell_1), (1,k_2,ell_2))
        number_added += 1
        _cover_side_edges.add(((k_1,ell_1), (k_2,ell_2)))
    return number_added

def add_random_other_side_edges(number_desired):
    """
    adds random edges between vertices on the side opposite the original min cover
    """
    global _other_side_edges
    number_added = 0
    while number_added < number_desired:
        i_1 = random.choice(range(1, _args.core + 1))
        i_2 = random.choice(range(1, _args.core + 1))
        j_1 = random.choice(range(1, _args.core // i_1 + 1))
        j_2 = random.choice(range(1, _args.core // i_2 + 1))
        if i_1 == i_2 and j_1 == j_2: continue
        if ((i_1,j_1), (i_2,j_2)) in _other_side_edges: continue
        if ((i_2,j_2), (i_1,j_1)) in _other_side_edges: continue
        add_edge((0,i_1,j_1), (0,i_2,j_2))
        number_added += 1
        _other_side_edges.add(((i_1,j_1), (i_2,j_2)))
    return number_added

def add_cover_cycle_edges():
    """
    creates a cycle that includes all vertices in the min cover
    """
    number_added = 0
    for ell in range(0, _args.multiplicity):
        for k in range(1, _args.core):
            number_added += 1
            add_edge((1,k,ell), (1,k+1,ell))
            _cover_side_edges.add(((k,ell), (k+1,ell)))
        number_added += 1
        add_edge((1,_args.core,ell), (1,1,(ell+1)%_args.multiplicity))
        _cover_side_edges.add(((_args.core,ell), (1,(ell+1)%_args.multiplicity)))
    return number_added
    
def add_other_cycle_edges():
    """
    creates a cycle that includes all vertices on the side opposite the min cover
    """
    number_added = 0
    for i in range(1, _args.core + 1):
        for j in range(1, _args.core // i):
            number_added += 1
            add_edge((0,i,j), (0,i,j+1))
            _other_side_edges.add(((i,j), (i,j+1)))
        number_added += 1
        add_edge((0,i,_args.core//i), (0,i%_args.core+1,1))
        _other_side_edges.add(((i,_args.core//i), (i%_args.core+1,1)))

def output_comments(out_stream):
    out_stream.write("# generated by wcg_gen.py {} {}, in repository VC-BR/scripts/generate,".format(_args.core, _args.multiplicity))
    out_stream.write(" {}\n".format(date()))
    out_stream.write("#  -e = {}; -r = {}; -s = {}\n".format(_args.extra, _args.random, _args.seed))

def output_edges(out_stream, vertex):
    """
    writes edges incident to the vertex in snap format
    """
    for neighbor in _adj_list[vertex]:
        out_stream.write("{} {}\n".format(_vertex_number[vertex],
                                          _vertex_number[neighbor]))

def output_snap(out_stream):
    output_comments(out_stream)
    for i in range(1, _args.core + 1):
        for j in range(1, _args.core // i + 1):
            output_edges(out_stream, (0,i,j))
    for k in range(1, _args.core + 1):
        for ell in range(0, _args.multiplicity):
            output_edges(out_stream, (1,k,ell))

def get_num_other_vertices(num_core):
    """
    @return number of U vertices, those on side opposite the core;
    brute force - there is probably a closed form but it could be complicated
    """
    number = 0
    for i in range(1, _args.core + 1):
        for j in range(1, _args.core // i + 1):
            number = number + 1
    return number

if __name__ == '__main__':
    global _args
    _args = parse_arguments()
    if _args.random and _args.seed:
        random.seed(int(_args.seed))
    init_vertices()
    num_bipartite_edges = add_bipartite_edges()
    num_extra_edges = 0
    if _args.extra == 'b' or _args.extra == 'c':
        num_extra_edges = add_cover_cycle_edges()
    if _args.extra == 'b' or _args.extra == 'u':
        num_extra_edges += add_other_cycle_edges()
    if _args.random:
        # compute maximum number of possible edges on each side and use that
        # to figure out whether user requested too many
        num_cover_vertices = _args.core * _args.multiplicity
        max_cover_edges = (num_cover_vertices * (num_cover_vertices - 1)) // 2
        num_other_vertices = get_num_other_vertices(_args.core)
        max_other_edges = (num_other_vertices * (num_other_vertices - 1)) // 2

        num_edge_list = _args.random.strip().split(',')
        num_random_cover_edges = int(num_edge_list[0])
        num_random_other_edges = int(num_edge_list[1])

        possible_cover_edges = max_cover_edges - len(_cover_side_edges)
        if num_random_cover_edges > possible_cover_edges:
            sys.stderr.write("*** Warning: requested too many random cover side edges\n")
            sys.stderr.write("*** requested = {}, possible = {}, resorting to possible\n"
                             .format(num_random_cover_edges, possible_cover_edges))
            num_random_cover_edges = possible_cover_edges
        num_extra_edges += add_random_cover_side_edges(num_random_cover_edges)
        
        possible_other_edges = max_other_edges - len(_other_side_edges)
        if num_random_other_edges > possible_other_edges:
            sys.stderr.write("*** Warning: requested too many random other side edges\n")
            sys.stderr.write("*** requested = {}, possible = {}, resorting to possible\n"
                             .format(num_random_other_edges, possible_other_edges))
            num_random_other_edges = possible_other_edges
        num_extra_edges += add_random_other_side_edges(num_random_other_edges)

    if _args.output:
        if _args.output == '_':
            seed_string = ""
            if _args.random:
                type_flag = 'r'
                seed_string = "_xx"
                if _args.seed:
                    seed_string = "_%02d" % _args.seed
            else:
                type_flag = 'c'
            filename = "wcg-%c%c_%03d_%02d_%04d%s.snap" %\
                       (type_flag, _args.extra, _args.core, _args.multiplicity,
                        num_extra_edges, seed_string)
            out_stream = open(filename, "w")
            output_snap(out_stream)
        else:
            output_snap(sys.stdout)

#  [Last modified: 2020 01 17 at 15:14:20 GMT]
