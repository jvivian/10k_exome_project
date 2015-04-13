__author__ = 'Jvivian'

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

1,2 = samtools index
3,4 = RealignerTargetCreator
5,6 = Indel Realignment
7,8 = Base Recalibration
9,10 = Recalibrate (PrintReads)
11 = MuTect

|,/,| = children
----> = follow-on

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
from subprocess import Popen
import argparse
import os


def build_parser():
    """ Parser for file input"""
    parser = argparse.ArgumentParser()
    parser.add_argument('-r', '--reference_genome', help="Reference Genome")
    parser.add_argument('-n', '--normal', help='Normal BAM')
    parser.add_argument('-t', '--tumor', help='Tumor BAM')
    parser.add_argument('-p', '--phase', help='1000G_phase1.indels.hg19.sites.fixed.vcf')
    parser.add_argument('-m', '--mills', help='Mills_and_1000G_gold_standard.indels.hg19.sites.fixed.vcf')
    parser.add_argument('-d', '--dbsnp', help='dbsnp_132_b37.leftAligned.vcf')
    parser.add_argument('-c', '--cosmic', help='b37_cosmic_v54_120711.vcf')
    return parser


def start_node(target, inputs):
    """Used to start children and follow-on"""
    target.addChildTargetFn()
    target.addChildTargetFn()
    target.addFollowOnTargetFn()

def normal_RTC(target, inputs):



def main():

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

    i = Stack(Target.makeTargetFn(start_node, (inputs))).startJobTree(args)

    if i != 0:
        raise RuntimeError("Got failed jobs")

if __name__ == "__main__":
    from JobTree.jt_GATK import *
    main()