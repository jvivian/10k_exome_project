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
11 is a "Target follow-on", it is executed after completion of children.

=========================================================================
:Directory Structure:

local_dir = /mnt/

# For "shared" input files
shared_dir = <local_dir>/<script_name>/<UUID4>

# For files specific to a tumor/normal pair
pair_dir = <local_dir>/<script_name>/<UUID4>/<pair>/
    <pair> is defined as UUID-normal:UUID-tumor

files are uploaded to:
    s3://bd2k-<script>/<UUID4>/ if shared (.fai/.dict)
    s3://bd2k-<script>/<UUID4>/<pair> if specific to that T/N pair.

=========================================================================
:Dependencies:

curl            - apt-get install curl
samtools        - apt-get install samtools
picard-tools    - apt-get install picard-tools
boto            - pip install boto
FileChunkIO     - pip install FileChunkIO
jobTree         - https://github.com/benedictpaten/jobTree
Active Internet Connection (Boto)
"""

import argparse
import errno
import multiprocessing
import os
import subprocess
import uuid

from jobTree.src.stack import Stack
from jobTree.src.target import Target


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
    parser.add_argument('-w', '--work_dir', required=True, help='Where you wanna work from? (full path please)')
    return parser


class SupportGATK(object):
    def __init__(self, input_urls, args, cleanup=False):
        self.input_urls = input_urls
        self.args = args
        self.cleanup = cleanup
        self.cpu_count = multiprocessing.cpu_count()
        self.work_dir = os.path.join(str(self.args.work_dir),
                                     'bd2k-{}'.format(os.path.basename(__file__).split('.')[0]),
                                     str(uuid.uuid4()))

    def unavoidable_download_method(self, name):
        """
        Accepts filename. Downloads if not present. returns path to file.
        """
        # Get path to file
        file_path = os.path.join(self.work_dir, name)

        # Create necessary directories if not present
        self.mkdir_p(self.work_dir)

        # Check if file exists, download if not presente
        if not os.path.exists(file_path):
            try:
                subprocess.check_call(['curl', '-fs', self.input_urls[name], '-o', file_path])
            except subprocess.CalledProcessError:
                raise RuntimeError('\nNecessary file could not be acquired: {}. Check input URL')
            except OSError:
                raise RuntimeError('Failed to find "curl". Install via "apt-get install curl"')

        assert os.path.exists(file_path)

        return file_path

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


def start_node(target, gatk):
    """
    Create .dict/.fai for reference and start children/follow-on
    """
    ref_path = gatk.unavoidable_download_method('reference.fasta')
    gatk.ref_fasta = target.writeGlobalFile(ref_path)

    # Create index file for reference genome (.fai)
    try:
        subprocess.check_call(['samtools', 'faidx', ref_path])
    except subprocess.CalledProcessError:
        raise RuntimeError('\nsamtools failed to create reference index!')
    except OSError:
        raise RuntimeError('\nFailed to find "samtools". \nInstall via "apt-get install samtools".')

    # Create dict file for reference genome (.dict)
    try:
        subprocess.check_call(['picard-tools', 'CreateSequenceDictionary',
                               'R={}'.format(ref_path),
                               'O={}.dict'.format(os.path.splitext(ref_path)[0])])
    except subprocess.CalledProcessError:
        raise RuntimeError('\nPicard failed to create reference dictionary')
    except OSError:
        raise RuntimeError('\nFailed to find "picard". \nInstall via "apt-get install picard-tools')

    # create FileStoreIDs
    gatk.ref_fai = target.writeGlobalFile(ref_path + '.fai')
    gatk.ref_dict = target.writeGlobalFile(os.path.splitext(ref_path)[0] + '.dict')

    # Spawn children and follow-on
    target.addChildTargetFn(normal_index, (gatk,))
    target.addChildTargetFn(tumor_index, (gatk,))
    target.setFollowOnTargetFn(mutect, (gatk,))


def normal_index(target, gatk):
    """
    Create .bai file for normal.bam
    """
    # Retrieve input bam
    normal_path = gatk.unavoidable_download_method('normal.bam')
    gatk.normal_bam = target.writeGlobalFile(normal_path)

    # Create index file for normal.bam (.bai)
    try:
        subprocess.check_call(['samtools', 'index', normal_path])
    except subprocess.CalledProcessError:
        raise RuntimeError('samtools failed to index BAM')
    except OSError:
        raise RuntimeError('Failed to find "samtools". Install via "apt-get install samtools"')

    # Create FileStoreIDs for output
    gatk.normal_bai = target.writeGlobalFile(normal_path + '.bai')

    # Spawn child
    target.addChildTargetFn(normal_rtc, (gatk,))


def tumor_index(target, gatk):
    """
    Create .bai file for tumor.bam
    """
    # Retrieve input bam
    tumor_path = gatk.unavoidable_download_method('tumor.bam')
    gatk.tumor_bam = target.writeGlobalFile(tumor_path)

    # Create index file for normal.bam (.bai)
    try:
        subprocess.check_call(['samtools', 'index', tumor_path])
    except subprocess.CalledProcessError:
        raise RuntimeError('samtools failed to index BAM')
    except OSError:
        raise RuntimeError('Failed to find "samtools". Install via "apt-get install samtools"')

    # Create FileStoreID for output
    gatk.tumor_bai = target.writeGlobalFile(tumor_path + '.bai')

    # Spawn child
    target.addChildTargetFn(tumor_rtc, (gatk,))


def normal_rtc(target, gatk):
    """
    Creates normal.intervals file
    """
    # Download files not in FileStore
    gatk_path = gatk.unavoidable_download_method('gatk.jar')
    phase_path = gatk.unavoidable_download_method('phase.vcf')
    mills_path = gatk.unavoidable_download_method('mills.vcf')

    # Store in FileStore
    gatk.gatk_jar = target.writeGlobalFile(gatk_path)
    gatk.phase_vcf = target.writeGlobalFile(phase_path)
    gatk.mills_vcf = target.writeGlobalFile(mills_path)

    # Retrieve paths for files not in FileStore
    ref_fasta = read_and_rename_global_file(target, gatk.ref_fasta, '.fasta')
    normal_bam = read_and_rename_global_file(target, gatk.normal_bam, '.bam')
    normal_bai = read_and_rename_global_file(target, gatk.normal_bai, '.bai', normal_bam)
    ref_dict = read_and_rename_global_file(target, gatk.ref_dict, '.dict', ref_fasta)
    ref_fai = read_and_rename_global_file(target, gatk.ref_fai, '.fasta.fai', ref_fasta)

    with open('normal_RTC_log.txt', 'w') as f:
        f.write('Ref path: {}\ndict path: {}\nlistdir: {}\n'.format(ref_fasta, ref_dict, os.listdir(os.path.split(ref_fasta)[0])))
        f.write('\nRef Exists: {}\ndict exists: {}'.format(os.path.exists(ref_fasta), os.path.exists(ref_dict)))

    # Output File
    output = os.path.join(gatk.work_dir, 'normal.intervals')

    # Create interval file
    try:
        subprocess.check_call(['java', '-Xmx15g', '-jar', gatk_path, '-T', 'RealignerTargetCreator',
                               '-nt', str(gatk.cpu_count), '-R', ref_fasta, '-I', normal_bam, '-known', phase_path,
                               '-known', mills_path, '--downsampling_type', 'NONE', '-o', output])
    except subprocess.CalledProcessError:
        raise RuntimeError('RealignerTargetCreator failed to finish')
    except OSError:
        raise RuntimeError('Failed to find "java" or gatk_jar')

    # Create FileStore ID for output
    gatk.normal_intervals = target.writeGlobalFile(output)

    # Spawn Child
    target.addChildTargetFn(normal_ir, (gatk,))


def tumor_rtc(target, gatk):
    """
    Creates tumor.intervals file
    """
    # Download files not in FileStore
    gatk_path = gatk.unavoidable_download_method('gatk.jar')
    phase_path = gatk.unavoidable_download_method('phase.vcf')
    mills_path = gatk.unavoidable_download_method('mills.vcf')

    # Store in FileStore
    gatk.gatk_jar = target.writeGlobalFile(gatk_path)
    gatk.phase_vcf = target.writeGlobalFile(phase_path)
    gatk.mills_vcf = target.writeGlobalFile(mills_path)

    # Retrieve paths for files not in FileStore
    ref_fasta = read_and_rename_global_file(target, gatk.ref_fasta, '.fasta')
    tumor_bam = read_and_rename_global_file(target, gatk.tumor_bam, '.bam')
    tumor_bai = read_and_rename_global_file(target, gatk.tumor_bai, '.bai', tumor_bam)
    ref_dict = read_and_rename_global_file(target, gatk.ref_dict, '.dict', ref_fasta)
    ref_fai = read_and_rename_global_file(target, gatk.ref_fai, '.fasta.fai', ref_fasta)

    with open('tumor_RTC_log.txt', 'w') as f:
        f.write('Ref path: {}\ndict path: {}\nlistdir: {}\n'.format(ref_fasta, ref_dict, os.listdir(os.path.split(ref_fasta)[0])))
        f.write('\nRef Exists: {}\ndict exists: {}'.format(os.path.exists(ref_fasta), os.path.exists(ref_dict)))

    # Output File
    output = os.path.join(gatk.work_dir, 'tumor.intervals')

    # Create interval file
    try:
        subprocess.check_call(['java', '-Xmx15g', '-jar', gatk_path, '-T', 'RealignerTargetCreator',
                               '-nt', str(gatk.cpu_count), '-R', ref_fasta, '-I', tumor_bam, '-known', phase_path,
                               '-known', mills_path, '--downsampling_type', 'NONE', '-o', output])
    except subprocess.CalledProcessError:
        raise RuntimeError('RealignerTargetCreator failed to finish')
    except OSError:
        raise RuntimeError('Failed to find "java" or gatk_jar')

    # Create FileStoreID for output
    gatk.tumor_intervals = target.writeGlobalFile(output)

    # Spawn Child
    target.addChildTargetFn(tumor_ir, (gatk,))


def normal_ir(target, gatk):
    """
    Creates realigned normal bams
    """
    # Retrieve paths from FileStoreID
    gatk_jar = read_and_rename_global_file(target, gatk.gatk_jar, '.jar')
    phase_vcf = read_and_rename_global_file(target, gatk.phase_vcf, '.vcf')
    mills_vcf = read_and_rename_global_file(target, gatk.mills_vcf, '.vcf')
    ref_fasta = read_and_rename_global_file(target, gatk.ref_fasta, '.fasta')
    ref_fai = read_and_rename_global_file(target, gatk.ref_fai, '.fai', ref_fasta)
    ref_dict = read_and_rename_global_file(target, gatk.ref_dict, '.dict', ref_fasta)
    normal_bam = read_and_rename_global_file(target, gatk.normal_bam, '.bam')
    normal_bai = read_and_rename_global_file(target, gatk.normal_bai, '.bai', normal_bam)
    normal_intervals = read_and_rename_global_file(target, gatk.normal_intervals, '.intervals')

    # Output file
    output = os.path.join(gatk.work_dir, 'normal.indel.bam')

    # Create interval file
    try:
        subprocess.check_call(['java', '-Xmx15g', '-jar', gatk_jar, '-T', 'IndelRealigner',
                               '-R', ref_fasta, '-I', normal_bam, '-known', phase_vcf, '-known', mills_vcf,
                               '-targetIntervals', normal_intervals, '--downsampling_type', 'NONE',
                               '-maxReads', str(720000), '-maxInMemory', str(5400000), '-o', output])
    except subprocess.CalledProcessError:
        raise RuntimeError('IndelRealignment failed to finish')
    except OSError:
        raise RuntimeError('Failed to find "java" or gatk_jar')

    # Create FileStoreID for output
    gatk.normal_indel_bam = target.writeGlobalFile(output)
    gatk.normal_indel_bai = target.writeGlobalFile(os.path.splitext(output)[0] + '.bai')

    # Spawn Child
    target.addChildTargetFn(normal_cleanup_bam, (gatk,))


def tumor_ir(target, gatk):
    """
    Creates realigned tumor bams
    """
    # Retrieve paths from FileStoreID
    gatk_jar = read_and_rename_global_file(target, gatk.gatk_jar, '.jar')
    phase_vcf = read_and_rename_global_file(target, gatk.phase_vcf, '.vcf')
    mills_vcf = read_and_rename_global_file(target, gatk.mills_vcf, '.vcf')
    ref_fasta = read_and_rename_global_file(target, gatk.ref_fasta, '.fasta')
    ref_fai = read_and_rename_global_file(target, gatk.ref_fai, '.fai', ref_fasta)
    ref_dict = read_and_rename_global_file(target, gatk.ref_dict, '.dict', ref_fasta)
    tumor_bam = read_and_rename_global_file(target, gatk.tumor_bam, '.bam')
    tumor_bai = read_and_rename_global_file(target, gatk.tumor_bai, '.bai', tumor_bam)
    tumor_intervals = read_and_rename_global_file(target, gatk.tumor_intervals, '.intervals')

    # Output file
    output = os.path.join(gatk.work_dir, 'tumor.indel.bam')

    # Create interval file
    try:
        subprocess.check_call(['java', '-Xmx15g', '-jar', gatk_jar, '-T', 'IndelRealigner',
                               '-R', ref_fasta, '-I', tumor_bam, '-known', phase_vcf, '-known', mills_vcf,
                               '-targetIntervals', tumor_intervals, '--downsampling_type', 'NONE',
                               '-maxReads', str(720000), '-maxInMemory', str(5400000), '-o', output])
    except subprocess.CalledProcessError:
        raise RuntimeError('IndelRealignment failed to finish')
    except OSError:
        raise RuntimeError('Failed to find "java" or gatk_jar')

    # Create FileStoreID for output
    gatk.tumor_indel_bam = target.writeGlobalFile(output)
    gatk.tumor_indel_bai = target.writeGlobalFile(os.path.splitext(output)[0] + '.bai')

    # Spawn Child
    target.addChildTargetFn(tumor_cleanup_start, (gatk,))


def normal_cleanup_bam(target, gatk):
    """
    remove intermediate files to reduce storage costs and keep disk space free
    """
    # Remove locally
    os.remove(os.path.join(gatk.work_dir, 'normal.bam'))

    target.addChildTargetFn(normal_br, (gatk,))


def tumor_cleanup_start(target, gatk):
    # Remove locally
    os.remove(os.path.join(gatk.work_dir, 'tumor.bam'))

    target.addChildTargetFn(tumor_br, (gatk,))


def normal_br(target, gatk):
    """
    Creates normal recal table
    """
    # Download files not in FileStore
    dbsnp_path = gatk.unavoidable_download_method('dbsnp.vcf')

    # Assign FileStoreID
    gatk.dbsnp_vcf = target.writeGlobalFile(dbsnp_path)

    # Retrieve paths via FileStoreID
    gatk_jar = read_and_rename_global_file(target, gatk.gatk_jar, '.jar')
    ref_fasta = read_and_rename_global_file(target, gatk.ref_fasta, '.fasta')
    ref_fai = read_and_rename_global_file(target, gatk.ref_fai, '.fai', ref_fasta)
    ref_dict = read_and_rename_global_file(target, gatk.ref_dict, '.dict', ref_fasta)
    normal_indel_bam = read_and_rename_global_file(target, gatk.normal_indel_bam, '.bam')
    normal_indel_bai = read_and_rename_global_file(target, gatk.normal_indel_bai, '.bai', normal_indel_bam)

    # Output file
    output = os.path.join(gatk.work_dir, 'normal.recal.table')

    # Create interval file
    try:
        subprocess.check_call(['java', '-Xmx7g', '-jar', gatk_jar, '-T', 'BaseRecalibrator',
                               '-nct', str(gatk.cpu_count), '-R', ref_fasta, '-I', normal_indel_bam,
                               '-knownSites', dbsnp_path, '-o', output])
    except subprocess.CalledProcessError:
        raise RuntimeError('BaseRecalibrator failed to finish')
    except OSError:
        raise RuntimeError('Failed to find "java" or gatk_jar')

    # Create FileStoreID for output
    gatk.normal_recal = target.writeGlobalFile(output)

    # Spawn Child
    target.addChildTargetFn(normal_pr, (gatk,))


def tumor_br(target, gatk):
    """
    Creates tumor recal table
    """
    # Download files not in FileStore
    dbsnp_path = gatk.unavoidable_download_method('dbsnp.vcf')

    # Assign FileStoreID
    gatk.dbsnp_vcf = target.writeGlobalFile(dbsnp_path)

    # Retrieve paths via FileStoreID
    gatk_jar = read_and_rename_global_file(target, gatk.gatk_jar, '.jar')
    ref_fasta = read_and_rename_global_file(target, gatk.ref_fasta, '.fasta')
    ref_fai = read_and_rename_global_file(target, gatk.ref_fai, '.fai', ref_fasta)
    ref_dict = read_and_rename_global_file(target, gatk.ref_dict, '.dict', ref_fasta)
    tumor_indel_bam = read_and_rename_global_file(target, gatk.tumor_indel_bam, '.bam')
    tumor_indel_bai = read_and_rename_global_file(target, gatk.tumor_indel_bai, '.bai', tumor_indel_bam)

    # Output file
    output = os.path.join(gatk.work_dir, 'tumor.recal.table')

    # Create interval file
    try:
        subprocess.check_call(['java', '-Xmx7g', '-jar', gatk_jar, '-T', 'BaseRecalibrator',
                               '-nct', str(gatk.cpu_count), '-R', ref_fasta, '-I', tumor_indel_bam,
                               '-knownSites', dbsnp_path, '-o', output])
    except subprocess.CalledProcessError:
        raise RuntimeError('BaseRecalibrator failed to finish')
    except OSError:
        raise RuntimeError('Failed to find "java" or gatk_jar')

    # Create FileStoreID for output
    gatk.tumor_recal = target.writeGlobalFile(output)

    # Spawn Child
    target.addChildTargetFn(tumor_pr, (gatk,))


def normal_pr(target, gatk):
    """
    Create normal.bqsr.bam
    """
    gatk_jar = read_and_rename_global_file(target, gatk.gatk_jar, '.jar')
    ref_fasta = read_and_rename_global_file(target, gatk.ref_fasta, '.fasta')
    ref_fai = read_and_rename_global_file(target, gatk.ref_fai, '.fai', ref_fasta)
    ref_dict = read_and_rename_global_file(target, gatk.ref_dict, '.dict', ref_fasta)
    normal_indel_bam = read_and_rename_global_file(target, gatk.normal_indel_bam, '.bam')
    normal_indel_bai = read_and_rename_global_file(target, gatk.normal_indel_bai, '.bai', normal_indel_bam)
    normal_recal = read_and_rename_global_file(target, gatk.normal_recal, '.table')

    # Output file
    output = os.path.join(gatk.work_dir, 'normal.bqsr.bam')

    # Create interval file
    try:
        subprocess.check_call(['java', '-Xmx7g', '-jar', gatk_jar, '-T', 'PrintReads',
                               '-nct', str(gatk.cpu_count), '-R', ref_fasta, '--emit_original_quals',
                               '-I', normal_indel_bam, '-BQSR', normal_recal, '-o', output])
    except subprocess.CalledProcessError:
        raise RuntimeError('PrintReads failed to finish')
    except OSError:
        raise RuntimeError('Failed to find "java" or gatk_jar')

    # Create FileStoreID for output
    gatk.normal_bqsr_bam = target.writeGlobalFile(output)
    gatk.normal_bqsr_bai = target.writeGlobalFile(os.path.splitext(output)[0] + '.bai')

    target.addChildTargetFn(normal_indel_cleaup, (gatk,))


def tumor_pr(target, gatk):
    """
    Create tumor.bqsr.bam
    """
    # Retrieve paths via FileStoreID
    gatk_jar = read_and_rename_global_file(target, gatk.gatk_jar, '.jar')
    ref_fasta = read_and_rename_global_file(target, gatk.ref_fasta, '.fasta')
    ref_fai = read_and_rename_global_file(target, gatk.ref_fai, '.fai', ref_fasta)
    ref_dict = read_and_rename_global_file(target, gatk.ref_dict, '.dict', ref_fasta)
    tumor_indel_bam = read_and_rename_global_file(target, gatk.tumor_indel_bam, '.bam')
    tumor_indel_bai = read_and_rename_global_file(target, gatk.tumor_indel_bai, '.bai', tumor_indel_bam)
    tumor_recal = read_and_rename_global_file(target, gatk.tumor_recal, '.table')

    # Output file
    output = os.path.join(gatk.work_dir, 'tumor.bqsr.bam')

    # Create interval file
    try:
        subprocess.check_call(['java', '-Xmx7g', '-jar', gatk_jar, '-T', 'PrintReads',
                               '-nct', str(gatk.cpu_count), '-R', ref_fasta, '--emit_original_quals',
                               '-I', tumor_indel_bam, '-BQSR', tumor_recal, '-o', output])
    except subprocess.CalledProcessError:
        raise RuntimeError('PrintReads failed to finish')
    except OSError:
        raise RuntimeError('Failed to find "java" or gatk_jar')

    # Create FileStoreID for output
    gatk.tumor_bqsr_bam = target.writeGlobalFile(output)
    gatk.tumor_bqsr_bai = target.writeGlobalFile(os.path.splitext(output)[0] + '.bai')

    target.addChildTargetFn(tumor_indel_cleanup, (gatk,))


def normal_indel_cleaup(target, gatk):
    # Remove locally
    os.remove(os.path.join(gatk.work_dir, 'normal.indel.bam'))


def tumor_indel_cleanup(target, gatk):
    # Remove locally
    os.remove(os.path.join(gatk.work_dir, 'tumor.indel.bam'))


def mutect(target, gatk):
    """
    Create output VCF
    """
    # Download files not in FileStore
    cosmic_path = gatk.unavoidable_download_method('cosmic.vcf')
    mutect_path = gatk.unavoidable_download_method('gatk.jar')

    # Add to FileStore
    cosmic_vcf = target.writeGlobalFile(cosmic_path)
    mutect_jar = target.writeGlobalFile(mutect_path)

    # Retrieve paths from FileStore
    normal_bqsr_bam = read_and_rename_global_file(target, gatk.normal_bqsr_bam, '.bam')
    normal_bqsr_bai = read_and_rename_global_file(target, gatk.normal_bqsr_bai, '.bai', normal_bqsr_bam)
    tumor_bqsr_bam = read_and_rename_global_file(target, gatk.tumor_bqsr_bam, '.bam')
    tumor_bqsr_bai = read_and_rename_global_file(target, gatk.tumor_bqsr_bai, '.bai', tumor_bqsr_bam)
    dbsnp_vcf = read_and_rename_global_file(target, gatk.dbsnb_vcf, '.vcf')
    ref_fasta = read_and_rename_global_file(target, gatk.ref_fasta, '.fasta')
    ref_fai = read_and_rename_global_file(target, gatk.ref_fai, '.fai', ref_fasta)
    ref_dict = read_and_rename_global_file(target, gatk.ref_dict, '.dict', ref_fasta)

    # Output files
    normal_uuid = gatk.input_URLs['normal.bam'].split('/')[-1].split('.')[0]
    tumor_uuid = gatk.input_URLs['tumor.bam'].split('/')[-1].split('.')[0]

    output = os.path.join(gatk.work_dir, '{}-normal:{}-tumor.vcf'.format(normal_uuid, tumor_uuid))
    mut_out = os.path.join(gatk.work_dir, 'mutect.out')
    mut_cov = os.path.join(gatk.work_dir, 'mutect.coverage')

    # Create interval file
    try:
        subprocess.check_call(['java', '-Xmx15g', '-jar', mutect_path, '--analysis_type', 'MuTect',
                               '--reference_sequence', ref_fasta, '--cosmic', cosmic_path, '--tumor_lod', str(10),
                               '--dbsnp', dbsnp_vcf, '--input_file:normal', normal_bqsr_bam,
                               '--input_file:tumor', tumor_bqsr_bam, '--out', mut_out,
                               '--coverage_file', mut_cov, '--vcf', output])
    except subprocess.CalledProcessError:
        raise RuntimeError('Mutect failed to finish')
    except OSError:
        raise RuntimeError('Failed to find "java" or mutect.jar')

    # Create FileStoreID for output
    gatk.mutect_vcf = target.writeGlobalFile(output)
    gatk.mutect_out = target.writeGlobalFile(mut_out)
    gatk.mutect_cov = target.writeGlobalFile(mut_cov)

    # Spawn Child
    if gatk.cleanup:
        target.addChildTargetFn(teardown, (gatk,))


def teardown(target, gatk):
    # Remove files from local working directory
    files = [os.path.join(gatk.work_dir, f) for f in os.listdir(gatk.work_dir)
             if 'tumor.vcf' not in f and os.path.isfile(f)]
    for f in files:
        os.remove(f)


def read_and_rename_global_file(target, fileStoreId, new_extension, diff_name=None):
    name = target.readGlobalFile(fileStoreId)
    new_name = (name if diff_name is None else diff_name) + new_extension
    os.rename(name, new_name)
    return new_name


def main():

    # Handle parser logic
    parser = build_parser()
    Stack.addJobTreeOptions(parser)
    args = parser.parse_args()

    input_urls = {'reference.fasta': args.reference,
              'normal.bam': args.normal,
              'tumor.bam': args.tumor,
              'phase.vcf': args.phase,
              'mills.vcf': args.mills,
              'dbsnp.vcf': args.dbsnp,
              'cosmic.vcf': args.cosmic,
              'gatk.jar': args.gatk,
              'mutect.jar': args.mutect}

    # Ensure user supplied URLs to files and that BAMs are in the appropriate format
    for bam in [args.normal, args.tumor]:
        if len(bam.split('/')[-1].split('.')) != 3:
            raise RuntimeError('{} BAM is not in the appropriate format: \
            UUID.normal.bam or UUID.tumor.bam'.format(str(bam).split('.')[1]))

    gatk = SupportGATK(input_urls, args)

    # Create JTree Stack
    i = Stack(Target.makeTargetFn(start_node, (gatk,))).startJobTree(args)

    #if i != 0:
    #    raise RuntimeError("Failed Jobs")


if __name__ == "__main__":
    #from jobtree_gatk_pipeline import *
    main()
