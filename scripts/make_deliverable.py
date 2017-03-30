#!/usr/bin/python

import os
import sys
import argparse
import textwrap
import subprocess

def eval_projects(projects):
    try:
        # Get the part of the project name that should be common
        proj = ['_'.join(p.split('_')[2:6]) for p in projects]

        # Count how many times the 1st element occurs.
        # If equal to the list length, then all elements
        # are the same (as should)
        return proj.count(proj[0]) == len(proj)
    except IndexError:
        print("Error! Make sure the project name(s) you gave are valid.")
        exit(1)


# Move the working directory to the local root folder
os.chdir(os.path.dirname(sys.path[0]))

w = textwrap.TextWrapper(width=90,
                         break_long_words=False,
                         replace_whitespace=False)

help_descr = "This script is used to create deliverables for the given projects"

parser = argparse.ArgumentParser(
             description=help_descr,
             formatter_class=argparse.RawDescriptionHelpFormatter)

parser.add_argument(
        '-v', '--version',
        action='version',
        version='%(prog)s 0.1')

parser.add_argument(
        '-f', '--fastq', action='store_const', const=True,
        help='If set, it will also include the fastqs in the deliverable.')

parser.add_argument(
        '-p', '--project', nargs='*', required=True,
        help='Names of the projects you want to include in the deliverable.\
        You can give multiple projects by simply separete them with space.\
        Note that the projects should be part of a bigger biological project.\
        In other words, this part of the name: 10X_YY_NNN_## should be common.')

parser.add_argument(
        '-o', '--output',
        help='(Optional) The name of the deliverable to be created.')

args = parser.parse_args()

target_dir = 'deliverables'
if os.path.exists(target_dir):
    os.chdir(target_dir)
else:
    print("'{0}' directory does not exist. Exiting...".format(target_dir))
    exit(1)

if not eval_projects(args.project):
    print("Error! Make sure the projects are \
            part of a bigger biological project.")
    print("Use --help for more information.")
    exit(1)

if args.output is None:
    args.output = '_'.join(args.project[0].split('_')[2:6])

# Create the deliverable directory for the project, and move to it
try:
    os.mkdir(args.output)
except OSError as e:
    print(e)
    exit(1)
finally:
    os.chdir(args.output)

print(os.getcwd())

# Create 'fastq_files' directory if fastq argument was set
if args.fastq:
    args.fastq = 'fastq_files'
    os.mkdir(args.fastq)

# Get a dictionary of listed (sample) directories in each project
#sample_dirs = {}
projects_dir = '../../projects/'

cmd = 'rsync -r --progress {0} {1}'

for project in args.project:
    # Form the dir to get the data from
    source_dir = os.path.join(projects_dir, project + '/', 'counts/')
    print(source_dir)

    p = subprocess.Popen(cmd.format(source_dir + '*', '.'),
                        shell=True).wait()

    # Copy the fastq files if the fastq argument was set
    if args.fastq:
        source_dir = os.path.join(projects_dir, project + '/', 'fastqs/')

        p = subprocess.Popen(cmd.format(source_dir + '*', args.fastq),
                            shell=True).wait()

def make_deliverable():
    pass



#if __name__ = '__main__':
#    make_deliverable()
