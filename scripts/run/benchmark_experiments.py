#! /usr/bin/env python3
"""
benchmark_experiments.py - runs experiments on all files in a directory;
                           configurations to be used and fields to put in the output
                           are specified in config files;
                           raw output is put into Raw_Output-xxx
this is a utility called from run_configs.sh and run_cplex.sh
"""

import argparse
import subprocess
import sys
import os

# file name for logging errors; the file will be in the raw output directory
ERROR_LOG_SUFFIX = "errors.log"
global error_filename

def parse_arguments():
    parser = argparse.ArgumentParser()

    # required arguments
    parser.add_argument("input_dir", help="Where to find the input instances")
    parser.add_argument("output_dir", help="Where to save raw output")
    parser.add_argument("options", help="File that contains list of options to run program with")
    parser.add_argument("fields", help="File that conatins list of fields to parse from the output")
    parser.add_argument("program", help="Program to run")

    return parser.parse_args()

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
    
# runs the program with the given options on the input file and puts the
# results in the output file; tag is added to the name of the output file
# @return True iff the run was free of errors
def run_option(program, input_file, options, tag, output_file):
    command = '{} {} {}'.format(program, options, input_file)
    sys.stderr.write("Running option(s) tagged as: {}\nFull command: {}\n".format(tag, command))

    with open(output_file, 'w') as of:
        get_host = os.popen("echo $HOSTNAME")
        command_status = subprocess.call(command.split(), stdout=of, stderr=subprocess.STDOUT)
    of = open(output_file, 'a')
    host_name = get_host.readline().rstrip()
    date_time = os.popen("date -u").readline().rstrip()
    of.write("host_name\t{}\n".format(host_name))
    of.write("date_time\t{}\n".format(date_time))

    if command_status != 0:
        error_stream = open(error_filename, 'a')
        error_stream.write("\n** Error when running\n  {}\n".format(command))
        error_stream.write("** host = {}\n".format(host_name))
        error_stream.write("** {}\n".format(date_time))
        error_stream.write("** Check {} for more details\n".format(output_file))
        return False
    else:
        return True

# parses the output file and creates a column for each field that was
# specified in the list of fields
# @param option a tag for the option
# @param results a 2-dimensional table with a value for each option/field combination
def process_output(output_file, option, fields, results):
    with open(output_file, 'r') as output:
        for line in output:
            pair = line.split()
            if len(pair) > 1:
                if pair[0] in fields:
                    results[option][pair[0]] = pair[1]

if __name__ == '__main__':
    global error_filename
    args = parse_arguments()

    # get options
    options = []
    with open(args.options, 'r') as options_file:
        for line in options_file:
            option, header = line.strip('\n').split(',')
            header = header.strip()
            options.append((option, header))

    # get fields
    fields = []
    with open(args.fields, 'r') as fields_file:
        for line in fields_file:
            fields.append(line.strip('\n'))

    # Check if output directory exists and create it if not
    sys.stderr.write("Checking if output directory exists\n")
    if not os.path.exists(args.output_dir):
        os.makedirs(args.output_dir)

    # Print header row
    option_string = ",".join([option[1] for option in options])
    print("{},{}".format("00-Instance", ",".join([field + "," + option_string for field in fields])))

    # create error log file in output directory; name will be the input
    # directory with a suffix
    error_filename = ''.join([args.output_dir, '00-', directory_base(args.input_dir),
                              '-', ERROR_LOG_SUFFIX])
    
    # process files - need to sort directory; some python implementations don't
    file_list = [ f for f in sorted(os.listdir(args.input_dir)) ]
    for file_name in file_list:
        sys.stderr.write("*** {}\n".format(file_name))
        if not os.path.isfile(os.path.join(args.input_dir, file_name)):
            sys.stderr.write("*** Warning: '{}' is not a regular file, ignored\n"
                             .format(file_name))
            continue
        # skip over files that don't have the right extensions
        if "java" in args.program:
            if not file_name.endswith(".snap") and not file_name.endswith(".txt"):
                sys.stderr.write("*** Warning: '{}' has an unrecognized extension, ignored\n"
                                 .format(file_name))
                sys.stderr.write("*** must be .snap or .txt if running VCSolver\n")
                continue
        elif "cplex" in args.program:
            if not file_name.endswith(".lpx"):
                sys.stderr.write("*** Warning: '{}' has an unrecognized extension, ignored\n"
                                 .format(file_name))
                sys.stderr.write("*** must be .lpx if running cplex\n")
                continue
        results = {option:{field:"" for field in fields} for option in options}
        for option in options:
            # run option
            input_file = args.input_dir + file_name
            output_file = ''.join([args.output_dir, extension_omitted(file_name),
                                   "-", option[1], ".txt"])
            if not os.path.isfile(output_file):
                succeeded = run_option(args.program, input_file, option[0], option[1], output_file)
                if succeeded:
                    process_output(output_file, option, fields, results)
            else:
                # if the file already exists, process it anyhow
                # this allows for reruns with more options or more instances,
                # while old information is still put into the spreadsheet
                sys.stderr.write("** file '{}' already exists, no need to rerun\n"
                                 .format(output_file))
                process_output(output_file, option, fields, results)


        # print results
        field_string = ""
        for field in fields:
            option_string = ""
            for option in options:
                option_string = ",".join([option_string, results[option][field]])
            field_string = ",".join([field_string, option_string])
        print("{}{}".format(extension_omitted(file_name), field_string))

#  [Last modified: 2019 07 01 at 21:08:32 GMT]
