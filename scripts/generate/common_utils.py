#!/usr/bin/env python3
#import networkx as nx

def split_file_parts(name):
    last_dot_pos = name.rfind('.')
    if last_dot_pos == -1:      # no '.'
        file_prefix = name
        file_suffix =""
    else:
        file_prefix = name[:last_dot_pos]
        file_suffix = name[last_dot_pos:]
    return file_prefix,file_suffix

def create_file_name(prefix, size, i, suffix):
    return "{}-{}-{}{}".format(prefix, size, i, suffix)

# def cleanup(G):
#     zero_degree = []
#     for v in G:
#         if G.degree(v) == 0:
#             zero_degree.append(v)
#     G.remove_nodes_from(zero_degree)
#     G = nx.convert_node_labels_to_integers(G)
#     return

#  [Last modified: 2018 03 29 at 18:10:47 GMT]
