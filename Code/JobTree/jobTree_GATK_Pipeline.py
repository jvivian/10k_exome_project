# 4-13-15
# John Vivian

"""
Tree Structure of GATK Pipeline

     0-----> 11
    / \
   1   2
   |   |
   3   4
   |   |
   5   6
   |   |
   7   8
   |   |
   9   10

0  = create .dict/.fai for reference genome
1,2 = samtools index
3,4 = RealignerTargetCreator
5,6 = Indel Realignment
7,8 = Base Recalibration
9,10 = Recalibrate (PrintReads)
11 = MuTect

1-10 are "Target children"
11 is a "Target follow-fn", it is executed after completion of children.

=========================================================================

local_dir = /ephemeral/jobtree

shared input files go in:
    <local_dir>/<script_name>/

BAMS go in:
    <local_dir>/<script_name>/<pair>/
<pair> is defined as UUID-normal:UUID-tumor

files are uploaded to:
    s3://<script>/<pair>/

TARGET
-----------
1. Call **Download** function
    |___>    Check for inputs.  If not present, download from S3.
2.  Run Tool
3.  Upload to S3
=========================================================================
:Dependencies:
wget        - apt-get install wget
samtools    - apt-get install samtools
picard      - apt-get install picard-tools

"""

from jobTree.scriptTree.target import Target
from jobTree.scriptTree.stack import Stack
import argparse
import os
import sys
import subprocess
import boto


def build_parser():
    """
    Contains arguments for the all of necessary input files
    :return:
    """
    parser = argparse.ArgumentParser()
    parser.add_argument('-r', '--reference_genome', required=True, help="Reference Genome URL")
    parser.add_argument('-n', '--normal', required=True, help='Normal BAM URL. Format: UUID.normal.bam')
    parser.add_argument('-t', '--tumor', required=True, help='Tumor BAM URL. Format: UUID.tumor.bam')
    parser.add_argument('-p', '--phase', required=True, help='1000G_phase1.indels.hg19.sites.fixed.vcf URL')
    parser.add_argument('-m', '--mills', required=True, help='Mills_and_1000G_gold_standard.indels.hg19.sites.vcf URL')
    parser.add_argument('-d', '--dbsnp', required=True, help='dbsnp_132_b37.leftAligned.vcf URL')
    parser.add_argument('-c', '--cosmic', required=True, help='b37_cosmic_v54_120711.vcf URL')
    parser.add_argument('-g', '--gatk', required=True, help='GenomeAnalysisTK.jar')
    return parser


def download_inputs(shared_dir, pair_dir, inputs, *arg):
    """
    Checks for files (provided in *arg) and downloads them if not present.
    *arg are key_names from the inputs dict that are needed for that tool.
    Returns a dict:  input : file_name
    :param local_dir: str
    :param inputs: dict
    :param arg: str
    :return: dict
    """

    # Create necessary directories if not present
    local_dir = os.path.split(shared_dir)[0]
    if not os.path.exists(local_dir):
        os.mkdir(local_dir)
    if not os.path.exists(shared_dir):
        os.mkdir(shared_dir)
    if not os.path.exists(pair_dir):
        os.mkdir(pair_dir)

    # Acquire necessary inputs if not present, return file_names as a dict.
    file_names = {}
    for input in arg:
        file_name = inputs[input].split('/')[-1]
        file_names[input] = file_name
        if input == 'normal' or input == 'tumor':
            path = pair_dir
        else:
            path = shared_dir
        if not os.path.exists(os.path.join(path, file_name)):
            try:
                subprocess.check_call(['wget', '-P', path, inputs[input]])
            except subprocess.CalledProcessError:
                raise RuntimeError('\nNecessary file could not be acquired: {}. Check input URL'.format(file_name))
            except OSError:
                raise RuntimeError('\nFailed to find "wget".\nInstall via "apt-get install wget".')

    return file_names

def download_intermediates(shared_dir, pair_dir, file_names, intermediates, *arg):
    """
    Downloads files from S3 that have been created during the pipeline's execution.
    *arg are key_names from the intermediate dict that are needed for that tool.
    Always call download_intermediates after download_inputs.
    :param shared_dir: str
    :param pair_dir: str
    :param file_names: dict
    :param intermediates: dict
    :param arg: str
    """

    return file_names

def upload():
    """
    Upload files to S3, add to intermediate dictionary
    :return:
    """

def start_node(target, shared_dir, pair_dir, inputs, intermediates):
    """Create .dict/.fai for reference and start children/follow-on
    samtools faidx reference
    picard CreateSequenceDictionary R=reference O=output
    """

    file_names = download_inputs(shared_dir, pair_dir, inputs, "reference")

    # Create index file for reference genome (.fai)
    try:
        subprocess.check_call(['samtools', 'faidx', os.path.join(shared_dir, file_names["reference"])])
    except subprocess.CalledProcessError:
        raise RuntimeError('')
    except OSError:
        raise RuntimeError('')

    target.addChildTargetFn()
    target.addChildTargetFn()
    target.addFollowOnTargetFn()

def normal_index(target, inputs):
    """Creates index file for BAM"""
    pass

def tumor_index(target, inputs):
    pass

def normal_RTC(target, inputs):
    pass

def tumor_RTC(target, inputs):
    pass

def normal_IR(target, inputs):
    pass

def tumor_IR(target, inputs):
    pass

def normal_BR(target, inputs):
    pass

def tumor_BR(target, inputs):
    pass

def normal_PR(target, inputs):
    pass

def tumor_PR(target, inputs):
    pass

def mutect(target, inputs):
    pass


def main():


    # Define global variable: local_dir
    local_dir = "/mnt/jobtree"

    # Handle parser logic
    parser = build_parser()
    Stack.addJobTreeOptions(parser)
    args = parser.parse_args()

    # Store inputs for easy unpacking/passing. Create dict for intermediate files.
    inputs = {'reference' : args.reference_genome,
              'normal': args.normal,
              'tumor': args.tumor,
              'phase': args.phase,
              'mills': args.mills,
              'dbsnp': args.dbsnp,
              'cosmic': args.cosmic,
              }
    intermediates = {}

    # Ensure user supplied URLs to files and that BAMs are in the appropriate format
    for input in inputs:
        if ".com" not in inputs[input]:
            sys.stderr.write("Invalid Input: {}".format(input))
            raise RuntimeError("Inputs must be valid URLs, please check inputs.")
        if input == 'normal' or input == 'tumor':
            if len(inputs[input].split('/')[-1].split('.')) != 3:
                raise RuntimeError('{} Bam, is not in the appropriate format: \
                UUID.normal.bam or UUID.tumor.bam'.format(input))

    # Create directories for shared files and for isolating pairs
    # os.path.split()[0] could be used to get shared_dir, but didn't want to do that for every function.
    shared_dir = os.path.join(local_dir, os.path.basename(__file__).split('.')[0])
    pair_dir = os.path.join(shared_dir, inputs['normal'].split('/')[-1].split('.')[0] +
                            '-normal:' + inputs['tumor'].split('/')[-1].split('.')[0] + '-tumor')



    # Create JobTree Stack
    #i = Stack(Target.makeTargetFn(start_node, (shared_dir, pair_dir, inputs, intermediates))).startJobTree(args)


if __name__ == "__main__":
    #from JobTree.jt_GATK import *
    main()