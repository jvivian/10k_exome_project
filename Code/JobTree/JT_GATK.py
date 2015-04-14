# 4-13-15
# John Vivian

"""
Tree Structure of GATK Pipeline is shown below

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

==================================================================

local_dir = /ephemeral/jobtree

shared input files go in:
    <local_dir>/<script>/

BAMS go in:
    <local_dir>/<script>/<pair>/

files are uploaded to:
    s3://<script>/<pair>/

TARGET
-----------
1. Call **Download** function
    |___>    Check for inputs.  If not present, download from S3.
2.  Run Tool
3.  Upload to S3
"""

from jobTree.scriptTree.target import Target
from jobTree.scriptTree.stack import Stack
import argparse
import os
import sys
import subprocess
import boto


def build_parser():
    """ Parser for file input"""
    parser = argparse.ArgumentParser()
    parser.add_argument('-r', '--reference_genome', required=True, help="Reference Genome URL")
    parser.add_argument('-n', '--normal', required=True, help='Normal BAM URL. Format: UUID.normal.bam')
    parser.add_argument('-t', '--tumor', required=True, help='Tumor BAM URL. Format: UUID.tumor.bam')
    parser.add_argument('-p', '--phase', required=True, help='1000G_phase1.indels.hg19.sites.fixed.vcf URL')
    parser.add_argument('-m', '--mills', required=True, help='Mills_and_1000G_gold_standard.indels.hg19.sites.vcf URL')
    parser.add_argument('-d', '--dbsnp', required=True, help='dbsnp_132_b37.leftAligned.vcf URL')
    parser.add_argument('-c', '--cosmic', required=True, help='b37_cosmic_v54_120711.vcf URL')
    return parser


def download(local_dir, *arg):
    """
    Checks for files (provided in *arg) and downloads them if not present.  *args should be URLs with the filename
    present in the URL. Example: www.foobar.com/FILENAME.vcf
    :param local_dir: str
    :param arg: str
    """

    # Create necessary directories if not present
    script_name = os.path.basename(__file__)
    if not os.path.exists(local_dir):
        os.mkdir(local_dir)
    if not os.path.exists(os.path.join(local_dir, script_name)):
        os.mkdir(os.path.join(local_dir, script_name))

    # Acquire necessary inputs if not present
    for input in arg:
        file_name = input.split('/')[-1]
        if not os.path.exists(os.path.join(local_dir, script_name, file_name)):
            try:
                subprocess.check_call(['wget', '-P', os.path.join(local_dir, script_name), input])
            except subprocess.CalledProcessError:
                raise RuntimeError('\nNecessary file could not be acquired: {}. Check input URL'.format(file_name))
            except OSError:
                raise RuntimeError('\nFailed to find "wget".\nInstall via "apt-get install wget".')


def upload():
    pass

def start_node(target, inputs):
    """Create .dict/.fai for reference and start children/follow-on"""

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

    # Store inputs for easy unpacking/passing
    inputs = {'ref' : args.reference_genome,
              'normal': args.normal,
              'tumor': args.tumor,
              'phase': args.phase,
              'mills': args.mills,
              'dbsnp': args.dbsnp,
              'cosmic': args.cosmic,
              }

    # Ensure user supplied URLs to files and that BAMs are in the appropriate format
    for input in inputs:
        if ".com" not in inputs[input]:
            sys.stderr.write("Invalid Input: {}".format(input))
            raise RuntimeError("Inputs must be valid URLs, please check inputs.")
        if input == 'normal' or input == 'tumor':
            if len(inputs[input].split('.')) != 3:
                raise RuntimeError('Bam: {}, is not in the appropriate format: UUID.normal.bam or UUID.tumor.bam')

        download(local_dir, inputs[input])
    # Create JobTree Stack
    #i = Stack(Target.makeTargetFn(start_node, (inputs))).startJobTree(args)


if __name__ == "__main__":
    #from JobTree.jt_GATK import *
    main()