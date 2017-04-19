#!/usr/bin/python

from scripts.script_generator import main
import os
import sys

if __name__ == "__main__":
    # Move the working directory to the local root folder
    # os.chdir(os.path.dirname(sys.path[0]))

    # Call the script_partitioner (_generator) through its main function
    main()
