#!/usr/bin/python

import os
import re
import zipfile
import fnmatch
import textwrap
import argparse

__version__ = "0.1.0"


def zipdir(path, ziph, exclude=[], regex=[]):
    """
    Inputs:
        path    - the path of the directory you want to zip
        ziph    - a zip handler [zipfile.ZipFile() object]
        exclude - the files or folders you want to exclude (as list)
        regex   - regular expression ONLY for the files to be excluded (optional)
    """

    # If exclude is not a list (e.g. single string), convert it to list
    if not isinstance(exclude, list):
        exclude = [exclude]

    # If regex is not a list (e.g. single string), convert it to list
    if not isinstance(regex, list):
        regex = [regex]

    reg_patterns = []
    for r in regex:
        reg_patterns.append(re.compile(r))

    for root, dirs, files in os.walk(path):
        dirs[:] = [dir for dir in dirs if not dir in exclude]

        try:
            # Remove/exclude the current script from the file list
            files.remove(os.path.basename(__file__))
        except ValueError:
            # If not there
            pass

        # Remove the files that match the files/patterns in the exclude list
        for pat in exclude:
            for f in fnmatch.filter(files, pat):
                files.remove(f)

        # Remove the files that match the Regex patterns
        for p in reg_patterns:
            files[:] = [p.match(f).group() for f in files if p.match(f)]

        # Zip the remaining files
        for f in files:
            ziph.write(os.path.join(root, f))


if __name__ == "__main__":
    # Create a text wrapper for the help output text
    w = textwrap.TextWrapper(width=90,
                             break_long_words=False,
                             replace_whitespace=False)

    help_descr = "This script can be used to Zip a folder (excluding itself)"

    epilog_note = "NOTE: Copy this file on the root of the folder you want to zip."

    # Initialize a parser
    parser = argparse.ArgumentParser(
                    description=help_descr,
                    epilog=epilog_note,
                    formatter_class=argparse.RawDescriptionHelpFormatter)

    # -- Add the appropriate arguments -- #
    parser.add_argument(
            '-v', '--version',
            action='version',
            version='%(prog)s {0}'.format(__version__))

    parser.add_argument(
            '-r', '--regex', nargs='*',
            help='A list of regex patterns to exclude the matching files.')

    parser.add_argument(
            '-e', '--exclude', nargs='*',
            help='A list of the files and/or Unix wildcard patterns \
            to exclude the matching files.')

    parser.add_argument(
            '-o', '--output', required=True,
            help='The name of the output zipped file to be created.')

    # Parse the given arguments
    args = parser.parse_args()

    # Create a zip file object
    zipf = zipfile.ZipFile(args.output, 'w', zipfile.ZIP_DEFLATED)

    # Call the zipdir() function to organize and write the zip file
    zipdir('.', zipf, args.exclude, args.regex)

    # Close the zip object
    zipf.close()
