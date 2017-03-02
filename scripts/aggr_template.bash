#!/bin/bash -l

# Define the variables for the sbatch job
?uppmax_project_name
#SBATCH -A
?partition
#SBATCH -p
?num_cores
#SBATCH -n
?ram_memory
#SBATCH -C
?use_qos_short
#SBATCH --qos=
?time_request
#SBATCH -t
?job_description
#SBATCH -J
?sbatch_output
#SBATCH --output=

# ================== NOTHING TO CARE ABOUT ==================== #
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

?aggregation_id
AGGR_ID=""
?aggr_csv_meta_file
AGGR_CSV=""
?cranger_aggr_norm
NORM=""
?cranger_localcores
LOCALC=
?cranger_localmem
LOCALM=

../../../cellranger-1.2.0/cellranger aggr --id=$AGGR_ID --csv="$RUNPATH/metadata/$AGGR_CSV" --normalize=$NORM --localcores=$LOCALC --localmem=$LOCALM