#! /bin/bash

## run_configs.sh - for running standard benchmark experiments using the Akiba-Iwata solver
##                  uses benchmark_experiments.py, which must be in the same directory.

CONFIG_FILE=all_configs.txt
CSV_FIELDS=useful_fields.txt
SCRIPT=benchmark_experiments.py
VCSolver_PATH=VCS-plus

function usage {
    echo "Usage: run_configs.sh INPUT_DIRECTORY [TIME_LIMIT] [TAG_1 ... TAG_k]"
    echo " where INPUT_DIRECTORY is the name of a directory containing files in snap format"
    echo "       TIME_LIMIT is timeout setting, default 900"
    echo "       TAG_i is a tag for a set of options, e.g. 'None', 'Cheap', etc."
    echo "       the tags default to 'None Deg1 DD Cheap LP All'"
    echo " *** requires benchmark_experiments.py in $1"
    echo " *** assumes a file all_configs.txt in $1/configs that has a line of the form"
    echo "          OPTIONS, TAG for each set of options"
    echo "     for example '--deg1 --dom --clique_lb, DD'"
    echo " *** also assumes a file useful_fields.txt in $1/configs"
    echo " creates the following in the *current* directory:"
    echo "    - Raw_Output-INPUT_DIRECTORY, where all output files go"
    echo "    - INPUT_DIRECTORY.csv, a csv file summarizing the results"
    echo " - can be run multiple times with added files or options:"
    echo "   runs already done will be skipped if corresponding raw output file is detected"
    echo "   but data from the earlier run *will still be in the csv file*, which is given a new name"
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

if [ $# -lt 1 ]; then
    usage $script_dir
    exit 1
fi
input_dir=$1
output_name=`basename $input_dir`
csv_output=$output_name.csv
if [ -e $csv_output ]; then
    alternate_name=$output_name-$$.csv
    echo "*** warning: file $csv_output exists, saving it as $alternate_name"
    mv $csv_output $alternate_name
fi

exec_script=$script_dir/$SCRIPT
if ! [ -x $exec_script ]; then
    echo "$exec_script is not able to be executed"
    exit 1
fi

# create a custom config file using the remaining command line args
shift
if [ $# -gt 0 ] && [[ $1 =~ ^[[:digit:]]+$ ]]; then
    timeout=$1
    shift
else
    # no time limit given (next item, if it exists, is not a number)
    timeout=900
fi

# remainder of command line is a list of tags
if [ $# -gt 0 ]; then
    tags="$@"
else
    # no tags given
    tags="None Deg1 DD Cheap LP All"
fi

# assemble the options into a file for use with benchmark_experiments.py
config_file=$config_dir/$CONFIG_FILE
options_file=/tmp/$$_configs
for tag in $tags; do
    options=`grep "$tag[[:space:]]*$" $config_file | cut -f 1 -d,`
    if [ -z "$options" ]; then
        echo "*** error: unknown tag '$tag', aborting ..."
        exit 1
    fi
    options="$options -t$timeout --show_solution, $tag"
    echo $options >> $options_file
done    

# assume VCSolver files are in a the root directory and that this is two
# levels above the current one;
# make sure you've compiled the latest version
java_dir=${script_dir%/*/*}/$VCSolver_PATH
echo "java_dir = $java_dir"
pushd $java_dir > /dev/null
./build.sh
popd > /dev/null
java_exec_dir=$java_dir/bin

if ! [ -e $java_exec_dir/Main.class ]; then
    echo "java main program $java_exec_dir/Main.class does not exist"
    exit 1
fi

output_dir=Raw_Output-$output_name
mkdir $output_dir

java_command="java -Xss1g -Xms4g -cp $java_exec_dir Main"

$exec_script $input_dir/ $output_dir/ $options_file $config_dir/$CSV_FIELDS "$java_command" > $csv_output

echo "*** Output is in $csv_output; previous output, if any, saved as '$alternate_name' ***"

#  [Last modified: 2019 07 07 at 20:02:29 GMT]
