#! /usr/bin/env python3

"""
Simple conversion from a csv file to &-separated fields suitable for latex tables.
A few features, such as markers for bold, italic, and bold-italic text (!,_,*)
and comma separation for large integers
"""

import argparse
import sys

def parse_arguments():
    parser = argparse.ArgumentParser(description = "converts csv to latex tabular format"
                                     + "; prefix ! = bold, _ = italic, * = bold-italic")
    parser.add_argument("input_file", help = "a csv file")
    parser.add_argument("-o", "--output", help = "output file, prints to stdout if none given")
    parser.add_argument("-c", "--comma_threshold", type = int,
                        help = "add commas to integers if >= this number (default 1000)",
                        default = 1000)
    parser.add_argument("-p", "--precision", type = int,
                        help = "number of digits to the right of decimal point for"
                        + "floating point numbers (default 1)",
                        default = 1)
    args = parser.parse_args()
    return args
    
def is_int(string):
    try:
        int(string)
        return True
    except ValueError:
        return False

def is_float(string):
    try:
        float(string)
        return True
    except ValueError:
        return False

def add_commas_helper(integer):
    """
    @return a string that represents the integer with commas added to
    partition the digits into blocks of three
    does the recursive part of the computation
    """
    if integer < 1000:
        return str(integer)
    return add_commas(integer // 1000) + "," + "%03d" % (integer % 1000)

def add_commas(integer):
    """
    @return a string that represents the integer with commas added
    """
    if integer < _args.comma_threshold:
        return str(integer)
    return add_commas_helper(integer // 1000) + "," + "%03d" % (integer % 1000)

def add_decimal_and_commas(number):
    """
    @return a string that represents the floating point number with commas
            for the integer part and digits after the decimal point
            as specified by command-line arguments
    """
    integer_part = int(number)
    fractional_part = number - integer_part
    fractional_format = "%0." + str(_args.precision) + "f"
    # note: formatted floats always begin with a 0 to the left of the decimal
    # point, but formatting can round up to the next integer, in which case
    # the integer part could be one less than it should be:
    #  for example 0.98 could become 1.0 with precision 1
    fractional_part_formatted = (fractional_format % fractional_part)
    if fractional_part_formatted[0] == '1':
        integer_part += 1
    fractional_part_formatted = fractional_part_formatted[1:]
    integer_string = add_commas(integer_part)
    return integer_string + fractional_part_formatted

def _convert(string):
    """
    performs useful conversions, such as adding commas to large integers and escaping _'s
    """
    string = string.replace('_', '\\_')
    if is_int(string):
        string = add_commas(int(string))
    elif is_float(string):
        string = add_decimal_and_commas(float(string))
    return string
    
def _format_token(token):
    """
    Wrap a token with formatting.
     ! -> \textbf{}
     _ -> \emph{}
     * -> \textbf{\emph{}}
    also, put an escape before each _
    """
    if len(token) == 0:
        return " "
    if token[0] == "!":
        return r'\textbf{' + _convert(token[1:]) + r'}'
    elif token[0] == '_':
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
                new_line = " & ".join(tokens) + r' \\ \hline' + '\n'
                out_stream.write(new_line)

if __name__ == '__main__':
    """
    Usage: python csv-to-latex.py <csv filename> <tex filename>
    """
    global _args
    _args = parse_arguments()
    in_stream = open(_args.input_file, "r")
    if _args.output:
        out_stream = open(_args.output, "w")
    else:
        out_stream = sys.stdout
    _csv_to_latex(in_stream, out_stream)

#  [Last modified: 2020 03 11 at 13:28:25 GMT]
