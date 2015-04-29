#!/bin/bash
# John Vivian
# 3-3-15

# Script will be run from /home/ubuntu/tool

MEM=15 # This should change based on available memory in the instance
NCT=4 # This should change based on # of cores in the instance
DATA="/home/ubuntu/data" # Change if necessary

#input BAM
INPUT=$1

# Parse input into array
IFS='.' read -a array <<< $INPUT

# Base Recalibration
echo "

BaseRecalibration

"

java -jar GenomeAnalysisTK.jar \
-T BaseRecalibrator \
-nct ${NCT} \
-R $DATA/genome.fa \
-I $DATA/${array[2]}.indel.bam \
-knownSites $DATA/dbsnp_132_b37.leftAligned.vcf \
-o $DATA/${array[2]}.recal_data.table
