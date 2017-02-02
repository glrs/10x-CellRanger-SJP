#!/usr/bin/python

import os
import sys
import shutil
import argparse
import textwrap
import itertools


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
    w = textwrap.TextWrapper(width=90,
                            break_long_words=False,
                            replace_whitespace=False)

    usage_note = ["%(prog)s [-h] [-o <Output_Name>] -A <Uppmax_Project>\n",
                    "\t-J <Jobname> [-p {core,node}] [-n int] [-N int]",
                    "[-t {d-hh:mm:ss}]\n\t[--qos] -d <Data_Path> [-r {mm,hg}]",
                    "-P <Project_Name> -s <Samplesheet>"]

    epilog_note = ["NOTE: If you call the script without arguments it will\n",
                    "     enter the adaptive mode, where you will be asked\n",
                    "     specifically to add each of the necessary inputs.\n"]

    # formatter_class=argparse.RawDescriptionHelpFormatter
    parser = argparse.ArgumentParser(
                description='Adapt the 10xGenomics Pipeline to your new Project.',
                formatter_class=CustomFormatter,
                epilog=" ".join(epilog_note),
                usage=" ".join(usage_note))

    # An argument group for #SBATCH
    group_sbatch = parser.add_argument_group('#SBATCH', textwrap.dedent('''
                    #SBATCH arguments are used for specifying your
                    preferences for the UPPMAX job you plan to submit.'''))

    group_sbatch.add_argument('-A', required=True, metavar='',
                        dest='uppmax_project_name',
                        help='UPPMAX Project name.')

    group_sbatch.add_argument('-J', required=True, metavar='',
                        dest='job_description',
                        help='Give a name to this job.')

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

    group_sbatch.add_argument('-q', '--qos', action='store_const' ,const='short',
                        dest='use_qos_short',
                        help='Use it for testing. Max 15mins, 4nodes. \
                        Very high priority.')


    # An argument group for the Script's variables of a project
    group_vars = parser.add_argument_group('Script Variables',
                        " ".join(["Variables you need to specify",
                                "about your project (e.g. file paths)"]))

    group_vars.add_argument('-d', '--hiseq-datapath', required=True, metavar='',
                        dest='hiseq_datapath',
                        help='Absolute path of the raw hiseq data to be analysed.')

    group_vars.add_argument('-r', '--ref', default='mm',
                        choices=['mm', 'hg'], dest='reference_genome',
                        help='Choose a reference genome [mouse, human]')

    group_vars.add_argument('-s', '--samplesheet', required=True, metavar='',
                        dest='samplesheet_name',
                        help='Provide the path of the metadata samplesheet.')

    # parser.add_argument('-i', '--input', help='Choose the input script')
    parser.add_argument('-o', '--output', dest='output',
                        help='Give a name to the output script.')

    parser.add_argument('--version',
                        action='version',
                        version='%(prog)s 1.0')

    args = parser.parse_args()


    # -- Argument Checks and Corrections --

    # Format Job description string properly
    args.job_description = args.job_description.replace(' ', '_')

    # Check if the given samplesheet path is valid.
    if not os.path.exists(args.samplesheet_name):
        print("The samplesheet path you provided is not valid. Exiting...")
        exit(1)

    # Check if the given hiseq data path is valid.
    if not os.path.exists(args.hiseq_datapath):
        print("The hiseq data-path you provided is not valid. Exiting...")
        exit(1)

    # Take the hiseq project name from the given hiseq path
    hiseq_project = os.path.basename(args.hiseq_datapath)

    # Extract project name by keeping the last part, starting from the 2nd char
    project_name = hiseq_project.split('_')[-1][1:]

    # If no name given for the generated script, use the hiseq project name
    if args.output is None:
        args.output = project_name + '_script.sh'


    # Generate the project folder and its subfolders.
    build_project_structure(project_name, args)

    # After creating the folder structure of the project
    # keep only the name of the samplesheet, instead of the full path.
    args.samplesheet_name = os.path.basename(args.samplesheet_name)

    # Edit the template file to generate the desired script
    edit_template(args)



def build_project_structure(project_name=None, args=None):
    """
    This function creates the folder structure to support a new project.
    """

    # Check if a project name is given
    if project_name is None:
        print("No project name given.")
        exit(2)

    # Move the working directory to the local root folder
    os.chdir(os.path.dirname(sys.path[0]))

    if not os.path.exists(os.getcwd() + "/Projects"):
        print("Directory 'Projects' could not be find in the current directory.")
        print("Make sure the script is located in the 'scripts' folder.")
        exit(3)

    # Form the name of the project folder to be created
    projects_dir = "Projects/" + "project_" + project_name

    # Check if a folder with the given name already exists
    # If exists, try suffixing with an ascending number
    count = itertools.count(1)
    while os.path.exists(projects_dir):
        print("A folder with the given project name, already exists.")
        projects_dir = '_'.join(projects_dir.split('_')[:2]) + '_' + str(count.next())
        print("Trying: " + projects_dir)

    # Form the name of the necessary folders in the project dir
    fastq_dir = projects_dir + "/fastqs"
    count_dir = projects_dir + "/counts"
    meta_dir  = projects_dir + "/metadata"

    # Try to create a project folder
    try:
        os.mkdir(projects_dir)
    except OSError as exception:
        raise
    else:
        os.mkdir(fastq_dir)
        os.mkdir(count_dir)
        os.mkdir(meta_dir)

    # Change directory back to the script's original dir
    os.chdir(sys.path[0])

    # Copy the samplesheet in the metadata folder
    # (it doesn't matter if the path is absolute or relative; this
    # will work since it passed the initial argument existing check)
    shutil.copy(args.samplesheet_name, "../" + meta_dir)


def edit_template(args, template=None):
    """
    This function creates a new file based on a (given) template,
    placing the appropriate given arguments in the right place.
    """

    args_dict = vars(args)
    args_keys = set(args_dict.keys())

    if template is None:
        template = "template_script.sh"

    if args.output == template or args.output == "template_script.sh":
        print("The output name should NOT be the same as the template script.")
        exit(5)

    with open(template, 'r') as template:
        template_buf = iter(template.readlines())

    with open(args.output, 'w') as output:
        for line in template_buf:
            if line.startswith('?'):
                # Is there something smart to do the replacement at once???
                lineplit = line[1:].split()

                arg_match = args_keys.intersection(lineplit)

                if arg_match and len(arg_match) == 1:
                    arg_val = args_dict[list(arg_match)[0]]
                    if arg_val is None:
                        line = ''
                        next(template_buf, None)
                    else:
                        next_line = next(template_buf).strip()
                        if next_line[-1:] != '"':
                            line = next_line + ' ' + str(arg_val) + '\n'
                        else:
                            line = next_line[:-1] + str(arg_val) + next_line[-1:] + '\n'
                else:
                    line = ''
                    next(template_buf, None)

            output.write(line)



if __name__ == "__main__":
    # print(len(sys.argv))
    if len(sys.argv) <= 1:
        interactive_input()
    else:
        arg_input()
