# 10x CellRanger SJP
10xGenomics CellRanger - Slurm Job Partitioner (SJP)

## Background
### The pipelines
Cell Ranger is a set of analysis pipelines that processes Chromium single cell 3’ RNA-seq output to align reads, generate gene-cell matrices and perform clustering and gene expression analysis. Cell Ranger includes four main pipelines:
* *cellranger mkfastq*
* *cellranger count*
* *cellranger aggr*
* *cellranger reanalyze*

These pipelines combine Chromium-specific algorithms with the widely used RNA-seq aligner STAR. Output is delivered in standard BAM, MEX, CSV, HDF5 and HTML formats that are augmented with cellular information.

You can find more information about Chromium and Cell Ranger [here](https://www.10xgenomics.com/single-cell/).

### The setup
I run the Cell Ranger pipelines (presented above) on a SLURM based cluster, to analyze the raw, single-cell sequencing data deriving from Illumina HiSeq instruments.

### The problem
Most of the bioinformatics tools to date, are not mature enough to make efficient use of distributed sytems. Cell Ranger is not an exception. It doesn't seem to provide destributing capabilities in order to run it in more than one nodes, to parallelize the process. Moreover, the nodes on the cluster I am using, are not so powerful by their own. That means, one should split one big batch job into several smaller (each running on a different node), in an attempt to parallelize the process.

### The workaround
Here I created a workaround (rather than a solution) to this problem. I made this Python script, which based on the given parameters it decides how to devide a project into small jobs that run individually in their own node.

## Usage
Adapt the 10xGenomics Pipeline to your new Project.
```
$ python script_generator.py [-h] -d <Data_Path> -s <Samplesheet> -A <Slurm_Project> -J <Jobname> [--qos] [-r {mm,hg}] [--aggr-norm {mapped,raw,None}] [--version]
 ```

### General arguments

|  Arguments     |   Description                                |
|----------------|:--------------------------------------------:|
|  -h, --help    |        show this help message and exit       |
|  --version     |        show program's version number and exit|


### #SBATCH arguments
  
  #SBATCH arguments are used for specifying your
  preferences for the SLURM job you plan to submit.

|  Arguments     |   Description                                      |
|----------------|:--------------------------------------------------:|
|  -A            |       SLURM Project name.                         |
|  -J            |        Give a name to this job.                    |
|  -q, --qos     |Use it for testing. Max 15mins, 4nodes. Very high priority. |

### Script Variables:
  Variables about your project (e.g. file paths)

|  Arguments     |   Description                                      |
|----------------|:--------------------------------------------------:|
|  -d, --hiseq-datapath | Path of the raw hiseq data (pref. absolute).|
| -r, --ref {mm,hg}     | Choose a reference genome [mouse, human].   |
| -s, --samplesheet     |Path of the metadata samplesheet (pref. absolute).|
| --aggr-norm {mapped,raw,None} | Normalization depth across the input libraries.|

__NOTE__: If you call the script without arguments it will
      enter the adaptive mode, where you will be asked
      specifically to add each of the necessary inputs. (currently under construction)
