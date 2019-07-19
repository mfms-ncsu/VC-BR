#! /bin/bash

## harvest_instance_data.sh - creates a csv file with data for specific
## instances from a selection of existing csv files

function usage {
    echo "Usage: harvest_instance_data.sh NAMES INSTANCE_FILE"
    echo "       prints (to stdout) a csv file with each line having all the data"
    echo "       from given files for the instances listed in a file"
    echo "NAMES is a comma-separated list of csv filenames without the .csv extension"
    echo "INSTANCE_FILE is a text file of problem instances, one instance per line"
}

if [ $# -ne 2 ]; then
    usage
fi

names="`echo $1 | tr ',' ' '`"
instance_alt_expr=`cat $2 | tr '\n' '|'`
instance_alt_expr=${instance_alt_expr%|} # remove trailing |
instance_expr="^($instance_alt_expr),"

for name in $names; do
    file=$name.csv
    temp_file=/tmp/$$-$name.csv
    temp_file_sorted=/tmp/$$-$name-sorted.csv
    head -1 $file >> $temp_file
    egrep "$instance_expr" $file >> $temp_file
    sort -k 1 -t ',' $temp_file > $temp_file_sorted
    files="$files $temp_file_sorted"
done

# need two temp files so that the results of each join can be saved
outfile=/tmp/$$-out.csv
temp_outfile=/tmp/$$-out-tmp
first_file=`echo $files | cut -f 1 -d' '`
other_files=`echo $files | cut -f 2- -d' '`
cat $first_file > $outfile
for file in $other_files; do
    join -t, $outfile $file > $temp_outfile
    rm $outfile
    cat $temp_outfile > $outfile
    rm $temp_outfile
done
cat $outfile

#  [Last modified: 2019 07 19 at 18:09:24 GMT]
