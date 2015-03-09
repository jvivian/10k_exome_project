#!/usr/bin/env python2.7
# John Vivian
# 3-9-15

'''
Hardcoding of pipeline steps for porting into 10k project
'''

DATA="/home/ubuntu/data"
MEM=15
HMEM= MEM/2
CORES=4
UUID='123456789'
NORMAL=UUID + '.N.bam'
TUMOR=UUID + '.T.bam'

s1_index_p = "samtools index {DATA}/{NORMAL} \
& samtools index {DATA}/{TUMOUR} \
& wait"

s2_RTC_n = "java -Xmx{MEM}g -jar GenomeAnalysisTK.jar \
-T RealignerTargetCreator \
-nt {CORES} \
-R {DATA}/genome.fa \
-I {DATA}/{NORMAL} \
-known {DATA}/1000G_phase1.indels.hg19.sites.fixed.vcf \
-known {DATA}/Mills_and_1000G_gold_standard.indels.hg19.sites.fixed.vcf \
--downsampling_type NONE \
-o {DATA}/{UUID}.normal.intervals"

s2_RTC_t = "java -Xmx{MEM}g -jar GenomeAnalysisTK.jar \
-T RealignerTargetCreator \
-nt {CORES} \
-R ${DATA}/genome.fa \
-I ${DATA}/${TUMOUR} \
-known ${DATA}/1000G_phase1.indels.hg19.sites.fixed.vcf \
-known ${DATA}/Mills_and_1000G_gold_standard.indels.hg19.sites.fixed.vcf \
--downsampling_type NONE \
-o ${DATA}/{UUID}.tumour.intervals"

s3_IR_p = "java -Xmx{HMEM}g -jar GenomeAnalysisTK.jar \
-T IndelRealigner \
-R {DATA}/genome.fa \
-I {DATA}/{NORMAL}  \
-targetIntervals {DATA}/{UUID}.normal.intervals \
--downsampling_type NONE \
-known {DATA}/1000G_phase1.indels.hg19.sites.fixed.vcf \
-known {DATA}/Mills_and_1000G_gold_standard.indels.hg19.sites.fixed.vcf \
-maxReads 720000 -maxInMemory 5400000 \
-o {DATA}/{UUID}.normal.indel.bam \
& java -Xmx{HMEM}g -jar GenomeAnalysisTK.jar \
-T IndelRealigner \
-R {DATA}/genome.fa \
-I {DATA}/{TUMOUR}  \
-targetIntervals {DATA}/{UUID}.output.tumour.intervals \
--downsampling_type NONE \
-known {DATA}/1000G_phase1.indels.hg19.sites.fixed.vcf \
-known {DATA}/Mills_and_1000G_gold_standard.indels.hg19.sites.fixed.vcf \
-maxReads 720000 -maxInMemory 5400000 \
-o {DATA}/{UUID}.tumour.indel.bam \
& wait"

s4_BR_n = "java -jar GenomeAnalysisTK.jar \
-T BaseRecalibrator \
-nct {CORES} \
-R {DATA}/genome.fa \
-I {DATA}/{UUID}.normal.indel.bam \
-knownSites {DATA}/dbsnp_132_b37.leftAligned.vcf \
-o {DATA}/{UUID}.normal.recal_data.table"

s4_BR_t = "java -jar GenomeAnalysisTK.jar \
-T BaseRecalibrator \
-nct {CORES} \
-R {DATA}/genome.fa \
-I {DATA}/{UUID}.tumour.indel.bam \
-knownSites {DATA}/dbsnp_132_b37.leftAligned.vcf \
-o {DATA}/{UUID}.tumour.recal_data.table"

s5_PR_n = "java -jar GenomeAnalysisTK.jar \
-T PrintReads \
-nct {CORES}  \
-R {DATA}/genome.fa \
--emit_original_quals  \
-I {DATA}/{UUID}.normal.indel.bam \
-BQSR {DATA}/{UUID}.normal.recal_data.table \
-o {DATA}/{UUID}.normal.bqsr.bam"

s5_PR_t = "java -jar GenomeAnalysisTK.jar \
-T PrintReads \
-nct {CORES} \
-R {DATA}/genome.fa \
--emit_original_quals  \
-I {DATA}/{UUID}.tumour.indel.bam \
-BQSR {DATA}/{UUID}.tumour.recal_data.table \
-o {DATA}/{UUID}.tumour.bqsr.bam"

s6_CAF = "java -Djava.io.tmpdir=~/tmp -Xmx2g \
-jar Queue-1.4-437-g6b8a9e1-svn-35362.jar \
-S ContaminationPipeline.scala \
--reference {DATA}/genome.fa \
--output {DATA}/contest \
--bamfile {DATA}/{UUID}.tumour.bqsr.bam \
-nbam {DATA}/{UUID}.normal.bqsr.bam \
--popfile {DATA}/hg19_population_stratified_af_hapmap_3.3.fixed.vcf \
--arrayinterval {DATA}/SNP6.hg19.interval_list \
--interval {DATA}/gaf_20111020+broad_wex_1.1_hg19.bed -run -memory 2"

'''
Note: Must store CONTAM value which is found in {DATA}/contest.firehose
before executing step 7
'''
# Do not use the below value as is -- it is simply a test variable.
CONTAM=.018

s7_Mu = "-Xmx{MEM}g -jar muTect-1.1.5.jar \
--analysis_type MuTect \
--reference_sequence {DATA}/genome.fa \
--cosmic  {DATA}/b37_cosmic_v54_120711.vcf \
--dbsnp {DATA}/dbsnp_132_b37.leftAligned.vcf \
--intervals {DATA}/SNP6.hg19.interval_list \
--input_file:normal {DATA}/{UUID}.normal.bqsr.bam \
--input_file:tumor {DATA}/{UUID}.tumour.bqsr.bam \
--fraction_contamination {CONTAM} \
--out {DATA}/MuTect.out \
--coverage_file {DATA}/MuTect.coverage \
--vcf {DATA}/{UUID}.vcf"



