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

# =================== STUFF BEFORE RUNNING ==================== #
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
                                                                #
# Print and keep the start time to calculate the run time       #
START_TIME=`date +%s`                                           #
echo $(date)                                                    #
# ============================================================= #


# -- Create the necessary variables for the project --
# Define the project variables given as arguments
?reference_genome
REF_ORGANISM=""
?samplesheet_loc
SAMPLESHEET=""
?hiseq_datapath
HISEQ_PATH=""
?cranger_localcores
LOCALC=
?cranger_localmem
LOCALM=


# Get the samples as a list (space separated string)
?bash_lane_or_sample_list
sample_array=""


# -- Create the necessary variables for the project --
# Get the hiseq directory name (without the path)
hiseq_dir=$(basename $HISEQ_PATH)

# Extract the project's name from the hiseq dir name
proj_name=$(awk -F"_" '{print substr($NF, 2);}' <<< $hiseq_dir)


# Assign the reference genome path according to the given organism
if [[ $REF_ORGANISM == "mm" ]]; then
  REF_GENOME="refdata-cellranger-mm10-1.2.0"

elif [[ $REF_ORGANISM == "hg" ]]; then
  REF_GENOME="refdata-cellranger-hg19-1.2.0"

else
  echo "There is no Genome available for the given organism."
  echo "Mouse will be used instead."
fi


# -- Run CellRanger count --

# Move to the 'counts' dir to run cellranger count, so its output goes there.
cd '../counts'


# TODO: Get the number of iterations to calculate the localcores/localmem based on the choosen plan
# Run CellRanger count (separatelly for every sample)
for sample in $sample_array
do
  echo $sample
  # Extract the sample's lane and form the folder's name
  extr_lane=($(awk -F, -v sample=$sample '$2 == sample {print $1}' "../metadata/$SAMPLESHEET"))

  fastq_dir=$proj_name"_"$extr_lane

  # TODO: Check 'localcores' and 'localmem'. Do some automation
  ../../../cellranger-1.2.0/cellranger count --id=$sample --transcriptome="../../../references/$REF_GENOME" --fastqs="../fastqs/$fastq_dir/outs/fastq_path/" --sample=$sample --localcores=$LOCALC --localmem=$LOCALM &
done


# ========================== STUFF AFTER RUNNING ============================= #
# Calculate and print the run and the end time                                 #
END_TIME=`date +%s`                                                            #
RUN_TIME=$((END_TIME - START_TIME))                                            #
                                                                               #
echo $(date)                                                                   #
printf 'Script was running for: '                                              #
printf '%d-%02d:%02d:%02d\n' $(($RUN_TIME/86400)) $(($RUN_TIME/3600)) $(($RUN_TIME%3600/60)) $(($RUN_TIME%60))
# ============================================================================ #
