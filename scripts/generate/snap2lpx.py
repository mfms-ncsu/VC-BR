#! /usr/bin/env python3

"""
 lightweight script to convert a snap file to a CPLEX-readable file;
 vertices numbered 0 through the maximum vertex number are assumed to exist;
 no harm done if they don't - it simply means that
 there will be variables not involved in any constraints;
 reason for this is so that the -verify option in cplex_ilp produces a string
 of 0's and 1's that represents vertices starting at vertex 0.
"""

import argparse
import sys

# maximum number of tokens in each line of output when printing the objective
# function or the list of binary variables
TOKENS_PER_LINE = 20

def is_comment(line):
    return line.startswith("#")

# @param in_stream a stream associated with an input file or stdin
# @return comments, vertex_list, edge_list
#   where comments is a list of strings corresponding to lines that began with # in the input
#         vertex_list is a list of vertex numbers
#         edge_list is a list of pairs of vertex numbers, each corresponding to an edge
def read_snap(in_stream):
    comments = []
    max_vertex = 0
    edge_list = []
    for line in in_stream:
        line = line.strip()
        tokens = line.split()
        if is_comment(line):
            comments.append(line[1:]) # leave off the #
        elif len(tokens) > 1:
            # ignores empty lines and stuff beyond the first two tokens
            v = int(tokens[0])
            w = int(tokens[1])
            max_vertex = max(v, w, max_vertex)
            edge_list.append((v,w))
    return comments, list(range(max_vertex + 1)), edge_list

def write_lpx_comments(out_stream, comments):
    for comment in comments:
        out_stream.write("\\{}\n".format(comment))

def write_objective_function(out_stream, vertex_list):
    out_stream.write('\nMin\n   obj: ')
    count = 1
    for vertex in vertex_list:
        out_stream.write('+x_{}'.format(vertex))
        if count > 0 and count % TOKENS_PER_LINE == 0:
            count = 1
            out_stream.write('\n')
        else:
            out_stream.write(' ')
            count = count + 1
    out_stream.write('\n')

def write_constraints(out_stream, edge_list):
    out_stream.write('st\n')
    count = 1
    for edge in edge_list:
        out_stream.write("   c{}: +x_{} +x_{} >= 1\n".format(count, edge[0], edge[1]))
        count = count + 1

def write_binary_variables(out_stream, vertex_list):
    out_stream.write("Binary\n  ")
    count = 1
    for vertex in vertex_list:
        out_stream.write("x_{}".format(vertex))
        if count % TOKENS_PER_LINE == 0:
            out_stream.write('\n')
            count = 1
        else:
            out_stream.write(' ')
            count = count + 1
    out_stream.write('\n')
            
def write_end(out_stream):
    out_stream.write("End\n")
    
if __name__ == '__main__':
    comments, vertex_list, edge_list = read_snap(sys.stdin)
    write_lpx_comments(sys.stdout, comments)
    write_objective_function(sys.stdout, vertex_list)
    write_constraints(sys.stdout, edge_list)
    write_binary_variables(sys.stdout, vertex_list)
    write_end(sys.stdout)

#  [Last modified: 2019 09 17 at 21:54:29 GMT]
