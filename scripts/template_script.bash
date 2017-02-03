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

#  -- Always change directory to the project's root dir
# where the script is located. This helps the orientation
# of the script relative to the project.

# Get which file was called on the bash command
# e.g.   symlink --or-- original
SOURCE="${BASH_SOURCE[0]}"

# resolve $SOURCE until the file is no longer a symlink
while [ -h "$SOURCE" ];
do
  DIR="$( cd -P "$( dirname "$SOURCE" )" && pwd )"
  SOURCE="$(readlink "$SOURCE")"

  # if $SOURCE was a relative symlink, we need to resolve it
  # relative to the path where the symlink file was located
  [[ $SOURCE != /* ]] && SOURCE="$DIR/$SOURCE"
done

# Form the directory and move there
DIR="$( cd -P "$( dirname "$SOURCE" )" && pwd )"
cd $DIR


# Define the project variables given as arguments
?reference_genome
REF_ORGANISM=""
?samplesheet_loc
SAMPLESHEET=""
?hiseq_datapath
HISEQ_PATH=""


# -- Create the necessary variables for the project --
# Get the hiseq directory name (without the path)
hiseq_dir=$(basename $HISEQ_PATH)

# Extract the project's name from the hiseq dir name
proj_name=$(awk -F"_" '{print substr($NF, 2);}' <<< $hiseq_dir)

# Get the second column (Sample) of the samplesheet, as an array
sample_array=$(awk -F, 'NR>=2 {print $2}' "metadata/$SAMPLESHEET")

# Find the MIN and MAX lane number
minLane=($(awk -F, 'BEGIN{a=1000}{if ($1<0+a) a=$1} END{print a}' "metadata/$SAMPLESHEET"))
maxLane=($(awk -F, 'BEGIN{a=   0}{if ($1>0+a) a=$1} END{print a}' "metadata/$SAMPLESHEET"))

# Assign the reference genome path according to the given organism
if [[ $REF_ORGANSM == "mm" ]]; then
  REF_GENOME="refdata-cellranger-mm10-1.2.0"

elif [[ $REF_ORGANSM == "hg" ]]; then
  REF_GENOME="refdata-cellranger-hg19-1.2.0"

else
  echo "There is no Genome available for the given organism."
  echo "Mouse will be used instead."
fi


# -- Run CellRanger mkfastq --

# Move to the 'fastqs' dir to run cellranger mkfastq, so its output goes there.
cd 'fastqs'

# TODO: Get the number of iterations to calculate the localcores/localmem based on the choosen plan
# Run CellRanger mkfastq (separatelly for every lane)
for $(seq $minLane $maxLane)
do
  # Run CellRanger mkfastq command
  # TODO: Add 'localcores' and 'localmem' restrictions.
  ../../../cellranger-1.2.0/cellranger mkfastq --run="$HISEQ_PATH" --csv="../metadata/$SAMPLESHEET" --lanes=$i &
done

echo "Waiting CellRanger mkfastq to finish for Lanes: $minLane to $maxLane ..."
wait


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
  ../../../cellranger-1.2.0/cellranger count --id=$sample --transcriptome="../../../references/$REF_GENOME" --fastqs="../fastqs/$fastq_dir/outs/fastq_path/" --sample=$sample --localcores=4 --localmem=115 &
done
