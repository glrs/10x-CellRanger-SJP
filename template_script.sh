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

# Always change directory to the current folder
# (which should always be the project folder)
# This helps the orientation of the script.
cd "$(dirname "$0")"

# Define the project variables given as arguments
?reference_genome
REF_ORGANISM=""
?samplesheet_name
SAMPLESHEET=""
?hiseq_datapath
HISEQ_PATH=""


# -- Create the necessary variables for the project --
# Get the hiseq directory name (without the path)
hiseq_dir=$(basename $HISEQ_PATH)

# Extract the mkfastq output directory from the hiseq dir name
mkfastq_dir=$(awk -F"_" '{print substr($NF, 2);}' <<< $hiseq_dir)

# Get the second column (Sample) of the samplesheet, as an array
sample_array=$(awk -F, 'NR>=2 {print $2}' "metadata/$SAMPLESHEET")

# Find the MIN and MAX lane number
minLane=($(awk -F, 'BEGIN{a=1000}{if ($1<0+a) a=$1} END{print a}' "metadata/$SAMPLESHEET"))
maxLane=($(awk -F, 'BEGIN{a=   0}{if ($1>0+a) a=$1} END{print a}' "metadata/$SAMPLESHEET"))

# Assign the reference genome path according to the given organism
if [[ $REF_ORGANSM == "mm10" ]]; then
  REF_GENOME="refdata-cellranger-mm10-1.2.0"

elif [[ $REF_ORGANSM == "hg19" ]]; then
  REF_GENOME="refdata-cellranger-hg19-1.2.0"

else
  echo "There is no Genome available for the given organism."
  echo "Mouse will be used instead."
fi


# Create a dir to place the mkfastq command's output. Then move there.
mkdir $mkfastq_dir && cd $_

# -- Run CellRanger mkfastq (separatelly for every lane) --
for $(seq $minLane $maxLane)
do
  # Run CellRanger mkfastq command
  # TODO: Add 'localcores' and 'localmem' restrictions.
  ../../../cellranger-1.2.0/cellranger mkfastq --run="$HISEQ_PATH" --csv="../metadata/$SAMPLESHEET" --lanes=$i &
done

echo "Waiting CellRanger mkfastq to finish for Lanes: $minLane to $maxLane ..."
wait
