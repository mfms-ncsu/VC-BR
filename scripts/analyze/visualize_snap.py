#!/usr/bin/env python3

"""
Visualizes SNAP-formatted graph files by using Graphviz.

Requirements:
  Python 3.5 or later
  GraphViz 2.16 or later
    see http://www.graphviz.org/
  NetworkX
  PyGraphviz

Author: Yosuke Mizutani

Usage: visualize_snap.py [-h] [-p {neato,dot,twopi,circo,fdp}]
                         [--out-dir OUT_DIR]
                         path [path ...]

Visualize a SNAP-formatted graph file.

positional arguments:
  path                  Path of a graph file

optional arguments:
  -h, --help            show this help message and exit
  -p {neato,dot,twopi,circo,fdp}, --prog {neato,dot,twopi,circo,fdp}
                        graphviz layout program
  --out-dir OUT_DIR     output directory
"""

import sys
import os
import argparse

try:
    import networkx as nx
    from pygraphviz import AGraph
except ImportError:
    sys.stderr.writelines([
        "Failed to import modules'\n",
        'Please run: pip3 install networkx pygraphviz\n',
    ])
    sys.exit(1)

# argument parser
parser = argparse.ArgumentParser(description='Visualizes SNAP-formatted graph files by using Graphviz.')
parser.add_argument('path', nargs='+', help='Path of a graph file')
parser.add_argument('-p', '--prog', default='neato', choices=['neato', 'dot', 'twopi', 'circo', 'fdp'],
                    help='graphviz layout program')
parser.add_argument('--out-dir', default='.image', help='output directory')


def loadSnap(path):
    """Loads one SNAP file."""
    edges = []
    with open(path) as f:
        for line in f:
            tokens = line.strip().split()
            if not tokens or tokens[0][0] == '#':  # skip comments
                continue
            if len(tokens) == 2 and all(s.isdigit() for s in tokens):
                edges += [(tokens[0], tokens[1])]
    return edges


def main(args):
    """Entry point of the program."""
    for inputPath in args.path:
        outputPath = os.path.join(args.out_dir, '%s.png' % os.path.basename(inputPath))
        if not os.path.isdir(args.out_dir):
            print('Creating directory: %s' % args.out_dir)
            os.makedirs(args.out_dir)

        G = AGraph()
        G.node_attr['shape'] = 'circle'
        G.node_attr['style'] = 'filled'
        G.node_attr['fillcolor'] = '#f0f0f0'

        print('Loading: %s' % inputPath)
        G.add_edges_from(loadSnap(inputPath))

        print('Writing: %s' % outputPath)
        G.draw(outputPath, prog=args.prog)

        # open file on Mac
        if sys.platform == 'darwin':
            import subprocess
            print('Opening: %s' % outputPath)
            subprocess.run(['/usr/bin/open', outputPath])


if __name__ == '__main__':
    main(parser.parse_args())
