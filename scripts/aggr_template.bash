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
#SBATCH --qos=short
?time_request
#SBATCH -t
?job_description
#SBATCH -J
?sbatch_output
#SBATCH --output=

?
AGGR_ID=""
?
AGGR_CSV=""
# aggregation_4count-run2_v1.csv
?
NORM=""
?
LOCALC=
?
LOCALM=

../../../cellranger-1.2.0/cellranger aggr --id=$AGGR_ID --csv="$RUNPATH/metadata/$AGGR_CSV" --normalize=$NORM --localcores=$LOCALC --localmem=$LOCALM
