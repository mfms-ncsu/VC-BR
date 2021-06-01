#! /usr/bin/env python3
import argparse
import random
from time import gmtime, strftime
import numpy as np
from common_utils import split_file_parts, create_file_name

def read_matrix(f):
    with open(f,'r') as m_file:
        M = []
        for line in m_file:
            row = [float(i) for i in line.strip().split()]
            M.append(row)
    return np.triu(np.array(M))

def expected_edges(M, block_size):
    """
    Given a stochastic block matrix, compute the expected number of edges
    """
    M_sum = 0.0
    for index, p in np.ndenumerate(M):
        i,j = index
        # don't do self loops
        if i==j:
            M_sum += p*block_size*(block_size-1)/2
        else:
            M_sum += p*block_size*block_size
    return M_sum

def scale_matrix(n, mu, M):
    """
    Scale probability matrix M so there are mu*n/2 edges in expectation
    """
    num_blocks = len(M)
    block_size = n/num_blocks
    # compute the expected number of edges
    expected_old = expected_edges(M,block_size)
    # scale matrix so expected number of edges is mu*n/2
    scale_factor = (mu*n/2)/expected_old
    return scale_factor*M
        


def generate_graph(n, mu, M):
    """
    Generate a stochastic block graph
    n:  number of vertices
    mu:  average degree
    M:  probability matrix
    """
    E = set()
    # find the number of blocks
    num_blocks = len(M)
    block_size = n/num_blocks
    # convert vertex id to block number
    block_num = lambda x:x/block_size

    # scale matrix to match mu
    M_scaled = scale_matrix(n, mu, M)
    # iterate through all possible edges
    for v in range(1, n+1):     # avoid vertex number 0
        v_block = block_num(v)
        for u in range(v+1,n+1):
            u_block = block_num(u)
            # flip coin for edge
            p = M_scaled[v_block-1][u_block-1] # -1 to adjust to 0-based
            flip = random.random()
            if flip < p:
                E.add((u,v))
    return E


if __name__=="__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("size", help="size in log2", type=int)
    parser.add_argument("matrix", help="file of probability matrix", type=str)
    parser.add_argument("mu", help="average degree", type=int)
    parser.add_argument("output", help="output file name", type=str)
    parser.add_argument("repetitions", help="number of times to run generator ", type=int)

    args = parser.parse_args()

    size = 2**args.size
    mu = args.mu
    matrix = read_matrix(args.matrix)
    filename = args.output
    reps = args.repetitions
   
    prefix,ext = split_file_parts(filename)

    for i in range(reps):
        edges = generate_graph(size, mu, matrix)

        with open(create_file_name(prefix, args.size, i, ext),'w') as output_file:
            output_file.write("# cluster graph with {} clusters, {} vertices, {} edges\n"
                              .format(len(matrix), size, len(edges)))
            output_file.write("# created by {}\n".format(" ".join(sys.args)))
            date_and_time_string = strftime("%Y-%m-%d %X", gmtime())
            output_file.write("# created {}\n".format(date_and_time_string))
            for u,v in edges:
                output_file.write("{} {}\n".format(u,v))
            output_file.close()

#  [Last modified: 2021 06 01 at 19:02:55 GMT]
