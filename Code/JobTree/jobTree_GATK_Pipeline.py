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
    <local_dir>/<script_name>/<UUID4>

BAMS go in:
    <local_dir>/<script_name>/<UUID4>/<pair>/
<pair> is defined as UUID-normal:UUID-tumor

files are uploaded to:
    s3://bd2k-<script>/<UUID4>/ if shared (.fai/.dict)
    s3://bd2k-<script>/<UUID4>/<pair> if specific to that T/N pair.

=========================================================================
:Dependencies:
curl        - apt-get install curl
samtools    - apt-get install samtools
picard      - apt-get install picard-tools
Active Internet Connection (Boto)
"""

import argparse
import errno
import os
import subprocess
import sys
import uuid

import boto
from boto.s3.key import Key
from boto.exception import S3ResponseError

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


def start_node(target, gatk):
    """Create .dict/.fai for reference and start children/follow-on
    samtools faidx reference
    picard CreateSequenceDictionary R=reference O=output
    """

    reference = gatk.get_input_path('reference.fasta')

    # Create index file for reference genome (.fai)
    try:
        subprocess.check_call(['samtools', 'faidx', reference])
    except subprocess.CalledProcessError:
        raise RuntimeError('\nsamtools failed to create reference index!')
    except OSError:
        raise RuntimeError('\nFailed to find "samtools". \n Install via "apt-get install samtools".')

    # Create dict file for reference genome (.dict)
    try:
        subprocess.check_call(['picard', 'CreateSequenceDictionary',
                               'R={}'.format(reference),
                               'O={}.dict'.format(reference)])
    except subprocess.CalledProcessError:
        raise RuntimeError('\nPicard failed to create reference dictionary')
    except OSError:
        raise RuntimeError('\nFailed to find "picard". \n Install via "apt-get install picard-tools')

    # upload to S3
    gatk.upload_to_S3()
    gatk.upload_to_S3()

    # Spawn children and follow-on
    target.addChildTargetFn()
    target.addChildTargetFn()
    target.addFollowOnTargetFn()


def normal_index(target, pair_dir, inputs, intermediates):
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

    def __init__(self, input_URLs, local_dir, shared_dir, pair_dir):
        self.input_URLs = input_URLs
        self.local_dir = local_dir
        self.shared_dir = shared_dir
        self.pair_dir = pair_dir

    def get_input_path(self, name):
        """
        Accepts filename. Downloads if not present. returns path to file.
        """
        # Get path to file
        shared = name != 'tumor.bam' and name != 'normal.bam'
        dir_path = self.shared_dir if shared else self.pair_dir
        file_path = os.path.join(dir_path, name)

        # Create necessary directories if not present
        self.mkdir_p(dir_path)

        # Check if file exists, download if not present
        if not os.path.exists(file_path):
            try:
                subprocess.check_call(['curl', '-fs', self.input_URLs[name], '-o', file_path])
            except subprocess.CalledProcessError:
                raise RuntimeError('\nNecessary file could not be acquired: {}. Check input URL')
            except OSError:
                raise RuntimeError('Failed to find "curl". Install via "apt-get install curl"')

        assert os.path.exists(file_path)

        return file_path

    def get_intermediate_path(self, name):

        # Get path to file
        shared = '.fai' in name or '.dict' in name
        dir_path = self.shared_dir if shared else self.pair_dir
        file_path = os.path.join(dir_path, name)

        # Create necessary directories if not present
        self.mkdir_p(dir_path)

        # Check if file exists, download if not present from s3
        if not os.path.exists(file_path):
            bucket_name = 'bd2k-{}'.format(os.path.basename(__file__).split('.')[0])
            try:
                conn = boto.connect_s3()
                bucket = conn.get_bucket(bucket_name)
                k = Key(bucket)
                k.name = file_path[len(self.local_dir):].strip('//')
            except:
                raise RuntimeError('Could not connect to S3 and retrieve bucket: {}'.format(bucket_name))

            try:
                k.get_contents_to_filename(file_path)
            except:
                raise RuntimeError('Contents from S3 could not be written to: {}'.format(file_path))

        return file_path

    def upload_to_S3(self, file_path):
        """
        file should be the path to the file, ex:  /mnt/jobtree/script/uuid4/pair/foo.vcf
        Files will be uploaded to: s3://bd2k-<script_name>/<UUID4> if shared
                              and: s3://bd2k-<script_name>/<UUID4>/<pair> if specific to that T/N pair.
        :param file_path: str
        """
        # Create S3 Object
        conn = boto.connect_s3()

        # Set bucket to bd2k-<script_name>
        bucket_name = 'bd2k-{}'.format(os.path.basename(__file__).split('.')[0])
        try:
            bucket = conn.get_bucket(bucket_name)
        except S3ResponseError as e:
            if e.error_code == 'NoSuchBucket':
                bucket = conn.create_bucket(bucket_name)
            else:
                raise e

        # Create Key Object -- reference intermediates placed in bucket root, all else in s3://bucket/<pair>
        k = Key(bucket)
        if not os.path.exists(file_path):
            raise RuntimeError('File at path: {}, does not exist'.format(file_path))

        # Derive the virtual folder and path for S3
        k.name = file_path[len(self.local_dir):].strip('//')

        # Upload to S3
        try:
            k.set_contents_from_filename(file_path)
        except:
            raise RuntimeError('File at path: {}, could not be uploaded to S3'.format(file_path))

    @staticmethod
    def mkdir_p(path):
        """
        The equivalent of mkdir -p
        https://github.com/BD2KGenomics/bd2k-python-lib/blob/master/src/bd2k/util/files.py
        """
        try:
            os.makedirs(path)
        except OSError as exc:
            if exc.errno == errno.EEXIST and os.path.isdir(path):
                pass
            else:
                raise


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

    # Create SupportGATK instance
    gatk = SupportGATK(input_URLs, local_dir, shared_dir, pair_dir)

    # Create JobTree Stack
    i = Stack(Target.makeTargetFn(start_node, (gatk,))).startJobTree(args)


if __name__ == "__main__":
    # from JobTree.jt_GATK import *
    main()

