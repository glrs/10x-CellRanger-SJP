#!/bin/bash -l

# Define the variables for the sbatch job
?uppmax_project_name
#SBATCH -A
?partition
#SBATCH -p
?num_cores
#SBATCH -n
?num_nodes
#SBATCH -N
?ram_memory
#SBATCH -C
?use_qos_short
#SBATCH --qos=short
?time_request
#SBATCH -t
?job_description
#SBATCH -J
?sbatch_output
#SBATCH --output=


# ================== SOME UGLY CODE FOLLOWS =================== #
#  -- Always change directory to the project's root dir         #
# where the script is located. This helps the orientation       #
# of the script relative to the project.                        #
                                                                #
# Get which file was called on the bash command                 #
# e.g.   symlink --or-- original                                #
SOURCE="${BASH_SOURCE[0]}"                                      #
                                                                #
# resolve $SOURCE until the file is no longer a symlink         #
while [ -h "$SOURCE" ];                                         #
do                                                              #
  DIR="$( cd -P "$( dirname "$SOURCE" )" && pwd )"              #
  SOURCE="$(readlink "$SOURCE")"                                #
                                                                #
  # if $SOURCE was a relative symlink, we need to resolve it    #
  # relative to the path where the symlink file was located     #
  [[ $SOURCE != /* ]] && SOURCE="$DIR/$SOURCE"                  #
done                                                            #
                                                                #
# Form the directory and move there                             #
DIR="$( cd -P "$( dirname "$SOURCE" )" && pwd )"                #
cd $DIR                                                         #
# ============================================================= #


# -- Create the necessary variables for the project --
?hiseq_datapath
HISEQ_PATH=""

# Get the hiseq directory name (without the path)
hiseq_dir=$(basename $HISEQ_PATH)
# Extract the project's name from the hiseq dir name
proj_name=$(awk -F"_" '{print substr($NF, 2);}' <<< $hiseq_dir)


# -- Create the necessary variables for the project --
# Get the hiseq directory name (without the path)
hiseq_dir=$(basename $HISEQ_PATH)


# Get the Lanes as a list (space separated string)
?bash_lane_or_sample_list
lanes=""

# -- Run CellRanger mkfastq --

# Move to the 'fastqs' dir to run cellranger mkfastq, so its output goes there.
cd 'fastqs'

# TODO: Get the number of iterations to calculate the localcores/localmem based on the choosen plan
# Run CellRanger mkfastq (separatelly for every lane)
for lane in $lanes
do
  # Run CellRanger mkfastq command
  # TODO: Add 'localcores' and 'localmem' restrictions.
  ../../../cellranger-1.2.0/cellranger mkfastq --run="$HISEQ_PATH" --csv="../metadata/$SAMPLESHEET" --lanes=$lane &
done

echo "Waiting CellRanger mkfastq to finish for Lanes: $lanes."
wait
