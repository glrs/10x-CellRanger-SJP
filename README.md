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

## Installation
### Before you start
(This steps will soon become automatic.)
Make sure your folder structure looks like this:
```
10x-CellRanger-SJP
  |
  +-- cellranger-1.2.0/
  |
  +-- deliverables
  |
  +-- projects
  |
  +-- references/
  |
  +-- scripts/
```
Make sure your cellranger installation is under the `cellranger-1.2.0` directory. Place the references in the `references` folder. Then download the python script and the template files in the `scripts` folder.

## Usage
Adapt the 10xGenomics Pipeline to your new Project.
```
$ python script_generator.py [-h] -d <Data_Path> -s <Samplesheet> -A <Slurm_Project> -J <Jobname> [--qos] [-r {mm,hg}] [--aggr-norm {mapped,raw,None}] [--version]
 ```

### General arguments

|  Argument     |   Description                                |
|----------------|:--------------------------------------------:|
|  -h, --help    |        shows the help message and exits        |
|  --version     |        shows program's version number and exits|


### #SBATCH arguments

  #SBATCH arguments are used for specifying your
  preferences for the SLURM job you plan to submit.

|  Argument     |   Description                                      |
|----------------|:--------------------------------------------------:|
|  -A            |       SLURM Project name.                         |
|  -J            |        Give a name to this job.                    |
|  -q, --qos     |Use it for testing. Max 15mins, 4nodes. Very high priority. |

### Script Variables:
  Variables about your project (e.g. file paths)

|  Argument     |   Description                                      |
|----------------|:--------------------------------------------------:|
|  -d, --hiseq-datapath | Path of the raw hiseq data (pref. absolute).|
| -r, --ref {mm,hg}     | Choose a reference genome [mouse, human].   |
| -s, --samplesheet     |Path of the metadata samplesheet (pref. absolute).|
| --aggr-norm {mapped,raw,None} | Normalization depth across the input libraries.|

__NOTE__: If you call the script without arguments it will
      enter the adaptive mode, where you will be asked
      specifically to add each of the necessary inputs. (currently under construction)


## Make Deliverables
Once the projects you were running are done, you may want to deliver the data to someone, or keep them organized for yourself. To do that you can use the `make_deliverable.py` script, which will aggregate the data of the given projects into one folder. (The given projects have to be subject of a common biological project. That means part of the project name should much.)

### Usage
```
./make_deliverable.py -p project_XXXXXXXXX_10X_YY_NNN_##_001 project_YYYYYYYYY_10X_YY_NNN_##_002 -f -o 10X_YY_NNN_##
```

### Parameters
| Argument       | Description    |
|:---------------|:--------------|
| -h, --help     | show the help message and exits |
| -v, --version  | shows program's version number and exits |
| -p, --project  | Names of the projects you want to include in the deliverable. |
| -f, --fastq    | If set, it will also include the fastqs in the deliverable. |
| -o, --output   | (Optional) The name of the deliverable to be created. |

__NOTE__:
* You can give multiple projects by simply separete them with space. Note that the projects should be part of a bigger biological project. In other words, this part of the name: `10X_YY_NNN_##` should be common.
*  If `-o, --output` argument is not given, the common part of the project names will be used for the naming of the output.
