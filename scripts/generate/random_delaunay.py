#! /usr/bin/env python3

"""
 creates a random Delaunay triangulation using delaunay.py to do the
 triangulation after a random set of points have been
 chosen; there is an option to triangulate the infinite face
"""

"""
if numpy is not installed you may have to do one of the following
  Ubuntu
    sudo apt install python3-pip
    pip3 install numpy
  For other Unix-based system, you may want to install anaconda python and
    pip install numpy
  Special instructions for NCSU VCL
    reserve a 'CentOS 8 base' machine (Red Hat 8)
  then do
    sudo yum install python3-pip python3-numpy
"""
import numpy
from numpy import array
import math
import sys
import os
import argparse
import random
from delaunay import Delaunay2d

def parse_arguments():
    parser = argparse.ArgumentParser(description="Creates a random Delaunay triangulation"
                                     + " and prints it in snap format on standard output.")
    parser.add_argument("-s", "--seed", type=int, help="seed for random generator;"
                        + " internal random seed if missing")
    parser.add_argument("-o", "--output", help="output file name; stdout if not given")
    parser.add_argument("-i", "--infinite_face", action='store_true',
                        help="triangulate the infinite face")
    parser.add_argument("-d", "--dual", action="store_true", help="produce the dual graph")
    parser.add_argument("-f", "--graph_format",
                        help="graph format (snap, gph); default is snap (no coordinates or edge weights); gph includes both coordinates and edge lengths",
                        default="snap")
    parser.add_argument("number_of_vertices", help="number of vertices; if --dual option is used, the actual number will be the number of faces, which is 2n-4 if --infinite_face is also used; to get N vertices in that case, you need to specify (N+4)/2", type=int)
    args = parser.parse_args()
    return args

def date():
    date_pipe = os.popen( 'date -u "+%Y/%m/%d %H:%M"' )
    return date_pipe.readlines()[0].split()[0]

def euclidian_distance(point1, point2):
    return math.sqrt((point1[0] - point2[0])**2 + (point1[1] - point2[1])**2)

def randomPoints(n):
    """
    @return a list of random points in the unit square;
            each point is an array of length 2
    """
    points = []
    for i in range(n):
        x = random.uniform(0,1)
        y = random.uniform(0,1)
        point = array([x, y])
        points.append(point)
    return points

def print_edges(file_stream, edges):
    """
    prints the edges on the file stream, one per line, a space between vertices;
    adds 1 to each vertex number to ensure no vertex 0
    """
    for edge in edges:
        file_stream.write("%d %d\n" % (edge[0] + 1, edge[1] + 1))

# @todo add an option to print in gph format with information about location
# of points, scaled to a given window size

def print_graph(file_stream, n, edges, seed):
    """
    @param file_stream an output file stream (or stdout)
    @param n number of vertices in the graph
    @param edges a set of pairs, each pair (v,w) represents an edge vw
    @param seed the random seed used to generate the graph, if any
    Prints the edges on the output stream in snap format
    with comments giving date, time, and graph parameters at the beginning
    """
    file_stream.write( "# generated by %s\n" % " ".join(sys.argv) )
    file_stream.write( "#   on %s\n" % date() )
    file_stream.write( "# vertices edges seed (-1 if none)\n" )
    if not seed:
        seed = -1
    file_stream.write( "# %d %d %d\n" % (n, len(edges), seed) )
    print_edges( file_stream, edges )

def print_gph(out_stream, points, edges, seed):
    """
    prints the graph in gph format, giving coordinates of the vertices (points),
    and lengths of the edges (Euclidian distance)
    gph format is as follows:
        c comment line 1
        ...
        c comment line k

        g number_of_nodes number_of_edges
        n v_1 x_1 y_1
        ...
        n v_n x_n y_n
        e source_1 target_1 weight_1
        ...
        e source_m target_m weight_m

    v_1 through v_n are node numbers, typically 1 through n
    x_i, y_i are x and y coordinates of v_i
    source_i and target_i are endpoints of edges, and weight_i are the weights
    """
    print_gph_preamble(out_stream, len(points), len(edges), seed)
    print_gph_nodes(out_stream, points)
    print_gph_edges(out_stream, points, edges)

def print_gph_preamble(out_stream, n, m, seed):
    out_stream.write( "c generated by %s\n" % " ".join(sys.argv) )
    out_stream.write( "c   on %s\n" % date() )
    out_stream.write( "c vertices edges seed (-1 if none)\n" )
    if not seed:
        seed = -1
    out_stream.write( "c %d %d %d\n" % (n, len(edges), seed) )
    out_stream.write( "g %d %d\n" % (n, m))

def scale(number):
    """@return an integer version of the number; requires a large scale factor
               to account for the fact that number is in the interval (0,1)
    """
    SCALE_FACTOR = 1000000
    return int(SCALE_FACTOR * number) + 1

def print_gph_nodes(out_stream, points):
    for node_id in range(len(points)):
        out_stream.write("n {} {} {}\n".format(node_id + 1,
                                               scale(points[node_id][0]),
                                               scale(points[node_id][1])))
                         
def print_gph_edges(out_stream, points, edges):
    for edge in edges:
        source = edge[0]
        target = edge[1]
        weight = euclidian_distance(points[source], points[target])
        out_stream.write("e {} {} {}\n".format(source + 1, target + 1, scale(weight)))

if __name__ == '__main__':
    args = parse_arguments()
    seed = args.seed
    random.seed(seed)
    n = args.number_of_vertices
    points = randomPoints(n)
    delaunay = Delaunay2d(points)
    if args.infinite_face:
        delaunay.triangulateInfiniteFace()
    if args.dual:
        delaunay.computeDual()
        points = delaunay.getDualPoints()
        edges = delaunay.getDualEdges()
    else:
        points = delaunay.getPoints()
        edges = delaunay.getEdges()
    if args.output:
        out_stream = open(args.output, 'w')
    else:
        out_stream = sys.stdout
    if args.graph_format == "snap":
        print_graph(out_stream, n, edges, seed)
    elif args.graph_format == "gph":
        print_gph(out_stream, points, edges, seed)
    else:
        print("unknown graph format", args.graph_format)
        
#  [Last modified: 2021 06 01 at 19:53:49 GMT]
