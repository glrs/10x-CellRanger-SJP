#!/usr/bin/python

from __future__ import division
from __future__ import print_function
from collections import defaultdict
from collections import namedtuple
from math import ceil

import os
import sys
import csv
import shutil
import argparse
import textwrap
import itertools


proj_struct = namedtuple('project', ['root', 'fastqs', 'counts',
                                        'aggr', 'meta', 'out'])
node = namedtuple('uppmax_node', ['partition', 'max_cores',
                                'mkfq_per_node', 'count_per_node'])

uppmax_node = node('core', 16, 4, 4)

scripts_to_gen = namedtuple('scripts_to_gen', ['mkfastq_plan',
                                'count_plan', 'aggr_plan'])

def interactive_input():
    #dirlist = os.listdir('.')

    #print("Choose a script: ")
    #choice = 0

    #for count, file in enumerate(dirlist):
    #    if file.endswith('.txt'):
    #        print(str(count) + ') ' + file)

    #try:
    #    filename = dirlist[int(raw_input())]
    #except ValueError:
    #    filename = choice
    filename = '<SCRIPT_NAME>'

    new_file = raw_input('How to name new script: ')

    with open(filename, 'r') as original:
        data = original.read()

    with open(new_file, 'w') as modified:
        modified.write(raw_input('What would you like to add? ') + '\n' + data)
        modified.close()
        original.close()

    return None


# Just to make things a bit nicer on the help output
class CustomHelpFormatter(argparse.HelpFormatter):
    def _format_action_invocation(self, action):
        if not action.option_strings:
            metavar, = self._metavar_formatter(action, action.dest)(1)
            return metavar
        else:
            parts = []
            # if the Optional doesn't take a value, format is:
            #    -s, --long
            if action.nargs == 0:
                parts.extend(action.option_strings)

            # if the Optional takes a value, format is:
            #    -s ARGS, --long ARGS
            # change to
            #    -s, --long ARGS
            else:
                default = action.dest.upper()
                args_string = self._format_args(action, default)
                for option_string in action.option_strings:
                    #parts.append('%s %s' % (option_string, args_string))
                    parts.append('%s' % option_string)
                parts[-1] += ' %s' % args_string
            return ', '.join(parts)

# Just to make things a bit nicer on the help output
class CustomFormatter(argparse.RawDescriptionHelpFormatter, CustomHelpFormatter):
    pass

def arg_input():
    # Create a text wrapper for the help output text
    w = textwrap.TextWrapper(width=90,
                            break_long_words=False,
                            replace_whitespace=False)

    # Form the usage note text
    usage_note = ["%(prog)s [-h] [-o <Output_Name>] -A <Uppmax_Project>\n",
                    "\t-J <Jobname> [-p {core,node}] [-n int] [-N int]",
                    "[-t {d-hh:mm:ss}]\n\t[--qos] -d <Data_Path> [-r {mm,hg}]",
                    "-P <Project_Name> -s <Samplesheet>"]

    # Form the epiloge text
    epilog_note = ["NOTE: If you call the script without arguments it will\n",
                    "     enter the adaptive mode, where you will be asked\n",
                    "     specifically to add each of the necessary inputs.\n"]

    # Initialize a parser using the CustomFormatter class
    parser = argparse.ArgumentParser(
                description='Adapt the 10xGenomics Pipeline to your new Project.',
                formatter_class=CustomFormatter,
                epilog=" ".join(epilog_note),
                usage=" ".join(usage_note))

    # Create an argument group for #SBATCH
    group_sbatch = parser.add_argument_group('#SBATCH', textwrap.dedent('''
                        #SBATCH arguments are used for specifying your
                        preferences for the UPPMAX job you plan to submit.'''))

    # -- Add the arguments for the #SBATCH group --
    group_sbatch.add_argument('-A', required=True, metavar='',
                        dest='uppmax_project_name',
                        help='UPPMAX Project name.')

    group_sbatch.add_argument('-J', required=True, metavar='',
                        dest='job_description',
                        help='Give a name to this job.')
    '''
    group_sbatch.add_argument('-p', choices=['core', 'node'], default='core',
                        dest='partition',
                        help='Choose partition.')

    group_sbatch.add_argument('-n', default=1, type=int, metavar='',
                        dest='num_cores',
                        help='No. of cores you will need.')

    group_sbatch.add_argument('-N', metavar='', dest='num_nodes',
                        help='No. of nodes [spreads given cores in several nodes]')

    group_sbatch.add_argument('-C', choices=['128','256','512'],
                        dest='ram_memory',
                        help="Choose memory(GB) (only when you select 'node')")

    group_sbatch.add_argument('-t', default='15:00', metavar='{d-hh:mm:ss}',
                        dest='time_request',
                        help='How long to reserve the resources for?')
    '''
    group_sbatch.add_argument('-q', '--qos', action='store_const' ,const='short',
                        dest='use_qos_short',
                        help='Use it for testing. Max 15mins, 4nodes. \
                        Very high priority.')

    # Create an argument group for variables related to a project
    group_vars = parser.add_argument_group('Script Variables',
                        " ".join(["Variables you need to specify",
                                "about your project (e.g. file paths)"]))

    # -- Add the arguments for the project variables group --
    group_vars.add_argument('-d', '--hiseq-datapath', required=True, metavar='',
                        dest='hiseq_datapath',
                        help='Path of the raw hiseq data (pref. absolute).')

    group_vars.add_argument('-r', '--ref', default='mm',
                        choices=['mm', 'hg'], dest='reference_genome',
                        help='Choose a reference genome [mouse, human]')

    group_vars.add_argument('-s', '--samplesheet', required=True, metavar='',
                        dest='samplesheet_loc',
                        help='Path of the metadata samplesheet (pref. absolute).')

    group_vars.add_argument('--aggr-norm', choices=['mapped', 'raw', 'None'],
                        default='mapped', dest='cranger_aggr_norm',
                        help='Normalization depth across the input libraries.')


    # -- The rest, general arguments --
    parser.add_argument('--version',
                        action='version',
                        version='%(prog)s 1.0')

    # Parse the given arguments
    args = parser.parse_args()

    return args


def run(args):
    # Get a dictionary of args
    args_dict = vars(args)

    # Add the predefind settings for Uppmax
    args_dict['num_cores'] = uppmax_node.max_cores
    args_dict['partition'] = uppmax_node.partition


    # -- Argument Checks and Corrections --

    # Format Job description string properly
    args.job_description = args.job_description.replace(' ', '_')

    # Check whether the given samplesheet path is valid or not.
    if os.path.exists(args.samplesheet_loc):
        pass
    elif os.path.exists('scripts/' + args.samplesheet_loc):
        try:
            args.samplesheet_loc = fix_path(args.samplesheet_loc)
        except:
            raise
    else:
        print("The samplesheet path you provided is not valid. Exiting...")
        exit(1)

    # Check whether the given hiseq data path is valid or not.
    if os.path.exists(args.hiseq_datapath):
        pass
    elif os.path.exists('scripts/' + args.hiseq_datapath):
        try:
            args.hiseq_datapath = fix_path(args.hiseq_datapath)
        except:
            raise
    else:
        print("The hiseq data-path you provided is not valid. Exiting...")
        exit(1)


    # Take the hiseq project name from the given hiseq path
    hiseq_project = os.path.basename(args.hiseq_datapath)

    # Take the samplesheet name from the given path (unique for each user)
    samplesheet_name = os.path.basename(args.samplesheet_loc)

    # Extract project name by keeping the last part, starting from the 2nd char
    project_name = hiseq_project.split('_')[-1][1:] + '_' + samplesheet_name[:-4]

    # Generate the project folder and its subfolders.
    project = build_project_structure(project_name)
    print("The project's folder structure has been created.")

    # Move/Copy the samplesheet in the correct location
    move_files(args.samplesheet_loc, project.meta, copy=True)
    print('The samplesheet has been put in the appropriate location.')

    # Get the samplesheet data in a dictionary
    samplesheet_dict = csv_to_dict(args.samplesheet_loc)

    # Remove duplicated Lanes
    samplesheet_dict['Lane'] = sorted(list(set(samplesheet_dict['Lane'])))

    # Keep only the NAME of the samplesheet, instead of the full path.
    args.samplesheet_loc = os.path.basename(args.samplesheet_loc)

    print('Calculating the plan for this project...')
    run_plan = calculate_plan(samplesheet_dict)

    if len(run_plan.aggr_plan) > 2:
        # Create a CSV file with the counts to be used by the 'cellranger aggr'
        args_dict['aggr_csv_meta_file'] = create_aggr_csv(project, samplesheet_dict)
        args_dict['aggregation_id'] = 'AGGR_' + project_name

    # Get the job description in a var to use it as prefix in the for loop
    job_descr = args.job_description

    print('Creating the appropriate scripts...')

    # Loop to generate the necessary files
    for scr_name, bash_list, loc, lom, template in list(itertools.chain(*run_plan)):
        # Append the SBATCH job description with the script name (no extension)
        args.job_description = job_descr + '_' + scr_name[:-3]

        # Assign the script name to be used
        args_dict['output'] = scr_name

        # Add an argument for the list of lanes or samples
        args_dict['bash_lane_or_sample_list'] = bash_list

        args_dict['cranger_localcores'] = loc
        args_dict['cranger_localmem'] = lom

        # Generate the script, given the arguments and the template
        generate_script(args_dict, template=template)

        # Move the generated script to the appropriate location
        move_files(scr_name, project.root)


    # Edit the template file to generate the desired script
    #edit_template(args)

    print('Done.')


# TODO!!!!!
# TODO: At the end create a script to collect all the
# TODO: slurm output files into the slurm_out folder
# TODO!!!!


def calculate_plan(samplesheet):
    """
    It gets a samplesheet (it should be in the form of a dictionary),
    and it calculates how many scripts should be generated and some
    details they should have, based on an earlier initialized global
    namedtuple variable named 'uppmax_node'.

    It returns a namedtuple with two lists, each contains a number of lists.
    Each inner list keeps three strings: the output script name, a string
    with space sep lanes or samples (BASH style list), and the name of the
    template to be used for the script's construction.
    """

    mpn = uppmax_node.mkfq_per_node
    cpn = uppmax_node.count_per_node

    # Calculate the number of mkfastq scripts to be generated
    mkfastq_scripts = len(samplesheet['Lane']) / mpn
    mkfastq_scripts = int(ceil(mkfastq_scripts))

    # Calculate the number of count scripts to be generated
    count_scripts = len(samplesheet['Sample']) / cpn
    count_scripts = int(ceil(count_scripts))

    # Initialize the predefind namedtuple with 2/3 empty lists
    # if count_scripts == 1:
    #     plan = scripts_to_gen([], [], None)
    # else:
    plan = scripts_to_gen([], [], [])

    cranger_info = namedtuple('cr_info', ['scr_name', 'bash_list',
                                'localcores', 'localmem', 'template'])

    # Generate the names for the mkfastq scripts
    for i in range(mkfastq_scripts):
        # Form the script name
        script_name = 'mkfastq_' + str(i+1) + '.sh'

        # Get the lanes corespond to each script (in BASH style string list)
        lanes = samplesheet['Lane'][i * mpn: (i+1) * mpn]
        lanes = " ".join(map(str, lanes))

        # Get the cores per lane (to be added to the $LOCALC var)
        cores_per_lane = uppmax_node.max_cores // len(lanes)

        mem_per_lane = cores_per_lane * 7

        mkfastq_info = cranger_info(script_name, lanes, cores_per_lane,
                                    mem_per_lane, 'mkfastq_template.bash')

        plan.mkfastq_plan.append(mkfastq_info)

        # plan.mkfastq_names.append(['mkfastq_' + str(i+1) + '.sh', lanes,
        #                         'mkfastq_template.bash'])

    # Generate the names for the count scripts
    for i in range(count_scripts):
        # Form the script name
        script_name = 'count_' + str(i+1) + '.sh'

        # Get the samples corespond to each script (in BASH style string list)
        samples = samplesheet['Sample'][i * cpn: (i+1) * cpn]
        samples = " ".join(map(str, samples))

        cores_per_sample = uppmax_node.max_cores // len(samples)
        mem_per_sample = cores_per_sample * 7

        count_info = cranger_info(script_name, samples, cores_per_sample,
                                    mem_per_sample, 'count_template.bash')

        plan.count_plan.append(count_info)
        # plan.count_info.append(['count_' + str(i+1) + '.sh', samples,
        #                         'count_template.bash'])

    if len(samplesheet['Sample']) != 1:
        cores = uppmax_node.max_cores
        mem = uppmax_node.max_cores * 7

        aggr_info = cranger_info('aggregation.sh', None, cores,
                                    mem, 'aggr_template.bash')

        plan.aggr_plan.append(aggr_info)
        # plan.aggregation.append(['aggregation.sh', None, cores,
        #                             mem, 'aggr_template.bash'])

    return plan


def create_aggr_csv(project, samplesheet, fieldnames=None):
    """
    It geberates a .csv file that contains the appropriate information
    about the 'count' output folders (named after the sample names in
    the samplesheet), needed to run the aggregation process.
    """

    meta_csv = project.meta + 'aggregation_meta.csv'
    with open(meta_csv, 'w') as f:
        if fieldnames is None:
            fieldnames = ['library_id', 'molecule_h5']

        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for sample in samplesheet['Sample']:
            # Form the path to the 'molecule_h5' file
            mol_path = project.counts + sample + '/outs/molecule_info.h5'

            # Write the row to the .csv output file
            writer.writerow({fieldnames[0]: sample, fieldnames[1]: mol_path})

    return meta_csv


def generate_script(args_dict, template):
    """
    This function creates a new file based on a (given) template,
    placing the appropriate given arguments in the right place.

    Areas that need to be edited on the template script should
    contain a '?' at the beginning of the line, followed by a
    string that matches the given argument keys.

    This function will delete this line, after either appending
    the next line with the right value (if the value was given),
    or deleting the next line too (if no value was given or if
    no such a key was found).

    template: { 'mkfastq', 'count' }
    """

    # Get a set of the given keys
    args_keys = set(args_dict.keys())

    if not os.path.exists(template):
        # Form the path that the template is expected to be.
        temp = fix_path(template)

        if not temp:
            print("Could not find the template file '{}' ".format(template), end='')
            print("in the scripts folder. Exiting...")
            exit(1)
        else:
            template = temp

    # Avoid replacing/losing the template file...
    # if args_dict['output'] == template \
    #     or args_dict['output'] == "mkfastq_template.bash" \
    #     or args_dict['output'] == "count_template.bash":
    #
    #     print("The output name should NOT be the same as the template script.")
    #     exit(3)

    # Open the template script in read mode
    with open(template, 'r') as template:
        template_buf = iter(template.readlines())

    # Open/Create the output file in write mode.
    with open(args_dict['output'], 'w') as output:
        for line in template_buf:
            # Lines starting with '?' in the template, indicate
            # positions where the argument keys can be found
            if line.startswith('?'):
                # Gets the string after '?' in a list
                linesplit = line[1:].split()

                # Get the matches of the key set and the linesplit as list
                arg_match = list(args_keys.intersection(linesplit))

                # Check whether only one match found
                if arg_match and len(arg_match) == 1:
                    # Get the value of the matched key
                    arg_val = args_dict[arg_match[0]]

                    # If the value is None, line should be omitted
                    if arg_val is None:
                        line = ''
                        next(template_buf, None)

                    else:
                        # Get the next line and strip any extra whitespace
                        next_line = next(template_buf).strip()

                        # Is the last char of the line a quotation mark?
                        if next_line[-1:] in ('"', "'"):
                            # Place the argument value between quotation marks
                            line = next_line[:-1] + str(arg_val) + next_line[-1:] + '\n'
                        else:
                            # Place the argument value at the end of the line
                            line = next_line + ' ' + str(arg_val) + '\n'

                else:
                    # If more or None matches found line should be omitted
                    line = ''
                    next(template_buf, None)

            # Write the edited template file into the final script file
            output.write(line)


def csv_to_dict(csv_file):
    """
    Get the content of a csv file as a list dictionary.

    i.e.
        print(dict['column1'])
        >>> ['Bob', 'Rob', 'John']
    """

    file_columns = defaultdict(list)

    with open(csv_file, 'r') as f:
        sheet = csv.DictReader(f)

        for row in sheet:
            for key, val in row.items():
                file_columns[key].append(val)

    return file_columns


def build_project_structure(project_name):
    """
    This function creates the folder structure to support a new project.
    """

    # Form the name of the project folder to be created inside 'projects'
    project_dir = 'projects/' + 'project_' + project_name

    # Check if a folder with the given name already exists
    # If exists, try suffixing with an ascending number
    count = itertools.count(1)
    while os.path.exists(project_dir):
        print("A folder with the given project name, already exists.")
        project_dir = '_'.join(project_dir.split('_')[:2]) + '_' + str(count.next())
        print("Trying: " + project_dir)

    # Form the name of the necessary folders in the project dir
    fastq_dir = project_dir + '/fastqs/'
    count_dir = project_dir + '/counts/'
    meta_dir  = project_dir + '/metadata/'
    out_dir   = project_dir + '/slurm_out/'
    aggr_dir  = project_dir + '/aggregation/'

    # Try to create the project folder
    try:
        os.mkdir(project_dir)
    except OSError as exception:
        raise
    else:
        # If successful create the extra directories inside it
        os.mkdir(fastq_dir)
        os.mkdir(count_dir)
        os.mkdir(meta_dir)
        os.mkdir(aggr_dir)
        os.mkdir(out_dir)

    # Instantiate the 'proj_struct' namedtuple for the project structure
    project = proj_struct(project_dir, fastq_dir, count_dir,
                            aggr_dir, meta_dir, out_dir)

    # Change directory back to the script's original dir
    # os.chdir(sys.path[0])

    # Copy the samplesheet in the metadata folder
    # (it doesn't matter if the path is absolute or relative; this
    # will work since it passed the initial argument existing check)
    # shutil.copy(args.samplesheet_loc, meta_dir)

    return project


# TODO: Get the arguments as dictionary [vars(args)]
def edit_template(args, template=None):
    """
    This function creates a new file based on a (given) template,
    placing the appropriate given arguments in the right place.

    Areas that need to be edited on the template script should
    contain a '?' at the beginning of the line, followed by a
    string that matches the given argument keys.

    This function will delete this line, after either appending
    the next line with the right value (if the value was given),
    or deleting the next line too (if no value was given or if
    no such a key was found).
    """

    # Get the arguments as a dictionary and get a set of the given keys
    args_dict = vars(args)
    args_keys = set(args_dict.keys())

    # If no template name was given, use the default template.
    if template is None:
        template = 'scripts/template_script.bash'

    if not os.path.exists(template):
        # Form the path that the template is expected to be.
        temp = fix_path(template)

        if not temp:
            print("Could not find the template file '{}' ".format(template), end='')
            print("in the scripts folder. Exiting...")
            exit(1)
        else:
            template = temp

    # Avoid replacing/losing the template file...
    if args.output == template or args.output == "template_script.bash":
        print("The output name should NOT be the same as the template script.")
        exit(3)

    # Open the template script in read mode
    with open(template, 'r') as template:
        template_buf = iter(template.readlines())

    # Open/Create the output file in write mode.
    with open(args.output, 'w') as output:
        for line in template_buf:
            # Lines starting with '?' in the template, indicate
            # positions where the argument keys can be found
            if line.startswith('?'):
                # Gets the string after '?' in a list
                linesplit = line[1:].split()

                # Get the matches of the key set and the linesplit as list
                arg_match = list(args_keys.intersection(linesplit))

                # Check whether only one match found
                if arg_match and len(arg_match) == 1:
                    # Get the value of the matched key
                    arg_val = args_dict[arg_match[0]]

                    # If the value is None, line should be omitted
                    if arg_val is None:
                        line = ''
                        next(template_buf, None)

                    else:
                        # Get the next line and strip any extra whitespace
                        next_line = next(template_buf).strip()

                        # Is the last char of the line a quotation mark?
                        if next_line[-1:] in ('"', "'"):
                            # Place the argument value between quotation marks
                            line = next_line[:-1] + str(arg_val) + next_line[-1:] + '\n'
                        else:
                            # Place the argument value at the end of the line
                            line = next_line + ' ' + str(arg_val) + '\n'

                else:
                    # If more or None matches found line should be omitted
                    line = ''
                    next(template_buf, None)

            # Write the edited template file into the final script file
            output.write(line)


def move_files(src, dest, copy=False):
    """
    Moves (or Copies) the given file to the given location.

    If you want to copy the files instead of moving them, set
    the 'copy' argument True.
    """
    func = shutil.move

    if copy:
        func = shutil.copy

    try:
        func(src, dest)
    except:
        raise


def fix_path(path, target='scripts'):
    """
    This function takes a path and a target (folder name) and
    joins them. The idea is to provide some flexibility for the
    users that use relative paths instead of absolute ones.

    Of course many things can go wrong (e.g. the folder the user
    calls the generator script from), so it's recommended to
    always make use of absolute data paths.
    """

    path = os.path.join(target, path)

    if os.path.exists(path):
        return path
    else:
        return False

if __name__ == "__main__":
    # Move the working directory to the local root folder
    os.chdir(os.path.dirname(sys.path[0]))

    # Check whether the 'projects' folder exists for localization
    if not os.path.exists(os.getcwd() + '/projects'):
        print("Directory 'projects' could not be find in the current directory.")
        print("Make sure the script is located in the 'scripts' folder.")
        exit(1)

    # print(len(sys.argv))
    if len(sys.argv) <= 1:
        args = interactive_input()
    else:
        args = arg_input()

    run(args)
