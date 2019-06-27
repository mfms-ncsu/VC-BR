#! /bin/bash

## run_cplex.sh - for running standard benchmark experiments using CPLEX

CPLEX_FIELDS="Objective runtime Nodes"

function usage {
    echo "Usage: run_cplex.sh INPUT_DIRECTORY [TIME_LIMIT]"
    echo " where INPUT_DIRECTORY is the name of a directory containing files in lp format"
    echo "       TIME_LIMIT is the time out, in seconds (default 900)"
    echo " *** requires benchmark_experiments.py in $1"
    echo " creates the following in the *current* directory:"
    echo "    - Raw_Output-INPUT_DIRECTORY, where all output files go"
    echo "    - INPUT_DIRECTORY.csv, a csv file summarizing the results"
}

# grab absolute path to this script
script_dir=${0%/*}
# need this sequence if the call is relative to the current directory
pushd $script_dir > /dev/null
script_dir=$PWD
popd > /dev/null
# directory containing files that specify reduction sets and fields to
# capture in the csv file
config_dir=$script_dir/configs

if [ $# -lt 1 ] || [ $# -gt 2 ]; then
    usage $script_dir
    exit 1
fi
input_dir=$1
output_name=`basename $input_dir`

shift
if [ $# -gt 0 ]; then
    if [[ $1 =~ ^[[:digit:]]+$ ]]; then
        timeout=$1
    else
        echo "Time limit must be an integer; $1 was given"
        usage $script_dir
        exit 1
    fi
else
    # no time limit given (next item, if it exists, is not a number)
    timeout=900
fi

# create a config file for the CPLEX run
options_file=/tmp/$$_configs
echo "-time=$timeout -verify, CPLEX" >> $options_file

# create a file specifying which fields to harvest
fields_file=/tmp/$$_fields
for field in $CPLEX_FIELDS; do
    echo $field >> $fields_file
done

exec_script=$script_dir/benchmark_experiments.py
if ! [ -x $exec_script ]; then
    echo "unable to execute $exec_script"
    exit 1
fi

cplex_exec=`which cplex_ilp`
if ! [ -x $cplex_exec ]; then
    echo "unable to execute $cplex_exec"
    exit 1
fi

output_dir=Raw_Output-$output_name
mkdir $output_dir

$exec_script $input_dir/ $output_dir/ $options_file $fields_file "$cplex_exec" > $output_name.csv

#  [Last modified: 2019 05 18 at 10:28:03 GMT]
