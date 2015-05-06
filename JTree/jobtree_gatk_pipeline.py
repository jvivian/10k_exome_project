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

work_dir = '/mnt/bd2k-<script name>/<UUID4>/'

Each invocation of the script gets its own directory (via randomly generated UUID4)

=========================================================================
:Dependencies:

curl            - apt-get install curl
samtools        - apt-get install samtools
picard-tools    - apt-get install picard-tools
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


def read_and_rename_global_file(target, file_store_id, new_extension, diff_name=None):
    name = target.readGlobalFile(file_store_id)
    new_name = os.path.splitext(name if diff_name is None else diff_name)[0] + new_extension
    os.rename(name, new_name)
    return new_name


class HannesDict(dict):
    """
    >>> d = HannesDict()
    >>> isinstance(d, dict)
    True
    >>> d.foo = 187
    >>> d['foo']
    187
    """
    def __getattr__(self, name):
        try:
            return self[name]
        except KeyError:
            raise AttributeError()

    def __setattr__(self, name, value):
        self[name] = value


class SupportGATK(object):
    """
    This support class encapsulates information that is used by all children/follow-ons in the GATK pipeline.
    """
    def __init__(self, target, args, input_urls, symbolic_input_names, cleanup=False):
        self.input_urls = input_urls
        self.args = args
        self.cleanup = cleanup
        self.cpu_count = multiprocessing.cpu_count()
        self.work_dir = os.path.join(str(self.args.work_dir),
                                     'bd2k-{}'.format(os.path.basename(__file__).split('.')[0]),
                                     str(uuid.uuid4()))

        # Special dictioanary that essentially acts as a namedtuple but is capable of being pickled
        # Key = symbolic name for input
        # Value = FileStoreID.  This FileStoreID is linked to a file via target.updateGlobalFile()
        self.ids = HannesDict( (name, target.getEmptyFileStoreID()) for name in symbolic_input_names )

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


def start_node(target, args, input_urls, symbolic_input_names):
    """
    Create .dict/.fai for reference and start children/follow-on
    """
    # Construct instance of Support class that will be passed to children / follow-ons
    gatk = SupportGATK(target, args, input_urls, symbolic_input_names, cleanup=True)

    ref_path = gatk.unavoidable_download_method('reference.fasta')
    target.updateGlobalFile(gatk.ids.ref_fasta, ref_path)

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

    # Update FileStoreIDs
    target.updateGlobalFile(gatk.ids.ref_fai, ref_path + '.fai')
    target.updateGlobalFile(gatk.ids.ref_dict, os.path.splitext(ref_path)[0] + '.dict')

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
    target.updateGlobalFile(gatk.ids.normal_bam, normal_path)

    # Create index file for normal.bam (.bai)
    try:
        subprocess.check_call(['samtools', 'index', normal_path])
    except subprocess.CalledProcessError:
        raise RuntimeError('samtools failed to index BAM')
    except OSError:
        raise RuntimeError('Failed to find "samtools". Install via "apt-get install samtools"')

    # Update FileStoreID for output
    target.updateGlobalFile(gatk.ids.normal_bai, normal_path + '.bai')

    # Spawn child
    target.addChildTargetFn(normal_rtc, (gatk,))


def tumor_index(target, gatk):
    """
    Create .bai file for tumor.bam
    """
    # Retrieve input bam
    tumor_path = gatk.unavoidable_download_method('tumor.bam')
    target.updateGlobalFile(gatk.ids.tumor_bam, tumor_path)

    # Create index file for normal.bam (.bai)
    try:
        subprocess.check_call(['samtools', 'index', tumor_path])
    except subprocess.CalledProcessError:
        raise RuntimeError('samtools failed to index BAM')
    except OSError:
        raise RuntimeError('Failed to find "samtools". Install via "apt-get install samtools"')

    # Create FileStoreID for output
    target.updateGlobalFile(gatk.ids.tumor_bai, tumor_path + '.bai')

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

    # Update FileStore
    target.updateGlobalFile(gatk.ids.gatk_jar, gatk_path)
    target.updateGlobalFile(gatk.ids.phase_vcf, phase_path)
    target.updateGlobalFile(gatk.ids.mills_vcf, mills_path)

    # Retrieve paths for files not in FileStore
    ref_fasta = read_and_rename_global_file(target, gatk.ids.ref_fasta, '.fasta')
    normal_bam = read_and_rename_global_file(target, gatk.ids.normal_bam, '.bam')
    normal_bai = read_and_rename_global_file(target, gatk.ids.normal_bai, '.bai', normal_bam)
    ref_dict = read_and_rename_global_file(target, gatk.ids.ref_dict, '.dict', ref_fasta)
    ref_fai = read_and_rename_global_file(target, gatk.ids.ref_fai, '.fasta.fai', ref_fasta)

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
    target.updateGlobalFile(gatk.ids.normal_intervals, output)

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

    # Update FileStore
    target.updateGlobalFile(gatk.ids.gatk_jar, gatk_path)
    target.updateGlobalFile(gatk.ids.phase_vcf, phase_path)
    target.updateGlobalFile(gatk.ids.mills_vcf, mills_path)

    # Retrieve paths for files not in FileStore
    ref_fasta = read_and_rename_global_file(target, gatk.ids.ref_fasta, '.fasta')
    tumor_bam = read_and_rename_global_file(target, gatk.ids.tumor_bam, '.bam')
    tumor_bai = read_and_rename_global_file(target, gatk.ids.tumor_bai, '.bai', tumor_bam)
    ref_dict = read_and_rename_global_file(target, gatk.ids.ref_dict, '.dict', ref_fasta)
    ref_fai = read_and_rename_global_file(target, gatk.ids.ref_fai, '.fasta.fai', ref_fasta)

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
    target.updateGlobalFile(gatk.ids.tumor_intervals, output)

    # Spawn Child
    target.addChildTargetFn(tumor_ir, (gatk,))


def normal_ir(target, gatk):
    """
    Creates realigned normal bams
    """
    # Retrieve paths from FileStoreID
    gatk_jar = read_and_rename_global_file(target, gatk.ids.gatk_jar, '.jar')
    phase_vcf = read_and_rename_global_file(target, gatk.ids.phase_vcf, '.vcf')
    mills_vcf = read_and_rename_global_file(target, gatk.ids.mills_vcf, '.vcf')
    ref_fasta = read_and_rename_global_file(target, gatk.ids.ref_fasta, '.fasta')
    ref_fai = read_and_rename_global_file(target, gatk.ids.ref_fai, '.fasta.fai', ref_fasta)
    ref_dict = read_and_rename_global_file(target, gatk.ids.ref_dict, '.dict', ref_fasta)
    normal_bam = read_and_rename_global_file(target, gatk.ids.normal_bam, '.bam')
    normal_bai = read_and_rename_global_file(target, gatk.ids.normal_bai, '.bai', normal_bam)
    normal_intervals = read_and_rename_global_file(target, gatk.ids.normal_intervals, '.intervals')

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
    target.updateGlobalFile(gatk.ids.normal_indel_bam, output)
    target.updateGlobalFile(gatk.ids.normal_indel_bai, os.path.splitext(output)[0] + '.bai')

    # Spawn Child
    target.addChildTargetFn(normal_cleanup_bam, (gatk,))


def tumor_ir(target, gatk):
    """
    Creates realigned tumor bams
    """
    # Retrieve paths from FileStoreID
    gatk_jar = read_and_rename_global_file(target, gatk.ids.gatk_jar, '.jar')
    phase_vcf = read_and_rename_global_file(target, gatk.ids.phase_vcf, '.vcf')
    mills_vcf = read_and_rename_global_file(target, gatk.ids.mills_vcf, '.vcf')
    ref_fasta = read_and_rename_global_file(target, gatk.ids.ref_fasta, '.fasta')
    ref_fai = read_and_rename_global_file(target, gatk.ids.ref_fai, '.fasta.fai', ref_fasta)
    ref_dict = read_and_rename_global_file(target, gatk.ids.ref_dict, '.dict', ref_fasta)
    tumor_bam = read_and_rename_global_file(target, gatk.ids.tumor_bam, '.bam')
    tumor_bai = read_and_rename_global_file(target, gatk.ids.tumor_bai, '.bai', tumor_bam)
    tumor_intervals = read_and_rename_global_file(target, gatk.ids.tumor_intervals, '.intervals')

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
    target.updateGlobalFile(gatk.ids.tumor_indel_bam, output)
    target.updateGlobalFile(gatk.ids.tumor_indel_bai, os.path.splitext(output)[0] + '.bai')

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
    target.updateGlobalFile(gatk.ids.dbsnp_vcf, dbsnp_path)

    # Retrieve paths via FileStoreID
    gatk_jar = read_and_rename_global_file(target, gatk.ids.gatk_jar, '.jar')
    ref_fasta = read_and_rename_global_file(target, gatk.ids.ref_fasta, '.fasta')
    ref_fai = read_and_rename_global_file(target, gatk.ids.ref_fai, '.fasta.fai', ref_fasta)
    ref_dict = read_and_rename_global_file(target, gatk.ids.ref_dict, '.dict', ref_fasta)
    normal_indel_bam = read_and_rename_global_file(target, gatk.ids.normal_indel_bam, '.bam')
    normal_indel_bai = read_and_rename_global_file(target, gatk.ids.normal_indel_bai, '.bai', normal_indel_bam)

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

    # Update FileStoreID for output
    target.updateGlobalFile(gatk.ids.normal_recal, output)

    # Spawn Child
    target.addChildTargetFn(normal_pr, (gatk,))


def tumor_br(target, gatk):
    """
    Creates tumor recal table
    """
    # Download files not in FileStore
    dbsnp_path = gatk.unavoidable_download_method('dbsnp.vcf')

    # Assign FileStoreID
    target.updateGlobalFile(gatk.ids.dbsnp_vcf, dbsnp_path)

    # Retrieve paths via FileStoreID
    gatk_jar = read_and_rename_global_file(target, gatk.ids.gatk_jar, '.jar')
    ref_fasta = read_and_rename_global_file(target, gatk.ids.ref_fasta, '.fasta')
    ref_fai = read_and_rename_global_file(target, gatk.ids.ref_fai, '.fasta.fai', ref_fasta)
    ref_dict = read_and_rename_global_file(target, gatk.ids.ref_dict, '.dict', ref_fasta)
    tumor_indel_bam = read_and_rename_global_file(target, gatk.ids.tumor_indel_bam, '.bam')
    tumor_indel_bai = read_and_rename_global_file(target, gatk.ids.tumor_indel_bai, '.bai', tumor_indel_bam)

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

    # Update FileStoreID for output
    target.updateGlobalFile(gatk.ids.tumor_recal, output)

    # Spawn Child
    target.addChildTargetFn(tumor_pr, (gatk,))


def normal_pr(target, gatk):
    """
    Create normal.bqsr.bam
    """
    gatk_jar = read_and_rename_global_file(target, gatk.ids.gatk_jar, '.jar')
    ref_fasta = read_and_rename_global_file(target, gatk.ids.ref_fasta, '.fasta')
    ref_fai = read_and_rename_global_file(target, gatk.ids.ref_fai, '.fasta.fai', ref_fasta)
    ref_dict = read_and_rename_global_file(target, gatk.ids.ref_dict, '.dict', ref_fasta)
    normal_indel_bam = read_and_rename_global_file(target, gatk.ids.normal_indel_bam, '.bam')
    normal_indel_bai = read_and_rename_global_file(target, gatk.ids.normal_indel_bai, '.bai', normal_indel_bam)
    normal_recal = read_and_rename_global_file(target, gatk.ids.normal_recal, '.table')

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
    target.updateGlobalFile(gatk.ids.normal_bqsr_bam, output)
    target.updateGlobalFile(gatk.ids.normal_bqsr_bai, os.path.splitext(output)[0] + '.bai')

    target.addChildTargetFn(normal_indel_cleaup, (gatk,))


def tumor_pr(target, gatk):
    """
    Create tumor.bqsr.bam
    """
    # Retrieve paths via FileStoreID
    gatk_jar = read_and_rename_global_file(target, gatk.ids.gatk_jar, '.jar')
    ref_fasta = read_and_rename_global_file(target, gatk.ids.ref_fasta, '.fasta')
    ref_fai = read_and_rename_global_file(target, gatk.ids.ref_fai, '.fasta.fai', ref_fasta)
    ref_dict = read_and_rename_global_file(target, gatk.ids.ref_dict, '.dict', ref_fasta)
    tumor_indel_bam = read_and_rename_global_file(target, gatk.ids.tumor_indel_bam, '.bam')
    tumor_indel_bai = read_and_rename_global_file(target, gatk.ids.tumor_indel_bai, '.bai', tumor_indel_bam)
    tumor_recal = read_and_rename_global_file(target, gatk.ids.tumor_recal, '.table')

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
    target.updateGlobalFile(gatk.ids.tumor_bqsr_bam, output)
    target.updateGlobalFile(gatk.ids.tumor_bqsr_bai, os.path.splitext(output)[0] + '.bai')

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
    mutect_path = gatk.unavoidable_download_method('mutect.jar')

    # Add to FileStore
    target.updateGlobalFile(gatk.ids.cosmic_vcf, cosmic_path)
    target.updateGlobalFile(gatk.ids.mutect_jar, mutect_path)

    # Retrieve paths from FileStore
    normal_bqsr_bam = read_and_rename_global_file(target, gatk.ids.normal_bqsr_bam, '.bam')
    normal_bqsr_bai = read_and_rename_global_file(target, gatk.ids.normal_bqsr_bai, '.bai', normal_bqsr_bam)
    tumor_bqsr_bam = read_and_rename_global_file(target, gatk.ids.tumor_bqsr_bam, '.bam')
    tumor_bqsr_bai = read_and_rename_global_file(target, gatk.ids.tumor_bqsr_bai, '.bai', tumor_bqsr_bam)
    dbsnp_vcf = read_and_rename_global_file(target, gatk.ids.dbsnp_vcf, '.vcf')
    ref_fasta = read_and_rename_global_file(target, gatk.ids.ref_fasta, '.fasta')
    ref_fai = read_and_rename_global_file(target, gatk.ids.ref_fai, '.fasta.fai', ref_fasta)
    ref_dict = read_and_rename_global_file(target, gatk.ids.ref_dict, '.dict', ref_fasta)

    # Output files
    normal_uuid = gatk.input_urls['normal.bam'].split('/')[-1].split('.')[0]
    tumor_uuid = gatk.input_urls['tumor.bam'].split('/')[-1].split('.')[0]

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
    target.updateGlobalFile(gatk.ids.mutect_vcf, output)
    target.updateGlobalFile(gatk.ids.mutect_out, mut_out)
    target.updateGlobalFile(gatk.ids.mutect_cov, mut_cov)

    # Spawn Child
    if gatk.cleanup:
        target.addChildTargetFn(teardown, (gatk,))


def teardown(target, gatk):
    # Remove files from local working directory
    files = [os.path.join(gatk.work_dir, f) for f in os.listdir(gatk.work_dir)
             if 'tumor.vcf' not in f and os.path.isfile(f)]
    for f in files:
        os.remove(f)


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

    # Symbolic names for all inputs in the GATK pipeline
    symbolic_inputs = ['ref_fasta', 'ref_fai', 'ref_dict', 'normal_bam', 'normal_bai', 'tumor_bam', 'tumor_bai',
                       'gatk_jar', 'mills_vcf', 'phase_vcf', 'normal_intervals', 'tumor_intervals', 'dbsnp_vcf',
                       'normal_indel_bam', 'normal_indel_bai', 'tumor_indel_bam', 'tumor_indel_bai', 'normal_recal',
                       'normal_bqsr_bam', 'normal_bqsr_bai', 'tumor_bqsr_bam', 'tumor_bqsr_bai','tumor_recal',
                       'cosmic_vcf', 'mutect_jar', 'mutect_vcf', 'mutect_out', 'mutect_cov']

    # Create JobTree Stack which launches the jobs starting at the "Start Node"
    i = Stack(Target.makeTargetFn(start_node, (args, input_urls, symbolic_inputs))).startJobTree(args)


if __name__ == "__main__":
    #from jobtree_gatk_pipeline import *
    main()
