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
    parser.add_argument('-o', '--out_dir', default='/home/ubuntu/VCFs', help='Output Directory')
    parser.add_argument('-d', '--dbsnp', help='dbsnp_132_b37.leftAligned.vcf')
    parser.add_argument('-c', '--cosmic', help='b37_cosmic_v54_120711.vcf')
    parser.add_argument('-t', '--tool_dir', default='home/ubuntu/tools', help='Path')
    # parser.add_argument('-d', '--data_dir', default='/home/ubuntu/data', help='Path to Data_Directory')
    return parser


class StartNode(Target):
    def __init__(self, inputs):

        # Initialize Target
        Target.__init__(self)
        self.inputs = inputs

    # Spawn 2 children and a follow-on
    def run(self):
        self.addChildTarget(NormalIndex(self))
        self.addChildTarget(TumorIndex(self))
        self.setFollowOnTarget(Mutect(self))


class NormalIndex(Target):
    def __init__(self, inputs):
        # initialize Target
        Target.__init__(self)
        self.normal = inputs['normal']

    def run(self):
        Popen(["samtools", "index", self.normal])
        self.addChildTarget(NormalRTC(self))


class NormalRTC(Target):
    def __init__(self, inputs):
        # Initialize Target
        Target.__init__(self)

    def run(self):
        pass

class NormalIR(Target):
    def __init__(self, inputs):
        # Initialize Target
        Target.__init__(self)

    def run(self):
        pass

class NormalBR(Target):
    def __init__(self, inputs):
        # Initialize Target
        Target.__init__(self)

    def run(self):
        pass

class NormalPR(Target):
    def __init__(self, inputs):
        # Initialize Target
        Target.__init__(self)

    def run(self):
        pass

class TumorIndex(Target):
    def __init__(self, inputs):
        # Initialize Target
        Target.__init__(self)

    def run(self):
        pass

class TumorRTC(Target):
    def __init__(self, inputs):
        # Initialize Target
        Target.__init__(self)

    def run(self):
        pass

class TumorIR(Target):
    def __init__(self, inputs):
        # Initialize Target
        Target.__init__(self)

    def run(self):
        pass

class TumorBR(Target):
    def __init__(self, inputs):
        # Initialize Target
        Target.__init__(self)

    def run(self):
        pass

class TumorPR(Target):
    def __init__(self, inputs):
        # Initialize Target
        Target.__init__(self)

    def run(self):
        pass

class Mutect(Target):
    def __init__(self, inputs):
        # Initialize Target
        Target.__init__(self)

    def run(self):
        pass


if __name__ == "__main__":

    parser = build_parser()
    Stack.addJobTreeOptions(parser)
    args = parser.parse_args()

    # Store inputs in dict
    inputs = {'ref' : args.reference_genome,
              'normal': args.normal,
              'tumor': args.tumor,
              'phase': args.phase,
              'mills': args.mills,
              'dbsnp': args.dbsnp,
              'cosmic': args.cosmic,
              'tool_dir' : args.tool_dir,
              'out_dir' : args.out_dir,
              }

    # Create output directory if it does not exist
    if not os.path.exists(args.out_dir):
        os.mkdir(args.out_dir)

    # Sanity checks for files/dirs
    for input in inputs:
        if not os.path.exists(inputs[input]):
            raise RuntimeError("File or Directory is missing: {}".format(inputs[input]))

    i = Stack(Target.makeTargetFn(StartNode(inputs))).startJobTree(args)

    if i != 0:
        raise RuntimeError("Got failed jobs")
