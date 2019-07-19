#! /usr/bin/env python3

"""
converts snap format to a simple edgelist format where the first line gives
number of vertices and edges, respectively, and the remaining lines give
endpoints of edges. Vertex numbers in the output range from 0 to n-1, where
n is the number of vertices.
The following assumptions are made about the input:
  - vertex numbers go from 1 to n
  - if a vertex number is > n, then the max vertex number is used as number of vertices
    in the output (no harm done for the oct estimator)
"""

import sys

def convert(input_filename, output_filename):
    vertices, edges = 0, 0
    with open(input_filename, 'r') as infile:
        for line in infile.readlines():
            if line.split()[0] == '#' or line.strip()[0] == '#':
                continue        # ignore comments
            vertex1, vertex2 = list(map(int, line.split()))
            vertices = max([vertices, vertex1, vertex2])
            edges += 1

    with open(input_filename, 'r') as infile:
        # Toss the first comment line
        infile.readline()
        with open(output_filename, 'w') as outfile:
            outfile.write('{} {}\n'.format(vertices, edges))
            for line in infile.readlines():
                if line.split()[0] == '#' or line.strip()[0] == '#':
                    continue	# ignore comments
                vertex1, vertex2 = list(map(int, line.split()))
                outfile.write('{} {}\n'.format(vertex1 - 1, vertex2 - 1))

if __name__ == '__main__':
    if len(sys.argv) != 3:
        print("Usage:", sys.argv[0], "INPUT_FILE OUTPUT_FILE")
        sys.exit(1)
    convert(sys.argv[1], sys.argv[2])

#  [Last modified: 2019 07 16 at 17:33:26 GMT]
