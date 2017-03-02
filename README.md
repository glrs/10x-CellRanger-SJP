# 10x CellRanger SJP
10xGenomics CellRanger - Slurm Job Partitioner (SJP)

usage: script_generator.py [-h] -d <Data_Path> -s <Samplesheet>
 	-A <Uppmax_Project> -J <Jobname> [--qos] [-r {mm,hg}]
 	[--aggr-norm {mapped,raw,None}] [--version]

Adapt the 10xGenomics Pipeline to your new Project.

optional arguments:
  -h, --help            show this help message and exit
  --version             show program's version number and exit

#SBATCH:
  
  #SBATCH arguments are used for specifying your
  preferences for the UPPMAX job you plan to submit.

  -A                    UPPMAX Project name.
  -J                    Give a name to this job.
  -q, --qos             Use it for testing. Max 15mins, 4nodes. Very high
                        priority.

Script Variables:
  Variables you need to specify about your project (e.g. file paths)

  -d, --hiseq-datapath 
                        Path of the raw hiseq data (pref. absolute).
  -r, --ref {mm,hg}     Choose a reference genome [mouse, human]
  -s, --samplesheet     Path of the metadata samplesheet (pref. absolute).
  --aggr-norm {mapped,raw,None}
                        Normalization depth across the input libraries.

NOTE: If you call the script without arguments it will
      enter the adaptive mode, where you will be asked
      specifically to add each of the necessary inputs.
