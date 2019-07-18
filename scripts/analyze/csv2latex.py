#! /usr/bin/env python3

"""
Simple conversion from a csv file to &-separated fields suitable for latex tables.
A few features, such as markers for bold, italic, and bold-italic text (!,+,*)
and comma separation for large integers
"""

import argparse
import sys

def parse_arguments():
    parser = argparse.ArgumentParser(description = "converts csv to latex tabular format"
                                     + "; prefix ! = bold, + = italic, * = bold-italic")
    parser.add_argument("input_file", help = "a csv file")
    parser.add_argument("-o", "--output", help = "output file, prints to stdout if none given")
    args = parser.parse_args()
    return args
    
def is_int(string):
    try:
        int(string)
        return True
    except ValueError:
        return False

def add_commas(integer):
    """
    @return a string that represents the integer with commas added
    """
    if integer < 1000:
        return str(integer)
    return add_commas(integer // 1000) + "," + str(integer % 1000)

def _convert(string):
    """
    performs useful conversions, such as adding commas to large integers and escaping _'s
    """
    string = string.replace('_', '\\_')
    if is_int(string):
        string = add_commas(int(string))
    return string
    
def _format_token(token):
    """
    Wrap a token with formatting.
     ! -> \textbf{}
     + -> \emph{}
     * -> \textbf{\emph{}}
    also, put an escape before each _
    """
    if len(token) == 0:
        return " "
    if token[0] == "!":
        return r'\textbf{' + _convert(token[1:]) + r'}'
    elif token[0] == '+':
        return r'\emph{' + _convert(token[1:]) + r'}'
    elif token[0] == '*':
        return r'\textbf{\emph{' + _convert(token[1:]) + r'}}'
    return _convert(token)


def _csv_to_latex(in_stream, out_stream):
    """
    Convert lines like this:
    x1, x2, ..., x4 -> x1 & x2 & ... & x4 \\\hline
    """
    with in_stream:
        with out_stream:
            for line in in_stream.readlines():
                tokens = [token.strip() for token in line.split(',')]
                tokens = list(map(_format_token, tokens))
                new_line = " & ".join(tokens) + ' \\\hline' + '\n'
                out_stream.write(new_line)

if __name__ == '__main__':
    """
    Usage: python csv-to-latex.py <csv filename> <tex filename>
    """
    args = parse_arguments()
    in_stream = open(args.input_file, "r")
    if args.output:
        out_stream = open(args.output, "w")
    else:
        out_stream = sys.stdout
    _csv_to_latex(in_stream, out_stream)

#  [Last modified: 2019 07 18 at 19:27:32 GMT]
