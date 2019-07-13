# !/bin/bash

## create_lpx.sh - creates a directory containing cplex input instances from instances
#                  in a given directory
# note: snap2lpx.py must be in the same directory as this script

if [ $# -ne 1 ]; then
    echo "Usage: create_lpx.sh DIRECTORY"
    echo " where DIRECTORY contains instances in snap format"
    echo " creates a new directory with name DIRECTORY-lpx, containing files in lpx format"
    exit 1
fi

# grab absolute path to this script
script_dir=${0%/*}
# need this sequence if the call is relative to the current directory
pushd $script_dir > /dev/null
script_dir=$PWD
popd > /dev/null

# input and output directories also need to be absolute in order for convert_graph.py to work
in_dir=$1
pushd $in_dir > /dev/null
in_dir=$PWD
popd > /dev/null

out_dir=$in_dir-lpx
if [ -f $out_dir ] || [ -d $out_dir ]; then
    echo "$out_dir already exists, stopping"
    exit 1
fi

mkdir $out_dir

for file in "$in_dir"/*
do
    file_without_path=${file##*/}
    base_name=${file_without_path%.*}
    echo "$file -> $out_dir/$base_name.lpx"
    $script_dir/snap2lpx.py < $file > $out_dir/$base_name.lpx
    echo "======= done with $base_name"
done

#  [Last modified: 2019 07 13 at 20:56:07 GMT]
