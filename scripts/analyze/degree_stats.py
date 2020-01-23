#! /usr/bin/env python3

"""
 degree_stats.py - given a graph in snap format as input, calculates a
 variety of statistics on the degree sequence
"""

import argparse
from argparse import ArgumentParser
from argparse import RawTextHelpFormatter # to allow newlines in help messages
import sys
import os
import math
import statistics

OUTPUT_PREFIX = "z_ds-"         # put degree stats files at the end of a directory list
INSTANCE_HEADER = "00-Instance" # standard header for problem instance to allow merging
VERTEX_HEADER = "n"
EDGE_HEADER = "m"
DEFAULT_STAT_LIST=["min", "bottom", "med", "mean", "top", "max", "stdev", "spread", "nad"]

def parse_arguments():
    parser = argparse.ArgumentParser(formatter_class=RawTextHelpFormatter,
                                     description="Read graphs in snap format and"
                                     + " produces degree statistics in csv format"
                                     + "\n in a file called z_ds-input_path.csv") 

    parser.add_argument("input_path", help="a file in snap format"
                        + " or a directory containing such files")
    parser.add_argument("-s", "--stats", dest="stats",
                        help="a comma separated list of statistics to print, options are:"
                        + "\n min, med, mean, max, stdev, first, third, iqrt, bottom, top, spread, nad"
                        + "\n  where first and third are the first and third quartile"
                        + ", respectively"
                        + "\n  iqrt is the interquartile ratio = (third - first) / median"
                        + "\n  top and bottom are top and bottom percentiles determined by the -p parameter"
                        + "\n  spread = lg(top / bottom) + stdev / median"
                        + "\n  and nad = 'normalized average degree'"
                        + "\n  Default is {}".format(', '.join(DEFAULT_STAT_LIST))
                        )
    parser.add_argument("-p", "--percentile", type = int, help = "percentile used to calculate top and bottom (default 5)", default = 5)
    parser.add_argument("-M", "--max_degree", dest="max_degree", type=int, default=200,
                        help="maximum degree to be used when normalizing (nad),"
                        + "\n i.e., actual average degree is mapped to [1..max_degree]"
                        + ", default is 200")
    parser.add_argument("-dt", "--degree_threshold", dest="degree_threshold",
                        type=int, default=20,
                        help="threshold below which actual average degree is used"
                        + "\n instead of normalized when normalizing (nad)"
                        + ", default is 20")
    args = parser.parse_args()
    return args

def is_comment(line):
    return line.startswith("#")

"""
@param neighbors is a map from vertices (integers) to their neighbors (sets of integers)
adds w to the set of v's neighbors, creating that set if it does no already exist
"""
def add_neighbor(neighbors, v, w):
    if not v in neighbors:
        neighbors[v] = set([w])
    else:
        neighbors[v].add(w)

"""    
@param in_stream a stream associated with an input file or stdin
@return a map that maps vertices to their sets of neighbors
"""
def read_snap(in_stream):
    neighbors = {}
    for line in in_stream:
        line = line.strip()
        tokens = line.split()
        if is_comment(line):
            continue
        elif len(tokens) > 1:
            # ignores empty lines and stuff beyond the first two tokens
            v = int(tokens[0])
            w = int(tokens[1])
            add_neighbor(neighbors, v, w)
            add_neighbor(neighbors, w, v)
    return neighbors

"""
@param neighbors is a map from vertices (integers) to their neighbors (sets of integers)
@return a list of integers representing degrees of vertices in ascending order
"""
def neighbors_to_degree_sequence(neighbors):
    if len(neighbors) == 0:
        return [0]              # so we don't get into trouble with empty graphs
    degrees = [len(neighbors[i]) for i in neighbors]
    return sorted(degrees)

"""
@return a weighted average of the elements in the data list that are at indices
floor(position) and ceiling(position)
weight depends on the difference between position and its floor or ceiling
"""
def weighted_element(data, position):
    if int(position) == position:
        # position is an integer
        return data[int(position)]
    # not an integer
    floor = int(position)
    ceiling = floor + 1
    return (ceiling - position) * data[floor] + (position - floor) * data[ceiling]

"""
@return a tuple of the form (first,median,third), where first and third
are the first and third quartiles in data
@param data a sorted list of data elements
"""
def percentiles(data, percent):
    last_index = len(data) - 1
    first_quartile_index = last_index / 4
    bottom_percentile_index = last_index * percent / 100
    top_percentile_index = last_index - last_index * percent / 100
    median_index = last_index / 2
    third_quartile_index = 3 * last_index / 4
    bottom_percentile = weighted_element(data, bottom_percentile_index)
    first_quartile = weighted_element(data, first_quartile_index)
    median = weighted_element(data, median_index)
    third_quartile = weighted_element(data, third_quartile_index)
    top_percentile = weighted_element(data, top_percentile_index)
    return bottom_percentile, first_quartile, median, third_quartile, top_percentile

"""
@return the normalized average degree, based on the command line arguments
        max_degree and degree_threshold
"""
def normalized_degree(true_average, num_vertices):
    if true_average < _threshold:
        return true_average
    else:
        return true_average * (_max_degree / num_vertices) 

"""
Writes the degree statistics specified by stat_list for a graph in snap format
@param instream input stream where the graph comes from
@param outstream where to write the output in csv format
@param instance the name of the problem instance
@param stat_list a list of strings specifying the statistics to write
"""
def write_statistics(instream, outstream, instance, stat_list):
    neighbors = read_snap(instream)
    degree_sequence = neighbors_to_degree_sequence(neighbors)
    vertices = len(degree_sequence)
    edges = sum(degree_sequence) / 2
    minimum = degree_sequence[0]
    maximum = degree_sequence[-1]
    mean = statistics.mean(degree_sequence)
    stdev = statistics.stdev(degree_sequence)
    bottom, first_quartile, median, third_quartile, top = percentiles(degree_sequence, args.percentile)
    output_list = [instance, vertices, edges]
    for stat in stat_list:
        if stat == "min":
            output_list.append(minimum)
        elif stat == "med":
            output_list.append(median)
        elif stat == "bottom":
            output_list.append(bottom)
        elif stat == "first":
            output_list.append(first_quartile)
        elif stat == "third":
            output_list.append(third_quartile)
        elif stat == "top":
            output_list.append(top)
        elif stat == "max":
            output_list.append(maximum)
        elif stat == "mean":
            output_list.append(mean)
        elif stat == "stdev":
            output_list.append(stdev)
        elif stat == "iqrt":
            output_list.append((third_quartile - first_quartile) / median)
        elif stat == "spread":
            if minimum == 0 or median == 0:
                # something's wrong
                output_list.append(-1)
            else:
                output_list.append(math.log2(top / bottom)
                                   + stdev / median)
        elif stat == "nad":
            output_list.append(normalized_degree(mean, vertices))
        else:
            print("unrecognized statistic {}".format(stat))
    output_list = [str(x) for x in output_list]
    outstream.write("{}\n".format(','.join(output_list)))

"""
@return the file name without the extension, i.e.,
        everything up to but not including the last '.',
        or the whole name if there is no '.'
        or the if the last '.' is the first character
"""
def extension_omitted(file_name):
    index = file_name.rfind('.')
    if index > 0:
        return file_name[:index]
    # index of 0 means file_name starts with the only '.', -1 means no '.'
    return file_name

"""
@return the base name of the directory, without the final '/'
"""
def directory_base(path):
    index = path.rfind('/')
    if index == len(path) - 1:
        path = path[:-1]        # remove trailing '/'
        index = path.rfind('/')
    # path ends with something other than '/' at this point
    if index < 0:
        return path             # no /
    return path[index+1:]       # there's stuff after last /

"""
write a header for the csv file: instance, vertices, edges, stats
@param header_list a string giving the comma-separated names of statitics to be included
"""
def write_header(outstream, header_list):
    outstream.write("{},{},{},{}\n".format(INSTANCE_HEADER,
                                           VERTEX_HEADER,
                                           EDGE_HEADER,
                                           ','.join(header_list)))

if __name__ == '__main__':
    global _max_degree
    global _threshold
    args = parse_arguments()
    if args.stats:
        stat_list = args.stats.split(',')
    else:
        stat_list = DEFAULT_STAT_LIST
    _max_degree = args.max_degree
    _threshold = args.degree_threshold
    if os.path.isdir(args.input_path):
        output_name = OUTPUT_PREFIX + directory_base(args.input_path) + ".csv"
        outstream = open(output_name, 'w')
        write_header(outstream, stat_list)
        for file_name in os.listdir(args.input_path):
            instream = open(args.input_path + "/" + file_name, 'r')
            basename = extension_omitted(file_name)
            print("computing statistics for", file_name)
            write_statistics(instream, outstream, basename, stat_list)
    elif os.path.isfile(args.input_path):
        basename = extension_omitted(directory_base(args.input_path))
        output_name = OUTPUT_PREFIX + basename + ".csv"
        outstream = open(output_name, 'w')
        write_header(outstream, stat_list)
        instream = open(args.input_path, 'r')
        write_statistics(instream, outstream, basename, stat_list)
    else:
        print("{} is not a file or a directory")
        
#  [Last modified: 2020 01 17 at 15:31:34 GMT]
