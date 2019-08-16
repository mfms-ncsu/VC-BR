#! /usr/bin/env python3

"""
A preprocessor for csv2latex. Takes a file with an instance in each row
and a configuration for each column.
Produces output where competitive runtimes are shown in bold and
those within some threshold of the minimum are in bold italics.
The last output column lists configs that are within the threshold.
"""

BOLD = '!'
COMPETITIVE_MARKER = '!'
THRESHOLD_MARKER = '*'
THRESHOLD = 1.1
COMPETITIVE = 2
SEPARATOR = ';'                 # need something other than comma to separate
                                # items in threshold list

import argparse
import sys

def parse_arguments():
    parser = argparse.ArgumentParser(description = "A preprocessor for csv2latex."
                                     + " Takes a file with an instance in each row"
+ " and a configuration for each column."
+ " Produces output where competitive runtimes are shown in bold and"
+ " those within some threshold of the minimum are in italics as well."
+ " The last output column lists configs that are within the threshold.")
    parser.add_argument("input_file", help = "a csv file")
    parser.add_argument("-o", "--output", help = "output file, prints to stdout if none given")
    args = parser.parse_args()
    return args
                                     
def add_format_marker(value, minimum):
    """
    @return value preceded by a formatting marker consistent with csv2latex
     ! -> \textbf{} (competitive)
     * -> \textbf{\emph{}} (within threshold)
    """
    if value / minimum <= THRESHOLD:
        return THRESHOLD_MARKER + str(value)
    elif value / minimum <= COMPETITIVE:
        return COMPETITIVE_MARKER + str(value)
    return str(value)

def process_header(header_line, out_stream):
    """
    @return a list consisting of all tokens in the header_line except the first;
            this can be used as a reference - these are names of configs
    output the header_line
    """
    token_list = [token.strip() for token in header_line.split(',')]
    header_list = token_list
    header_list.append("min")
    header_list.append("configs")
    out_stream.write(','.join(header_list) + '\n')
    return token_list[1:]

def process_row(row, out_stream):
    """
    output the row with appropriate tag on each entry and an extra column
    for the configs that are within threshold (based on _global_configs)
    """
    token_list = [token.strip() for token in row.split(',')]
    instance_name = token_list[0]
    value_list = [float(token) for token in token_list[1:]]
    output_list = [instance_name]
    threshold_list = []
    minimum = min(value_list)
    for value, i in zip(value_list, range(len(value_list))):
        marked_value = add_format_marker(value, minimum)
        if marked_value[0] == THRESHOLD_MARKER:
            threshold_list.append(_global_configs[i])
        output_list.append(marked_value)
    output_list.append(str(minimum))
    output_list.append(SEPARATOR.join(threshold_list))
    out_stream.write(','.join(output_list) + '\n')
    
def highlight_competitive(in_stream, out_stream):
    """
    @see help message
    """
    global _global_configs
    _global_configs = process_header(in_stream.readline(), out_stream)
    for line in in_stream.readlines():
        process_row(line, out_stream)

if __name__ == '__main__':
    args = parse_arguments()
    in_stream = open(args.input_file, "r")
    if args.output:
        out_stream = open(args.output, "w")
    else:
        out_stream = sys.stdout
    highlight_competitive(in_stream, out_stream)

#  [Last modified: 2019 08 11 at 20:55:00 GMT]
