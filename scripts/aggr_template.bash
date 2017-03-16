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

# # =================== STUFF BEFORE RUNNING ==================== #
# #  -- Always change directory to the project's root dir         #
# # where the script is located. This helps the orientation       #
# # of the script relative to the project.                        #
#                                                                 #
# # Get which file was called on the bash command                 #
# # e.g.   symlink --or-- original                                #
# SOURCE="${BASH_SOURCE[0]}"                                      #
#                                                                 #
# # resolve $SOURCE until the file is no longer a symlink         #
# while [ -h "$SOURCE" ];                                         #
# do                                                              #
#   DIR="$( cd -P "$( dirname "$SOURCE" )" && pwd )"              #
#   SOURCE="$(readlink "$SOURCE")"                                #
#                                                                 #
#   # if $SOURCE was a relative symlink, we need to resolve it    #
#   # relative to the path where the symlink file was located     #
#   [[ $SOURCE != /* ]] && SOURCE="$DIR/$SOURCE"                  #
# done                                                            #
#                                                                 #
# # Form the directory and move there                             #
# DIR="$( cd -P "$( dirname "$SOURCE" )" && pwd )"                #
# cd $DIR                                                         #
                                                                #
# Print and keep the start time to calculate the run time       #
START_TIME=`date +%s`                                           #
echo $(date)                                                    #
# ============================================================= #


# Load the bcl2fastq (v2.17.1) module
module load bioinfo-tools
module load bcl2fastq/2.17.1

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

# TODO: Most probably I'll need to change directory to 'aggregation'
# cd 'aggregation'

../../../cellranger-1.2.1/cellranger aggr --id=$AGGR_ID --csv="../metadata/$AGGR_CSV" --normalize=$NORM --localcores=$LOCALC --localmem=$LOCALM


# ========================== STUFF AFTER RUNNING ============================= #
# Calculate and print the run and the end time                                 #
END_TIME=`date +%s`                                                            #
RUN_TIME=$((END_TIME - START_TIME))                                            #
                                                                               #
echo $(date)                                                                   #
printf 'Script was running for: '                                              #
printf '%d-%02d:%02d:%02d\n' $(($RUN_TIME/86400)) $(($RUN_TIME/3600)) $(($RUN_TIME%3600/60)) $(($RUN_TIME%60))
# ============================================================================ #
