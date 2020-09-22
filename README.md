# IKC Group Quantitation Pipeline

The quantitation pipeline provides a series of tools to automate the quantification
of protein identifications from ProteinPilot search results.

# Table of Contents

- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [Practice](#practice)
- [Sample Data](#sampledata)

# Installation

The quantitation pipeline, *i.e.* the Python package `QuantitationPipeline` and
its associated user interface scripts, can be installed from this Git repository.

### Compatibility

`QuantitationPipeline` is written in Python 3 and is compatible with most operating
systems.

### Instructions

1. Install Python 3 (>= 3.6).
2. Install the latest version of the `QuantitationPipeline` using:
```shell script
git clone git@github.com:ikcgroup/QuantitationPipeline.git
```
This will create a new directory containing the pipeline code.
3. Navigate to the new directory (*e.g.* `cd QuantitationPipeline`).
4. Run `pip3 install -r requirements.txt`. This will install the dependency modules.
5. Run `python3 setup.py install`. This will install the pipeline's scripts
for use on your computer.

# Configuration

All of the scripts are configured using a configuration file in JSON syntax, for example:
```JSON
{
	"ProteinSummaryFiles": [
		"data/Run1_ProteinSummary_113.txt",
		"data/Run2_ProteinSummary_113.txt",
	],
    "PeptideSummaryFiles": [
		"data/Run1_PeptideSummary_113.txt",
		"data/Run2_PeptideSummary_113.txt",
	],
	"ResultsDirectory": "data/results",
    "QuantitationRatios": [
		"114:113",
		"116:115",
		"118:117",
		"121:119"
	],
	"PeptideConfidenceThreshold": 95
}
```

Each script provided in the `QuantitationPipeline` package expects the name of
the configuration file to be passed as a parameter on the command line.

### Configuration Options

The required and optional configuration options are detailed below. Where scripts
are explicitly specified in "Required", the parameter is mandatory for those
scripts.

#### `ResultsDirectory` (Required)

- Description: The directory to which results files will be saved.
- Type: string (file path).

#### `ProteinSummaryFiles` (Required - app_accessions.py, accession_protein_names.py)

- Description: The raw ProteinSummary files from ProteinPilot.
- Type: array of file paths (strings) relative to the current directory.

#### `PeptideSummaryFiles` (Required - quantify.py, quantify_group.py)

- Description: The raw PeptideSummary files from ProteinPilot.
- Type: array of file paths (strings) relative to the current directory.

#### `QuantitationRatios` (Required - quantify.py, quantify_group.py)

- Description: The iTRAQ quantitation ratios to be considered.
- Type: array of string ratios, *e.g.* "113:114".

#### `PeptideConfidenceThreshold` (Optional - quantify.py, quantify_group.py)

- Description: The minimum peptide identification confidence for inclusion.
- Type: numeric value.
- Default: 95.

#### `MinNumSpectra` (Optional - quantify.py, quantify_group.py)

- Description: The minimum number of peptide identifications required for a protein group.
- Type: numeric value.
- Default: 4.

# Usage

The `QuantitationPipeline` provides four scripts:
1. `app_accessions.py`
2. `accession_protein_names.py`
3. `quantify.py`
4. `quantify_group.py`

Some of the scripts depend on the output of others and should be run consecutively.

### app_accessions.py and accession_protein_names.py

When several MS/MS experiments were performed using the same sample, the `app_accessions.py`
and `accession_protein_names.py` scripts should be used to summarize the combined
results.

To use these scripts, setup a configuration file with the `ProteinSummaryFiles` and
ensure that the files exist at those paths on your computer. You should also
have the ProteinPilot FDR spreadsheets, named in the same pattern as the ProteinSummary
files, in the same directory.

ProteinPilot groups proteins into groups of proteins which cannot be differentiated
by the database search algorithm, such as protein isoforms. The `app_accessions.py`
script will select protein groups with local FDR less than 5% and combine the
groups from the multiple configured experiments. For example, if isoform 1 of
protein Z is identified in experiment 1, while isoform 2 is identified in experiment 2,
then the script will generate a new protein group list with these two isoforms
in the same group. By default, the script will generate results in a folder named
"cowinner" inside your configured `ResultsDirectory`. The generated list of
protein groups is saved in the "merge" subfolder.

You should then run the script `accession_protein_names.py`, with the same configuration
file. This will create a new folder named "group" which contains a file listing
the proteins identified across all of the configured experiments. If the objective
of the analysis is to identify the proteins, there is no need to proceed to the
quantitation scripts.

### quantify.py

`quantify.py` is for quantifying iTRAQ data of a single MS/MS experiment.

This script requires the PeptideSummary files, along with the same FDR spreadsheets
required to run the previous scripts in the pipeline. You must also configure
the `QuantitationRatios` that should be quantified in this process.

`quantify.py` will filter those protein groups with less than 5% local FDR. You
can select the minimum confidence for each spectrum considered for
quantification via the `PeptideConfidenceThreshold` option. You may also configure
the minimum number of spectra required to quantify a protein group using the
`MinNumSpectra` option.

The one sample T test is applied to calculate the p-value of the protein expression ratio between the different samples based on the iTRAQ ratios of the peptides. For example, given the distribution of iTRAQ ratios between sample 114 and 113, what is the probability of the true sample mean be higher than 1.23 (for up-regulation, user define value) and lower than 0.81 (for down-regulation).
The resultant files will have a file name containing "hkuNoBgCorr" and need to be renamed to avoid overwriting. Column I (Normalized protein ratio) in the “Protein” tab is the expression ratios of the proteins. Normalization refers to correcting the bias introduced during sample preparation. Column K to N are the T test statistics.

For the monkey brain project, the convention is to use 114:113 for monkey 1, 116:115 for monkey 2, 118:117 for monkey 3 and 121:119 for monkey 4.

### quantify_group.py

Once the expression ratios of the proteins in single MS experiments have been calculated, `quantify_group.py` is used to combine the results from the different experiments. This program can take more than hour.

# Practice

All of the below practice questions refer to the Monkey Brain data set.

1.	Use the `app_accessions.py` script to combine the protein groups for I01 to I08.
2.	Use the `quantify.py` script to calculate the expression ratio of 114:113 for I01 to I08.
3.	Use the `quantify_group.py` script to combine the results of the 8 runs.

# Sample Data

Pipeline results for some known data sets are useful for benchmarking the procedure
and making sure that you can run the `QuantitationPipeline` successfully. The following
data files have well known results and the data can be downloaded from the
cloud disk in KBSB.
- 20130512_nonphos_ProteinSummary_113.txt
- 20130515_NCBI_iT_ProteinSummary_113.txt
- 20130916_2DRPRP_PH10_1-NCBI_ProteinSummary_113.txt
- 20130917_20ugMBI_2DRP-RP_PH10_2_ProteinSummary_113.txt
- 20130918pgcrp-ncbi_ProteinSummary_113.txt
- 20130919_2DPGCRP_ProteinSummary_113.txt
- 20131115-ncbi_tho 8F_ProteinSummary_113.txt
- 20131118-ncbi_tho 8F_ProteinSummary_113.txt
- 2D-HILICSCXRP-np_ProteinSummary_113.txt
- 3D_HILICSCXRP_np_ProteinSummary_113.txt
- F1-8 all thou NCBI 20140117search mgf_ProteinSummary_113.txt
