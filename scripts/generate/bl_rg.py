#! /usr/bin/env python3

"""
bl_rg.py - (bucket-list random graph) generates graphs with a specified degree variance,
           minimum degree and maximum degree
           uses a list of buckets, each bucket storing vertices of the same degree
           a graph is printed to standard output in snap format

@author Matt Stallmann
@date 2018/7/18
"""

"""
@todo The file name created with the -of option should be a better reflection
of reality. For example, a -dv 0 does not guarantee a regular graph; you
also need the right -md and -MD settings, and those alone might work.

@todo The -dv option is finicky as far as controlling real degree
distribution is concerned. Often, it takes many tries with different -dv,
-md, and -MD settings to get what you want and the three options interact in
unpredictable ways. Probably not an easy fix.

@todo one "feature" that tends to create uneven distribution is the current notion of desparate vertices; the *right* way to handle this is not to make vertices desparate until the number of remaining edges is just enough to accommodate vertices whose degree is less than minimum; worth a try anyhow

@todo should have a -uniform option which allows random choice of vertices instead of choosing a bucket first; idea would be to concatenate the buckets and then choose a vertex at random; do this after desparate vertices are taken care of; might even try this with different -dv settings, i.e., concatenate a subset of the buckets based on the usual random bucket choice mechanism
"""

"""
The algorithm (outline) is as follows. Each random vertex chosen is subject
to priorities detailed at the end of the description.

First create a random spanning tree by running a randomized Prim's algorithm.
   pick an arbitrary start vertex $s$ and add it to $T$
   for every other vertex $u$, do
      pick a random $w \in T$ and add edge $uw$, putting $u$ in $T$
      
Then,
    until the desired average degree is achieved, do
      choose a random vertex $u$
      choose a random vertex $w \neq u$ that is not already a neighbor of $u$
      add edge $uw$

Priorities: [if not specified by user, min_deg = 1 and max_deg = n-1]
  - if there is a vertex with degree less than min_deg, choose among such vertices
  - eliminate vertices with degree = max_degree from consideration
  - given that vertices of degrees $d_0 < \ldots < d_{k-1}$ exist,
       choose degree $d_i$ as follows ($dv =$ deg_variance, $r$ is random in [0,1])
      .. if $dv = 0$, choose $d_1$
      .. if $dv \leq 1$, choose $d_i$,
           where $i = dv \times r \times k$
           dv = 0 is a special case; dv = 1 means choice is uniformly distributed
      .. if $dv > 1$, use python's random.expovariate() to get $r$ and let
           $i = (1 - r) \times k$, truncated if this is $<0$ or $>k-1$
           this should yield an exponential distribution
           in practice, you end up with a lot of max_deg vertices
"""

import sys
import os
import random
import argparse
import statistics
import functools

DEBUG = False

def debug_print(format_string, tuple_of_values):
    """
    @param format_string a format string using %d, %f, %s, etc. (no {}'s)
    """
    if DEBUG:
        sys.stderr.write(format_string % tuple_of_values)

def date():
    date_pipe = os.popen( 'date -u "+%Y/%m/%d %H:%M"' )
    return date_pipe.readlines()[0].split()[0]

def parse_arguments():
    parser = argparse.ArgumentParser(
        description = "Creates a random (connected) graph following, as much as possible, the specifications supplied by the user; graph is printed in snap format on standard output",
        epilog = "min_deg and max_deg will impact the effect of deg_variance"
    )
    parser.add_argument("vertices", help = "number of vertices", type = int)
    parser.add_argument("average_degree",
                        help = "average degree - number of edges is vertices * this / 2; restricted to be integer",
                        type = int)
    parser.add_argument("-s", "--seed",
                        help = "random seed (default is based on internal system state)",
                        type = int)
    parser.add_argument("-dv", "--deg_variance",
                        help = "desired degree variance, 0 means regular, 1 means distribution is roughly uniform, > 1 means roughly power law", type=float, default = 1)
    parser.add_argument("-md", "--min_deg",
                        help = "miminum degree of a vertex",
                        type = int)
    parser.add_argument("-MD", "--max_deg",
                        help = "maximum degree of a vertex",
                        type = int)
    parser.add_argument("-o", "--output", help = "send output to file with given name")
    parser.add_argument("-of", "--output_file", action='store_true',
                        help = "sends output to a file with a standardized name of the form blg-vertices_density_dv_md'D'MD_s.txt")
    args = parser.parse_args()
    return args

###############################################
# a quick an dirty graph implementation
#  - simply a set of neighbors for each vertex
###############################################

def init_graph():
    global _neighbors
    _neighbors = [set() for x in range(_num_vertices)]

def add_edge(v, w):
    debug_print("add_edge: %d %d\n", (v, w))
    _neighbors[v].add(w)
    _neighbors[w].add(v)
    increment_degree(v)
    increment_degree(w)

###############################################
# The degree bucket data structure is the key to controlling degree
# distributions. Here, _bucket_list[k] is a set that stores nodes whose
# degree is k and _degree[vertex] stores the index of the bucket containing
# the vertex, i.e., its degree.
#
# When degree variance is small, vertices in buckets with small indices are
# given preference. If degree variance is 1.0 all vertices are treated
# equally. If dv is greater than 1, a value x is chosen from an exponential
# distribution with mean 1/dv and the bucket at (relative) position 1-x is
# chosen from the list of available (nonempty) buckets
#
# @todo Obviously this should be a class, but the current implementation is
# meant to be quick and dirty
###############################################

def init_buckets():
    """
    puts each vertex into a bucket corresponding to degree 0
    """
    global _bucket_list
    global _degree
    global highest_bucket_index
    _bucket_list = [set([x for x in range(_num_vertices)])]
    _degree = [0] * _num_vertices
    highest_bucket_index = 0

def increment_degree(vertex):
    """
    moves the vertex into the next higher bucket to reflect the fact that its
    degree has increased
    """
    global _bucket_list
    global _degree
    global highest_bucket_index
    k = _degree[vertex]
    if k == _num_vertices - 1:
        # already adjacent to every other vertex, so no longer relevant,
        # should have been filtered by now
        print("unable to increment degree on vertex {}, already max".format(vertex))
        sys.exit()
    _bucket_list[k].remove(vertex)
    if highest_bucket_index == k:
        _bucket_list.append(set())
        highest_bucket_index = highest_bucket_index + 1
    _bucket_list[k+1].add(vertex)
    _degree[vertex] = k + 1

def choose_random_bucket(buckets_to_choose_from, degree_var):
    """
    @return a random bucket from a (filtered) list of buckets; the bucket
    chosen is based on a mapping from the unit interval to the range of indices
    of buckets_to_choose_from; degree_var determines the bias in the choice:
    0 => favor nodes of lowest current degree
    0 < dv < 1 => normal distribution with increasing stdev
    1 => treat all nodes equally
    > 1 => exponential distribution with increasing tail
    """
    debug_print("-> choose_random_bucket: %s, %f\n", (buckets_to_choose_from, degree_var))
    if buckets_to_choose_from == []:
        return []
    
    # this variation is based on the original version of createRandomLayeredGraph
    # uniform_number = random.random()
    # choice_index = int(uniform_number * degree_var * len(buckets_to_choose_from))

    if degree_var <= 1:
        uniform_number = random.random()
        choice_index = int(uniform_number * degree_var * len(buckets_to_choose_from))
    else:
        random_exp = random.expovariate(degree_var)
        choice_index = int((1 - random_exp) * len(buckets_to_choose_from))
    choice_index = min(choice_index, len(buckets_to_choose_from) - 1)
    choice_index = max(choice_index, 0)
    return buckets_to_choose_from[choice_index]

def get_available_vertices():
    """
    @return a list of vertices that have degree < n - 1 or the maximum
    degree, if one has been specified, where n = # of vertices
    """
    maximum_allowed_degree = _num_vertices - 1
    if _max_degree:
        maximum_allowed_degree = min(_max_degree, maximum_allowed_degree)
    return [x for x in range(_num_vertices) if _degree[x] < maximum_allowed_degree]

def get_available_neighbors(v):
    """
    @return a list of vertices that have degree < n - 1 or the maximum
    degree, if one has been specified, where n = # of vertices,
    with the additional condition that none of the vertices are v
    or current neighbors of v
    """
    potential_neighbors = [x for x in range(_num_vertices) if x != v
                           and x not in _neighbors[v]]
    if _max_degree:
        trial_neighbors = [x for x in potential_neighbors if _degree[x] < _max_degree]
        if trial_neighbors != []:
            potential_neighbors = trial_neighbors
        else:
            sys.stderr.write("*** warning: need to exceed max degree for vertex {}\n"
                             .format(v))
    return potential_neighbors

def filter_buckets(vertex_choices):
    """
    @return a list of buckets such that each bucket contains at least one
    vertex in the set vertex_choices
    """
    bucket_choices = [bucket & vertex_choices for bucket in _bucket_list]
    return [bucket for bucket in bucket_choices if bucket != set()]
    
def random_vertex(degree_var, choices):
    """
    @return a random vertex chosen 
    @param degree_var guides the choice as follows 
    choose one whose degree is currently small if degree_var < 1, no particular
    preference if degree_var = 1, and one with large degree if
    degree_var > 1
    @param choices a nonempty set of possible vertices
    """
    if _min_degree:
        desparate = functools.reduce(lambda x,y: x.union(y),
                                     _bucket_list[:_min_degree])
        debug_print("vertex: desparate = %s\n", desparate)
        desparate = desparate & choices
        if desparate != set():
            return random.choice(list(desparate))
    debug_print("vertex_choices = %s\n", choices)
    bucket_choices = filter_buckets(choices)
    the_bucket = choose_random_bucket(bucket_choices, degree_var)
    return random.choice(list(the_bucket))

def choose_random_vertex(degree_var):
    return random_vertex(degree_var, set(get_available_vertices()))

def choose_random_neighbor(v, degree_var):
    return random_vertex(degree_var, set(get_available_neighbors(v)))

def random_spanning_tree(degree_var):
    """
    chooses a random neighbor in the existing tree for each vertex to be added
    """
    for v in range(1, _num_vertices):
        choices = [w for w in range(v)]
        if _max_degree:
            choices = [w for w in choices if _degree[w] < _max_degree]
        w = random_vertex(degree_var, set(choices))
        add_edge(v,w)
    
def random_graph(degree_var):
    random_spanning_tree(degree_var)
    # add m - n + 1 edges where n = # of vertices and m = # of desired edges
    for i in range(_num_vertices - 1, _num_edges):
        v = choose_random_vertex(degree_var)
        w = choose_random_neighbor(v, degree_var)
        add_edge(v, w)

def write_preamble(file_stream, degree_var, seed):
    file_stream.write("# random_dv n = {} m = {} dv = {} seed = {}\n".format(_num_vertices,
                                                                             _num_edges,
                                                                             degree_var,
                                                                             seed))
    degree_list = [len(x) for x in _neighbors]
    min_deg = min(degree_list)
    max_deg = max(degree_list)
    median_deg = statistics.median(degree_list)
    mean_deg = statistics.mean(degree_list)
    # the following is not the true variance, as defined by statisticians,
    # but it's used in the thesis
    deviation = statistics.stdev(degree_list, mean_deg)
    dv = deviation / mean_deg
    file_stream.write('# degree stats\tmin\tmedian\tmean\tmax\tstdev\tdv\n')
    file_stream.write('#DEGREE_STATS \t{}\t{}\t{}\t{}\t{:5.2f}\t{:5.2f}\n'.format(min_deg, median_deg,
                                                              mean_deg, max_deg,
                                                                        deviation, dv))
def write_graph(file_stream):
    """
    writes the graph in snap format on the file stream
    vertex numbers start at 1 in the output, although at 0 internally
    edges are printed with lower numbered vertex first
    """
    for v in range(_num_vertices):
        for w in _neighbors[v]:
            if v < w:
                file_stream.write('{} {}\n'.format(v + 1, w + 1))
        
def convert_float_to_string(z):
    """
    @return a string of the form XpY from the floating point number z = X.Y...
            assumption is that Y is a single digit
    """
    X = int(z)                  # integer part
    Y = int((z - X) * 10)       # fractional part
    return "{:02d}p{:1d}".format(X, Y)

def standard_name(degree_var, seed):
    """
    @return a string of the form blg-n_{m/n}_dv_{md}D{MD}_s.txt,
            where n, m = number of vertices and edges, respectively,
            and dv, md, MD, and s are the arguments provided
    """
    # convert degree variance to a string
    dv = int(degree_var)
    if dv == degree_var:
        # integer
        dv = "{:02d}".format(dv)
    else:
        # not integer
        dv = convert_float_to_string(degree_var)
    # give default values for arguments that have none and are not specified
    if seed:
        seed_str = "{:02d}".format(seed)
    else:
        seed_str = "xx"
    return "blg-{:04d}_{:03d}_{}_{:02d}D{:04d}_{}.snap".format(_num_vertices,
                                                              _avg_deg, dv,
                                                              _min_degree, _max_degree,
                                                              seed_str)

if __name__ == "__main__":
    global _num_vertices
    global _num_edges
    args = parse_arguments()
    _num_vertices = args.vertices
    _avg_deg = args.average_degree
    _num_edges = int(_avg_deg * _num_vertices / 2)
    if _avg_deg < 2:
        print("average_degree is too small, min is 2")
        sys.exit()
    max_avg_deg = _num_vertices - 1
    if _avg_deg > max_avg_deg:
        print("average_degree is too large, max is {}"
              .format(max_avg_deg))
        sys.exit()
    _min_degree = args.min_deg
    if not _min_degree:
        _min_degree = 1
    _max_degree = args.max_deg
    if not _max_degree:
        _max_degree = _num_vertices - 1 
    average_degree = 2 * _num_edges / _num_vertices
    if _min_degree and _min_degree > average_degree:
        print("Min degree too large for number of edges, should be at most {}"
              .format(average_degree))
        sys.exit()
    if _max_degree and _max_degree < average_degree:
        print("Max degree too small for number of edges, should be at least {}"
              .format(average_degree))
        sys.exit()
    degree_var = args.deg_variance
    seed = args.seed
    random.seed(seed)
    init_graph()
    init_buckets()
    random_graph(degree_var)
    file_stream = sys.stdout
    if args.output:
        file_stream = open(args.output, 'w')
    elif args.output_file:
        file_stream = open(standard_name(degree_var, seed), 'w')
    write_preamble(file_stream, degree_var, seed)
    write_graph(file_stream)
    debug_print("%s\n", sorted([len(x) for x in _neighbors]))

#  [Last modified: 2019 09 17 at 21:55:04 GMT]
