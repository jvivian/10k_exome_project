# 4-13-15
# John Vivian

"""
Tree Structure of GATK Pipeline

     0-----> 11 ---- 12
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
12 = teardown / cleanup

1-10, and 12 are "Target children"
11 is a "Target follow-fn", it is executed after completion of children.

=========================================================================
:Directory Structure:

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

curl            - apt-get install curl
samtools        - apt-get install samtools
picard-tools    - apt-get install picard-tools
Active Internet Connection (Boto)
"""

import argparse
import errno
import multiprocessing
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
    parser.add_argument('-u', '--mutect', required=True, help='Mutect.jar')
    return parser


def start_node(target, gatk):
    """
    Create .dict/.fai for reference and start children/follow-on
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
        raise RuntimeError('\nFailed to find "samtools". \nInstall via "apt-get install samtools".')

    # Create dict file for reference genome (.dict)
    try:
        subprocess.check_call(['picard-tools', 'CreateSequenceDictionary',
                               'R={}'.format(reference),
                               'O={}.dict'.format(reference.split('.')[0])])
    except subprocess.CalledProcessError:
        raise RuntimeError('\nPicard failed to create reference dictionary')
    except OSError:
        raise RuntimeError('\nFailed to find "picard". \nInstall via "apt-get install picard-tools')

    # upload to S3
    gatk.upload_to_S3(reference + '.fai')
    gatk.upload_to_S3(reference.split('.')[0] + '.dict')

    # Spawn children and follow-on
    target.addChildTargetFn(normal_index, (gatk,))
    target.addChildTargetFn(tumor_index, (gatk,))
    #target.addFollowOnTargetFn(mutect, (gatk,))


def normal_index(target, gatk):
    """
    Create .bai file for normal.bam.
    samtools index normal.bam
    """

    # Retrieve normal.bam filepath
    normal = gatk.get_input_path('normal.bam')

    # Create index file for normal.bam (.bai)
    try:
        subprocess.check_call(['samtools', 'index', normal])
    except subprocess.CalledProcessError:
        raise RuntimeError('samtools failed to index BAM')
    except OSError:
        raise RuntimeError('Failed to find "samtools". Install via "apt-get install samtools"')

    # Upload to S3
    gatk.upload_to_S3(normal + '.bai')

    # Spawn child
    target.addChildTargetFn(normal_rtc, (gatk,))


def tumor_index(target, gatk):
    """
    Create .bai file for tumor.bam.
    samtools index tumor.bam
    """

    # Retrieve normal.bam filepath
    tumor = gatk.get_input_path('tumor.bam')

    # Create index file for normal.bam (.bai)
    try:
        subprocess.check_call(['samtools', 'index', tumor])
    except subprocess.CalledProcessError:
        raise RuntimeError('samtools failed to index BAM')
    except OSError:
        raise RuntimeError('Failed to find "samtools". Install via "apt-get install samtools"')

    # Upload to S3
    gatk.upload_to_S3(tumor + '.bai')

    # Spawn child
    target.addChildTargetFn(tumor_rtc, (gatk,))


def normal_rtc(target, gatk):
    """
    Creates normal.intervals file
    """
    # Retrieve input files
    gatk_jar = gatk.get_input_path('gatk.jar')
    ref = gatk.get_input_path('reference.fasta')
    phase = gatk.get_input_path('phase.vcf')
    mills = gatk.get_input_path('mills.vcf')
    normal = gatk.get_input_path('normal.bam')

    ref_fai = gatk.get_intermediate_path('reference.fasta.fai')
    ref_dict = gatk.get_intermediate_path('reference.fasta.dict')
    normal_bai = gatk.get_intermediate_path('normal.bam.bai')

    # Output File
    output = os.path.join(gatk.pair_dir, 'normal.intervals')

    # Create interval file
    try:
        subprocess.check_call(['java', '-Xmx15g', '-jar', gatk_jar, '-T', 'RealignerTargetCreator',
                               '-nt', str(gatk.cpu_count), '-R', ref, '-I', normal, '-known', phase,
                               '-known', mills, '--downsampling_type', 'NONE', '-o', output])
    except subprocess.CalledProcessError:
        raise RuntimeError('RealignerTargetCreator failed to finish')
    except OSError:
        raise RuntimeError('Failed to find "java" or gatk_jar')
    # Upload to S3
    gatk.upload_to_S3(output)

    # Spawn Child
    #target.addChildTargetFn(normal_ir, (gatk,))


def tumor_rtc(target, gatk):
    """
    Creates tumor.intervals file
    """
    # Retrieve input files
    gatk_jar = gatk.get_input_path('gatk.jar')
    ref = gatk.get_input_path('reference.fasta')
    phase = gatk.get_input_path('phase.vcf')
    mills = gatk.get_input_path('mills.vcf')
    tumor = gatk.get_input_path('tumor.bam')

    ref_fai = gatk.get_intermediate_path('reference.fasta.fai')
    ref_dict = gatk.get_intermediate_path('reference.fasta.dict')
    tumor_bai = gatk.get_intermediate_path('tumor.bam.bai')

    # Output File
    output = os.path.join(gatk.pair_dir, 'tumor.intervals')

    # Create interval file
    try:
        subprocess.check_call(['java', '-Xmx15g', '-jar', gatk_jar, '-T', 'RealignerTargetCreator',
                               '-nt', str(gatk.cpu_count), '-R', ref, '-I', tumor, '-known', phase,
                               '-known', mills, '--downsampling_type', 'NONE', '-o', output])
    except subprocess.CalledProcessError:
        raise RuntimeError('RealignerTargetCreator failed to finish')
    except OSError:
        raise RuntimeError('Failed to find "java" or gatk_jar')
    # Upload to S3
    gatk.upload_to_S3(output)

    # Spawn Child
    #target.addChildTargetFn(normal_ir, (gatk,))


def normal_ir(target, gatk):
    """
    Creates realigned normal bams
    """
    # Retrieve input files
    gatk_jar = gatk.get_input_path('gatk.jar')
    ref = gatk.get_input_path('reference.fasta')
    ref_fai = gatk.get_input_path('reference.fasta.fai')
    ref_dict = gatk.get_input_path('reference.fasta.dict')
    normal = gatk.get_input_path('normal.bam')
    normal_bai = gatk.get_input_path('normal.bam.bai')
    phase = gatk.get_input_path('phase.vcf')
    mills = gatk.get_input_path('mills.vcf')

    normal_intervals = gatk.get_intermediate_path('normal.intervals')

    # Output file
    output = os.path.join(gatk.pair_dir, 'normal.indel.bam')

    # Create interval file
    try:
        subprocess.check_call(['java', '-Xmx15g', '-jar', gatk_jar, '-T', 'IndelRealigner',
                               '-R', ref, '-I', normal, '-known', phase, '-known', mills,
                               '-targetIntervals', normal_intervals, '--downsampling_type', 'NONE',
                               'maxReads', str(720000), '-maxInMemory', str(5400000), '-o', output])
    except subprocess.CalledProcessError:
        raise RuntimeError('IndelRealignment failed to finish')
    except OSError:
        raise RuntimeError('Failed to find "java" or gatk_jar')
    # Upload to S3
    gatk.upload_to_S3(output)
    gatk.upload_to_S3(output + '.bai')

    # Spawn Child
    target.addChildTargetFn(normal_br, (gatk,))


def tumor_ir(target, gatk):
    """
    Creates realigned tumor bams
    """
    # Retrieve input files
    gatk_jar = gatk.get_input_path('gatk.jar')
    ref = gatk.get_input_path('reference.fasta')
    ref_fai = gatk.get_input_path('reference.fasta.fai')
    ref_dict = gatk.get_input_path('reference.fasta.dict')
    tumor = gatk.get_input_path('tumor.bam')
    tumor_bai = gatk.get_input_path('tumor.bam.bai')
    phase = gatk.get_input_path('phase.vcf')
    mills = gatk.get_input_path('mills.vcf')

    tumor_intervals = gatk.get_intermediate_path('tumor.intervals')

    # Output file
    output = os.path.join(gatk.pair_dir, 'tumor.indel.bam')

    # Create interval file
    try:
        subprocess.check_call(['java', '-Xmx15g', '-jar', gatk_jar, '-T', 'IndelRealigner',
                               '-R', ref, '-I', tumor, '-known', phase, '-known', mills,
                               '-targetIntervals', tumor_intervals, '--downsampling_type', 'NONE',
                               'maxReads', str(720000), '-maxInMemory', str(5400000), '-o', output])
    except subprocess.CalledProcessError:
        raise RuntimeError('IndelRealignment failed to finish')
    except OSError:
        raise RuntimeError('Failed to find "java" or gatk_jar')
    # Upload to S3
    gatk.upload_to_S3(output)
    gatk.upload_to_S3(output + '.bai')

    # Spawn Child
    target.addChildTargetFn(normal_br, (gatk,))


def normal_br(target, gatk):
    """
    Creates normal recal table
    """
    # Retrieve input files
    gatk_jar = gatk.get_input_path('gatk.jar')
    ref = gatk.get_input_path('reference.fasta')
    ref_fai = gatk.get_input_path('reference.fasta.fai')
    ref_dict = gatk.get_input_path('reference.fasta.dict')
    dbsnp = gatk.get_input_path('dbsnp.vcf')

    normal_indel = gatk.get_intermediate_path('normal.indel.bam')
    normal_bai = gatk.get_intermediate_path('normal.indel.bam.bai')

    # Output file
    output = os.path.join(gatk.pair_dir, 'normal.recal.table')

    # Create interval file
    try:
        subprocess.check_call(['java', '-Xmx15g', '-jar', gatk_jar, '-T', 'BaseRecalibrator',
                               '-nct', str(gatk.cpu_count), '-R', ref, '-I', normal_indel,
                               '-knownSites', dbsnp, '-o', output])
    except subprocess.CalledProcessError:
        raise RuntimeError('BaseRecalibrator failed to finish')
    except OSError:
        raise RuntimeError('Failed to find "java" or gatk_jar')
    # Upload to S3
    gatk.upload_to_S3(output)

    # Spawn Child
    target.addChildTargetFn(normal_pr, (gatk,))


def tumor_br(target, gatk):
    """
    Creates tumor recal table
    """
    # Retrieve input files
    gatk_jar = gatk.get_input_path('gatk.jar')
    ref = gatk.get_input_path('reference.fasta')
    ref_fai = gatk.get_input_path('reference.fasta.fai')
    ref_dict = gatk.get_input_path('reference.fasta.dict')
    dbsnp = gatk.get_input_path('dbsnp.vcf')

    tumor_indel = gatk.get_intermediate_path('tumor.indel.bam')
    tumor_bai = gatk.get_intermediate_path('tumor.indel.bam.bai')

    # Output file
    output = os.path.join(gatk.pair_dir, 'tumor.recal.table')

    # Create interval file
    try:
        subprocess.check_call(['java', '-Xmx15g', '-jar', gatk_jar, '-T', 'BaseRecalibrator',
                               '-nct', str(gatk.cpu_count), '-R', ref, '-I', tumor_indel,
                               '-knownSites', dbsnp, '-o', output])
    except subprocess.CalledProcessError:
        raise RuntimeError('BaseRecalibrator failed to finish')
    except OSError:
        raise RuntimeError('Failed to find "java" or gatk_jar')
    # Upload to S3
    gatk.upload_to_S3(output)

    # Spawn Child
    target.addChildTargetFn(normal_pr, (gatk,))


def normal_pr(target, gatk):
    """
    Create normal.bqsr.bam
    """
    # Retrieve input files
    gatk_jar = gatk.get_input_path('gatk.jar')
    ref = gatk.get_input_path('reference.fasta')
    ref_fai = gatk.get_input_path('reference.fasta.fai')
    ref_dict = gatk.get_input_path('reference.fasta.dict')

    normal_indel = gatk.get_intermediate_path('normal.indel.bam')
    normal_bai = gatk.get_intermediate_path('normal.indel.bam.bai')
    normal_recal = gatk.get_input_path('normal.recal.table')

    # Output file
    output = os.path.join(gatk.pair_dir, 'normal.bqsr.bam')

    # Create interval file
    try:
        subprocess.check_call(['java', '-Xmx15g', '-jar', gatk_jar, '-T', 'PrintReads',
                               '-nct', str(gatk.cpu_count), '-R', ref, '--emit_original_quals',
                               '-I', normal_indel, '-BQSR', normal_recal, '-o', output])
    except subprocess.CalledProcessError:
        raise RuntimeError('PrintReads failed to finish')
    except OSError:
        raise RuntimeError('Failed to find "java" or gatk_jar')

    # Upload to S3
    gatk.upload_to_S3(output)
    gatk.upload_to_S3(output + '.bai')


def tumor_pr(target, gatk):
    """
    Create tumor.bqsr.bam
    """
    # Retrieve input files
    gatk_jar = gatk.get_input_path('gatk.jar')
    ref = gatk.get_input_path('reference.fasta')
    ref_fai = gatk.get_input_path('reference.fasta.fai')
    ref_dict = gatk.get_input_path('reference.fasta.dict')

    tumor_indel = gatk.get_intermediate_path('tumor.indel.bam')
    tuor_bai = gatk.get_intermediate_path('tumor.indel.bam.bai')
    tumor_recal = gatk.get_input_path('tumor.recal.table')

    # Output file
    output = os.path.join(gatk.pair_dir, 'tumor.bqsr.bam')

    # Create interval file
    try:
        subprocess.check_call(['java', '-Xmx15g', '-jar', gatk_jar, '-T', 'PrintReads',
                               '-nct', str(gatk.cpu_count), '-R', ref, '--emit_original_quals',
                               '-I', tumor_indel, '-BQSR', tumor_recal, '-o', output])
    except subprocess.CalledProcessError:
        raise RuntimeError('PrintReads failed to finish')
    except OSError:
        raise RuntimeError('Failed to find "java" or gatk_jar')

    # Upload to S3
    gatk.upload_to_S3(output)
    gatk.upload_to_S3(output + '.bai')


def mutect(target, gatk):
    """
    Create output VCF
    """
    # Retrieve input files
    ref = gatk.get_input_path('reference.fasta')
    ref_fai = gatk.get_input_path('reference.fasta.fai')
    ref_dict = gatk.get_input_path('reference.fasta.dict')
    dbsnp = gatk.get_input_path('dbsnp.vcf')
    cosmic = gatk.get_input_path('cosmic.vcf')
    mutect = gatk.get_input_path('mutect.vcf')

    normal_bqsr = gatk.get_intermediate_path('normal.bqsr.bam')
    normal_bai = gatk.get_intermediate_path('normal.bqsr.bam.bai')
    tumor_bqsr = gatk.get_intermediate_path('tumor.bqsr.bam')
    tumor_bai = gatk.get_intermediate_path('tumor.bqsr.bam.bai')

    # Output file
    normal_UUID = gatk.input_URLs['normal.bam'].split('/')[-1].split('.')[0]
    tumor_UUID = gatk.input_URLs['tumor.bam'].split('/')[-1].split('.')[0]

    output = os.path.join(gatk.pair_dir, '{}-normal:{}-tumor.vcf'.format(normal_UUID, tumor_UUID))
    mut_out = os.path.join(gatk.pair_dir, 'mutect.out')
    mut_cov = os.path.join(gatk.pair_dir, 'mutect.coverage')

    # Create interval file
    try:
        subprocess.check_call(['java', '-Xmx15g', '-jar', mutect, '--analysis_type', 'MuTect',
                               '--reference_sequence', ref, '--cosmic', cosmic, '--tumor_lod', str(10),
                               '--dbsnp', dbsnp, 'input_file:normal', normal_bqsr,
                               'input_file:tumor', tumor_bqsr, '--out', mut_out,
                               '--coverage_file', mut_cov, '--vcf', output])
    except subprocess.CalledProcessError:
        raise RuntimeError('Mutect failed to finish')
    except OSError:
        raise RuntimeError('Failed to find "java" or mutect.jar')
    # Upload to S3
    gatk.upload_to_S3(output)

    # Spawn Child
    if gatk.cleanUp:
        target.addChildTargetFn(teardown, (gatk,))


def teardown(target, gatk):

    # Remove local files

    # Remove intermediate S3 files
    pass

class SupportGATK(object):
    """
    Class to encapsulate all necessary data structures and methods used in the pipeline.
    """

    def __init__(self, input_URLs, local_dir, shared_dir, pair_dir, cleanUp=False):
        self.input_URLs = input_URLs
        self.local_dir = local_dir
        self.shared_dir = shared_dir
        self.pair_dir = pair_dir
        self.cpu_count = multiprocessing.cpu_count()
        self.cleanUp = cleanUp

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
                  'gatk.jar': args.gatk,
                  'mutect.jar' : args.mutect}

    # Ensure user supplied URLs to files and that BAMs are in the appropriate format
    for input in input_URLs:
        if ".com" not in input_URLs[input]:
            sys.stderr.write("Invalid Input: {}".format(input))
            raise RuntimeError("Inputs must be valid URLs, please check inputs.")
        if input == 'normal' or input == 'tumor':
            if len(input_URLs[input].split('/')[-1].split('.')) != 3:
                raise RuntimeError('{} BAM is not in the appropriate format: \
                UUID.normal.bam or UUID.tumor.bam'.format(input))

    # Create directories for shared files and for isolating pairs
    shared_dir = os.path.join(local_dir, os.path.basename(__file__).split('.')[0], str(uuid.uuid4()))
    pair_dir = os.path.join(shared_dir, input_URLs['normal.bam'].split('/')[-1].split('.')[0] +
                            '-normal:' + input_URLs['tumor.bam'].split('/')[-1].split('.')[0] + '-tumor')

    # Create SupportGATK instance
    gatk = SupportGATK(input_URLs, local_dir, shared_dir, pair_dir)

    # Create JobTree Stack
    i = Stack(Target.makeTargetFn(start_node, (gatk,))).startJobTree(args)


if __name__ == "__main__":
    # from JobTree.jt_GATK import *
    main()