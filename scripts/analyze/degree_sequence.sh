#! /bin/bash

# degree_sequence.sh - outputs a list of vertex degrees for a graph in snap format

if [ $# -eq 0 ]; then
    echo "Usage: degree_sequence.sh FILE"
    echo "processes one file and outputs a single column listing degrees of all vertices:"
    echo "if FILE is '-', uses stdin"
    exit
fi

# removes lines that begin with #
function strip_comments {
    sed '/^#/d' $1
}

# @return the number of unique lines in the file ($1)
function number_unique {
    sort -n $1 | uniq | wc | awk '{print $1}'
}

# removes duplicates where both v w and w v appear in the file
function remove_duplicate_edges {
    awk '{if ($1 > $2) print $2, $1; else print $1, $2;}' $1 | sort | uniq
}

# turns all numbers in a file into a single column
function single_column {
    tr '[[:blank:]]' '\n' $1
}

# @return number of vertices in a snap format file ($1)
function num_vertices {
    strip_comments $1 | single_column | number_unique
}

# @return number of edges in a snap format file ($1)
function num_edges {
    strip_comments $1 | remove_duplicate_edges | number_unique
}

# creates a column giving the number of occurrences of each number in the input
function count_occurrences {
    sort -n $1 | uniq -c | awk '{print $1}'
}

################## main program ###################

file=$1
if [ $file != '-' ]; then
    strip_comments $file | remove_duplicate_edges | single_column | count_occurrences
else
    # use stdin
    strip_comments | remove_duplicate_edges | single_column | count_occurrences
fi

#  [Last modified: 2019 06 28 at 17:47:52 GMT]
