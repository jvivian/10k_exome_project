#!/bin/bash
# John Vivian
# 3-3-15

# Script will be run from /home/ubuntu/tool

NCT=4 # This should change based on # of cores in the instance
DATA="/home/ubuntu/data" # Change if necessary

# Parse input into array
IFS='.' read -a array <<< $INPUT

# MuTect
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
--fraction_contamination 1.8 \
--out $DATA/MuTect.out \
--coverage_file $DATA/MuTect.coverage \
--vcf $DATA/MuTect.vcf
