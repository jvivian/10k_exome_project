#!/bin/bash
set -ex
# John Vivian
# 3-2-15

DATA="/home/ubuntu/data"
NORMAL="testexome.pair8.normal.bam"
TUMOUR="testexome.pair8.tumour.bam"

# Copy and paste help:   ${NORMAL}  ${TUMOUR}  ${DATA}   ${DATA}/${NORMAL}  ${DATA}/${TUMOUR}

# Obtain BAMS
cd /home/ubuntu/data
echo Obtaining Tumour/Normal BAMs >> /home/ubuntu/time.txt
{ time wget https://s3-us-west-2.amazonaws.com/bd2k-test-data/$NORMAL \
& wget https://s3-us-west-2.amazonaws.com/bd2k-test-data/$TUMOUR \
& wait; } 2> /home/ubuntu/time.txt
cd /home/ubuntu/tools


# Create Index Files from Input Data ====================================================
echo "

INDEXING BAMS

"
echo Indexing BAMs >> /home/ubuntu/time.txt
{ time samtools index $DATA/$NORMAL \
& samtools index $DATA/$TUMOUR \
& wait; } 2>> /home/ubuntu/time.txt


# RealignerTargetCreator ================================================================
echo "

REALIGNER TARGET CREATOR

"
# NORMAL
echo RTC-Normal >> /home/ubuntu/time.txt
{ time java -Xmx15g -jar GenomeAnalysisTK.jar \
-T RealignerTargetCreator \
-nt 4 \
-R ${DATA}/Homo_sapiens_assembly19.fasta \
-I ${DATA}/${NORMAL} \
-known ${DATA}/1000G_phase1.indels.hg19.sites.fixed.vcf \
-known ${DATA}/Mills_and_1000G_gold_standard.indels.hg19.sites.fixed.vcf \
--downsampling_type NONE \
-o ${DATA}/output.normal.intervals; } 2>> /home/ubuntu/time.txt

# TUMOUR
echo RTC-Tumour >> /home/ubuntu/time.txt
{ time java -Xmx15g -jar GenomeAnalysisTK.jar \
-T RealignerTargetCreator \
-nt 4 \
-R ${DATA}/Homo_sapiens_assembly19.fasta \
-I ${DATA}/${TUMOUR} \
-known ${DATA}/1000G_phase1.indels.hg19.sites.fixed.vcf \
-known ${DATA}/Mills_and_1000G_gold_standard.indels.hg19.sites.fixed.vcf \
--downsampling_type NONE \
-o ${DATA}/output.tumour.intervals ; } 2>> /home/ubuntu/time.txt


# IndelRealigner =======================================================================
echo "

INDEL REALIGNER

"
# NORMAL
echo IR-parallel >> /home/ubuntu/time.txt
{time java -Xmx15g -jar GenomeAnalysisTK.jar \
-T IndelRealigner \
-R $DATA/Homo_sapiens_assembly19.fasta \
-I $DATA/$NORMAL  \
-targetIntervals $DATA/output.normal.intervals \
--downsampling_type NONE \
-known $DATA/1000G_phase1.indels.hg19.sites.fixed.vcf \
-known $DATA/Mills_and_1000G_gold_standard.indels.hg19.sites.fixed.vcf \
-maxReads 720000 -maxInMemory 5400000 \
-o $DATA/normal.indel.bam \
& java -Xmx15g -jar GenomeAnalysisTK.jar \
-T IndelRealigner \
-R $DATA/Homo_sapiens_assembly19.fasta \
-I $DATA/$TUMOUR  \
-targetIntervals $DATA/output.tumour.intervals \
--downsampling_type NONE \
-known $DATA/1000G_phase1.indels.hg19.sites.fixed.vcf \
-known $DATA/Mills_and_1000G_gold_standard.indels.hg19.sites.fixed.vcf \
-maxReads 720000 -maxInMemory 5400000 \
-o $DATA/tumour.indel.bam \
& wait ; } 2>> /home/ubuntu/time.txt

# File Cleanup to keep size down
rm $DATA/$TUMOUR
rm $DATA/$NORMAL
rm $DATA/*.intervals


# Base Recalibrator =====================================================================
echo "

Base Recalibrator

"
echo BR-Normal >> /home/ubuntu/time.txt
# NORMAL
{ time java -Xmx15g -jar GenomeAnalysisTK.jar \
-T BaseRecalibrator \
-nct 4 \
-R $DATA/Homo_sapiens_assembly19.fasta \
-I $DATA/normal.indel.bam \
-knownSites $DATA/dbsnp_132_b37.leftAligned.vcf \
-o $DATA/normal.recal_data.table ; } 2>> /home/ubuntu/time.txt

echo BR-Tumour >> /home/ubuntu/time.txt
# TUMOUR
{ time java -Xmx15g -jar GenomeAnalysisTK.jar \
-T BaseRecalibrator \
-nct 4 \
-R $DATA/Homo_sapiens_assembly19.fasta \
-I $DATA/tumour.indel.bam \
-knownSites $DATA/dbsnp_132_b37.leftAligned.vcf \
-o $DATA/tumour.recal_data.table ; } 2>> /home/ubuntu/time.txt


# PrintReads ==========================================================================
echo "

Print Reads

"
echo PR-Normal >> /home/ubuntu/time.txt
# NORMAL
{ time java -Xmx15g -jar GenomeAnalysisTK.jar \
-T PrintReads \
-nct 4  \
-R $DATA/Homo_sapiens_assembly19.fasta \
--emit_original_quals  \
-I $DATA/normal.indel.bam \
-BQSR $DATA/normal.recal_data.table \
-o $DATA/normal.bqsr.bam ; } 2>> /home/ubuntu/time.txt

echo PR-Tumour >> /home/ubuntu/time.txt
# TUMOUR
{ time java -Xmx15g -jar GenomeAnalysisTK.jar \
-T PrintReads \
-nct 4  \
-R $DATA/Homo_sapiens_assembly19.fasta \
--emit_original_quals  \
-I $DATA/tumour.indel.bam \
-BQSR $DATA/tumour.recal_data.table \
-o $DATA/tumour.bqsr.bam ; } 2>> /home/ubuntu/time.txt

# File Cleanup to keep size down
rm $DATA/normal.indel.bam
rm $DATA/normal.indel.bai
rm $DATA/tumour.indel.bam
rm $DATA/tumour.indel.bai


# Contest ArrayFree ====================================================================
echo "

Contest_ArrayFree

"
echo CAF >> /home/ubuntu/time.txt
{ time java -Djava.io.tmpdir=~/tmp -Xmx2g \
-jar Queue-1.4-437-g6b8a9e1-svn-35362.jar \
-S ContaminationPipeline.scala \
--reference $DATA/Homo_sapiens_assembly19.fasta \
--output $DATA/contest \
--bamfile $DATA/tumour.bqsr.bam \
-nbam $DATA/normal.bqsr.bam \
--popfile $DATA/hg19_population_stratified_af_hapmap_3.3.fixed.vcf \
--arrayinterval $DATA/SNP6.hg19.interval_list \
--interval $DATA/gaf_20111020+broad_wex_1.1_hg19.bed -run -memory 2 ; } 2>> /home/ubuntu/time.txt


echo STORING CONTAM VALUE
CONTAM=$(cat $DATA/contest.firehose)

# remove the large number of contest files
cd $DATA
mv contest.firehose backup.contam
find . -type f -name .contest\* -exec rm {} \;
find . -type f -name contest\* -exec rm {} \;
cd /home/ubuntu/tools


# MuTect ===============================================================================
echo "

MuTect

"
echo mutect >> /home/ubuntu/time.txt
{ time java -Xmx15g -jar mutect-1.1.7.jar \
--analysis_type MuTect \
--reference_sequence $DATA/Homo_sapiens_assembly19.fasta \
--cosmic  $DATA/b37_cosmic_v54_120711.vcf \
--dbsnp $DATA/dbsnp_132_b37.leftAligned.vcf \
--input_file:normal $DATA/normal.bqsr.bam \
--input_file:tumor $DATA/tumour.bqsr.bam \
--out $DATA/MuTect.out \
--coverage_file $DATA/MuTect.coverage \
--vcf $DATA/MuTect.pair8.vcf ; } 2>> /home/ubuntu/time.txt


