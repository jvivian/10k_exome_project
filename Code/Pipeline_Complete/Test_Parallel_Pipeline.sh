#!/bin/bash
set -ex
# John Vivian
# 3-2-15

DATA="/home/ubuntu/data"
INT="/home/ubuntu/intermediates"
NORMAL="testexome.pair8.normal.bam"
TUMOUR="testexome.pair8.tumour.bam"

# Copy and paste help:   ${NORMAL}  ${TUMOUR}  ${DATA}   ${DATA}/${NORMAL}  ${DATA}/${TUMOUR}

# Obtain BAMS
cd /home/ubuntu/data
wget https://s3-us-west-2.amazonaws.com/bd2k-test-data/testexome.pair8.normal.bam
wget https://s3-us-west-2.amazonaws.com/bd2k-test-data/testexome.pair8.tumour.bam
cd /home/ubuntu/tools

# Create Index Files from Input Data ====================================================
echo "

INDEXING BAMS

"

samtools index $DATA/$NORMAL & samtools index $DATA/$TUMOUR & wait

# RealignerTargetCreator ================================================================
echo "

REALIGNER TARGET CREATOR

"

# NORMAL
java -Xmx15g -jar GenomeAnalysisTK.jar \
-T RealignerTargetCreator \
-nt 4 \
-R ${DATA}/genome.fa \
-I ${DATA}/${NORMAL} \
-known ${DATA}/1000G_phase1.indels.hg19.sites.fixed.vcf \
-known ${DATA}/Mills_and_1000G_gold_standard.indels.hg19.sites.fixed.vcf \
--downsampling_type NONE \
-o ${DATA}/output.normal.intervals

# TUMOUR
java -Xmx15g -jar GenomeAnalysisTK.jar \
-T RealignerTargetCreator \
-nt 4 \
-R ${DATA}/genome.fa \
-I ${DATA}/${TUMOUR} \
-known ${DATA}/1000G_phase1.indels.hg19.sites.fixed.vcf \
-known ${DATA}/Mills_and_1000G_gold_standard.indels.hg19.sites.fixed.vcf \
--downsampling_type NONE \
-o ${DATA}/output.tumour.intervals

# IndelRealigner =======================================================================
echo "

INDEL REALIGNER

"
# NORMAL
java -Xmx15g -jar GenomeAnalysisTK.jar \
-T IndelRealigner \
-R $DATA/genome.fa \
-I $DATA/$NORMAL  \
-targetIntervals $DATA/output.normal.intervals \
--downsampling_type NONE \
-known $DATA/1000G_phase1.indels.hg19.sites.fixed.vcf \
-known $DATA/Mills_and_1000G_gold_standard.indels.hg19.sites.fixed.vcf \
-maxReads 720000 -maxInMemory 5400000 \
-o $DATA/normal.indel.bam & \
java -Xmx15g -jar GenomeAnalysisTK.jar \
-T IndelRealigner \
-R $DATA/genome.fa \
-I $DATA/$TUMOUR  \
-targetIntervals $DATA/output.tumour.intervals \
--downsampling_type NONE \
-known $DATA/1000G_phase1.indels.hg19.sites.fixed.vcf \
-known $DATA/Mills_and_1000G_gold_standard.indels.hg19.sites.fixed.vcf \
-maxReads 720000 -maxInMemory 5400000 \
-o $DATA/tumour.indel.bam & \
wait

# File Cleanup to keep size down
rm $DATA/$TUMOUR
rm $DATA/$NORMAL


# Base Recalibrator =====================================================================
echo "

Base Recalibrator

"
# NORMAL
java -jar GenomeAnalysisTK.jar \
-T BaseRecalibrator \
-nct 4 \
-R $DATA/genome.fa \
-I $DATA/normal.indel.bam \
-knownSites $DATA/dbsnp_132_b37.leftAligned.vcf \
-o $DATA/normal.recal_data.table

# TUMOUR
java -jar GenomeAnalysisTK.jar \
-T BaseRecalibrator \
-nct 4 \
-R $DATA/genome.fa \
-I $DATA/tumour.indel.bam \
-knownSites $DATA/dbsnp_132_b37.leftAligned.vcf \
-o $DATA/tumour.recal_data.table

# PrintReads ==========================================================================
echo "

Print Reads

"
# NORMAL
java -jar GenomeAnalysisTK.jar \
-T PrintReads \
-nct 4  \
-R $DATA/genome.fa \
--emit_original_quals  \
-I $DATA/normal.indel.bam \
-BQSR $DATA/normal.recal_data.table \
-o $DATA/normal.bqsr.bam

# TUMOUR
java -jar GenomeAnalysisTK.jar \
-T PrintReads \
-nct 4  \
-R $DATA/genome.fa \
--emit_original_quals  \
-I $DATA/tumour.indel.bam \
-BQSR $DATA/tumour.recal_data.table \
-o $DATA/tumour.bqsr.bam

# File Cleanup to keep size down
rm $DATA/normal.indel.bam
rm $DATA/tumour.indel.bam

# Contest ArrayFree ====================================================================
echo "

Contest_ArrayFree

"
java -Djava.io.tmpdir=~/tmp -Xmx2g \
-jar Queue-1.4-437-g6b8a9e1-svn-35362.jar \
-S ContaminationPipeline.scala \
--reference $DATA/genome.fa \
--output $DATA/contest \
--bamfile $DATA/tumour.bqsr.bam \
-nbam $DATA/normal.bqsr.bam \
--popfile $DATA/hg19_population_stratified_af_hapmap_3.3.fixed.vcf \
--arrayinterval $DATA/SNP6.hg19.interval_list \
--interval $DATA/gaf_20111020+broad_wex_1.1_hg19.bed -run -memory 2


echo STORING CONTAM VALUE
CONTAM=$(cat $DATA/contest.firehose)

# MuTect ===============================================================================
echo "

MuTect

"
java -Xmx4g -jar muTect-1.1.5.jar \
--analysis_type MuTect \
--reference_sequence $DATA/genome.fa \
--cosmic  $DATA/b37_cosmic_v54_120711.vcf \
--dbsnp $DATA/dbsnp_132_b37.leftAligned.vcf \
--intervals $DATA/SNP6.hg19.interval_list \
--input_file:normal $DATA/normal.bqsr.bam \
--input_file:tumor $DATA/tumour.bqsr.bam \
--fraction_contamination $CONTAM \
--out $DATA/MuTect.out \
--coverage_file $DATA/MuTect.coverage \
--vcf $DATA/MuTect.pair8.vcf


