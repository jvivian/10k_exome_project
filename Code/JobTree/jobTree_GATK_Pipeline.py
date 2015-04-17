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

local_dir = /mnt/jobtree

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

import argparse
import errno
import os
import subprocess
import sys
import uuid

import boto
from boto.s3.key import Key

from jobTree.scriptTree.stack import Stack
from jobTree.scriptTree.target import Target


def build_parser():
    """
    Contains arguments for the all of necessary input files
    :return:
    """
    parser = argparse.ArgumentParser()
    parser.add_argument('-r', '--reference', required=True, help="Reference Genome URL")
    parser.add_argument('-n', '--normal', required=True, help='Normal BAM URL. Format: UUID.normal.bam')
    parser.add_argument('-t', '--tumor', required=True, help='Tumor BAM URL. Format: UUID.tumor.bam')
    parser.add_argument('-p', '--phase', required=True, help='1000G_phase1.indels.hg19.sites.fixed.vcf URL')
    parser.add_argument('-m', '--mills', required=True, help='Mills_and_1000G_gold_standard.indels.hg19.sites.vcf URL')
    parser.add_argument('-d', '--dbsnp', required=True, help='dbsnp_132_b37.leftAligned.vcf URL')
    parser.add_argument('-c', '--cosmic', required=True, help='b37_cosmic_v54_120711.vcf URL')
    parser.add_argument('-g', '--gatk', required=True, help='GenomeAnalysisTK.jar')
    return parser


def start_node(target, GATK):
    """Create .dict/.fai for reference and start children/follow-on
    samtools faidx reference
    picard CreateSequenceDictionary R=reference O=output
    """

    download_inputs(pair_dir, inputs, 'reference')

    shared_dir = get_shared_dir(pair_dir)
    file_names = get_filenames(inputs, 'reference')

    # Create index file for reference genome (.fai)
    try:
        subprocess.check_call(['samtools', 'faidx', os.path.join(shared_dir, file_names['reference'])])
    except subprocess.CalledProcessError:
        raise RuntimeError('\nsamtools failed to create reference index!')
    except OSError:
        raise RuntimeError('\nFailed to find "samtools". \n Install via "apt-get install samtools".')

    # Create dict file for reference genome (.dict)
    try:
        subprocess.check_call(['picard', 'CreateSequenceDictionary',
                               'R={}'.format(os.path.join(shared_dir, file_names['reference'])),
                               'O={}.dict'.format(os.path.join(shared_dir, file_names['reference']))])
    except subprocess.CalledProcessError:
        raise RuntimeError('\nPicard failed to create reference dictionary')
    except OSError:
        raise RuntimeError('\nFailed to find "picard". \n Install via "apt-get install picard-tools')

    # Save local path to intermediates
    intermediates['fai'] = os.path.join(shared_dir, file_names['reference'] + '.fai')
    intermediates['dict'] = os.path.join(shared_dir, file_names['reference'] + '.dict')

    # upload to S3
    upload_to_S3(pair_dir, intermediates['fai'])
    upload_to_S3(pair_dir, intermediates['dict'])

    # Spawn children and follow-on
    target.addChildTargetFn()
    target.addChildTargetFn()
    target.addFollowOnTargetFn()


def normal_index(target, pair_dir, inputs, intermediates):
    """Creates index file for BAM"""
    pass


def tumor_index(target, pair_dir, inputs, intermediates):
    pass


def normal_rtc(target, pair_dir, inputs, intermediates):
    pass


def tumor_rtc(target, pair_dir, inputs, intermediates):
    pass


def normal_ir(target, pair_dir, inputs, intermediates):
    pass


def tumor_ir(target, pair_dir, inputs, intermediates):
    pass


def normal_br(target, pair_dir, inputs, intermediates):
    pass


def tumor_br(target, pair_dir, inputs, intermediates):
    pass


def normal_pr(target, pair_dir, inputs, intermediates):
    pass


def tumor_pr(target, pair_dir, inputs, intermediates):
    pass


def mutect(target, pair_dir, inputs, intermediates):
    pass



class SupportGATK(object):
    """ Class to encapsulate all necessary data structures and methods used in the pipeline.
    """

    def __init__(self, input_URLs, shared_dir, pair_dir):
        self.input_URLs = input_URLs
        self.shared_dir = shared_dir
        self.pair_dir = pair_dir


    def get_input_path(self, name):

        shared_dir = SupportGATK.get_shared_dir(self.pair_dir)

        # Get path to file
        shared = name != 'tumor.bam' and name != 'normal.bam'
        dir_path = shared_dir if shared else self.pair_dir
        file_path = os.path.join(dir_path, name)

        # Create necessary directories if not present
        mkdir_p(dir_path)

        # Check if file exists, download if not present
        if not os.path.exists(file_path):
            try:
                subprocess.check_call(['curl', '-fs', self.input_URLs[name], '-o', file_path])
            except subprocess.CalledProcessError:
                raise RuntimeError('\nNecessary file could not be acquired: {}. Check input URL')
            except OSError:
                raise RuntimeError('Failed to find "curl". Install via "apt-get install curl"')

        return file_path


    def upload_to_S3(self, file):
        """
        file should be the relative path to the file.
        s3://bd2k_<script_name>/<pair>
        :param pair_dir: str
        :param file: str
        :return:
        """

        # Create S3 Object
        conn = boto.connect_s3()

        # Set bucket to bd2k-<script_name>
        bucket_name = 'bd2k-{}'.format(os.path.basename(__file__).split('.')[0])
        try:
            bucket = conn.get_bucket(bucket_name)
        except:
            bucket = conn.create_bucket(bucket_name)

        # Create Key Object -- reference intermediates placed in bucket root, all else in s3://bucket/<pair>
        k = Key(bucket)
        if not os.path.exists(file):
            raise RuntimeError('File at path: {}, does not exist'.format(file))
        if '.fai' in file or '.dict' in file:
            k.name = file.split('/')[-1]
        else:
            k.name = os.path.join(os.path.split(self.pair_dir)[1], file.split('/')[-1])

        # Upload to S3
        try:
            k.set_contents_from_filename(file)
        except:
            raise RuntimeError('File at path: {}, could not be uploaded to S3'.format(file))


    def get_shared_dir(self):
        return os.path.split(self.pair_dir)[0]

def main():
    # Define global variable: local_dir
    local_dir = "/mnt/jobtree"

    # Handle parser logic
    parser = build_parser()
    Stack.addJobTreeOptions(parser)
    args = parser.parse_args()

    # Store inputs for easy unpacking/passing. Create dict for intermediate files.
    input_URLs = {'reference.fasta': args.reference,
                  'normal.bam': args.normal,
                  'tumor.bam': args.tumor,
                  'phase.vcf': args.phase,
                  'mills.vcf': args.mills,
                  'dbsnp.vcf': args.dbsnp,
                  'cosmic.vcf': args.cosmic,
                  'gatk.jar': args.gatk
                  }

    # Ensure user supplied URLs to files and that BAMs are in the appropriate format
    for input in input_URLs:
        if ".com" not in input_URLs[input]:
            sys.stderr.write("Invalid Input: {}".format(input))
            raise RuntimeError("Inputs must be valid URLs, please check inputs.")
        if input == 'normal' or input == 'tumor':
            if len(input_URLs[input].split('/')[-1].split('.')) != 3:
                raise RuntimeError('{} Bam, is not in the appropriate format: \
                UUID.normal.bam or UUID.tumor.bam'.format(input))

    # Create directories for shared files and for isolating pairs
    shared_dir = os.path.join(local_dir, os.path.basename(__file__).split('.')[0], str(uuid.uuid4()))
    pair_dir = os.path.join(shared_dir, input_URLs['normal'].split('/')[-1].split('.')[0] +
                            '-normal:' + input_URLs['tumor'].split('/')[-1].split('.')[0] + '-tumor')


    # Create JobTree Stack
    # i = Stack(Target.makeTargetFn(start_node, (pair_dir, input_URLs, intermediates))).startJobTree(args)


if __name__ == "__main__":
    # from JobTree.jt_GATK import *
    main()


# Potentially defunct functions/methods live here. Delete when possible.
'''
def download_inputs(pair_dir, inputs, *arg):
    """
    Checks for files (provided in *arg) and downloads them if not present.
    *arg are key_names from the inputs dict that are needed for that tool.

    :param pair_dir: str
    :param inputs: dict
    :param arg: str
    """

    shared_dir = get_shared_dir(pair_dir)

    # Create necessary directories if not present
    local_dir = os.path.split(shared_dir)[0]
    if not os.path.exists(local_dir):
        os.mkdir(local_dir)
    if not os.path.exists(shared_dir):
        os.mkdir(shared_dir)
    if not os.path.exists(pair_dir):
        os.mkdir(pair_dir)

    # Acquire necessary inputs if not present, return file_names as a dict.
    for input in arg:
        file_name = get_filenames(inputs, input)[input]
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


def get_filenames(inputs, *arg):
    filenames = {}
    for input in arg:
        filenames[input] = inputs[input].split('/')[-1]
    return filenames

'''