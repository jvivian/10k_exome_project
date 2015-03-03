#!/bin/bash
# John Vivian
# 3-3-15

# Script will be run from /home/ubuntu/tool

MEM=15 # This should change based on memory of instance
DATA="/home/ubuntu/data" # Change if necessary

#input BAM
INPUT=$1

# Parse input into array
IFS='.' read -a array <<< $INPUT

# Indeal Realignment
echo "

Indel Realigner for Normal.bam

"
java -Xmx${MEM}g -jar GenomeAnalysisTK.jar \
-T IndelRealigner \
-R $DATA/genome.fa \
-I $DATA/${INPUT}  \
-targetIntervals $DATA/output.${array[2]}.intervals \
--downsampling_type NONE \
-known $DATA/1000G_phase1.indels.hg19.sites.fixed.vcf \
-known $DATA/Mills_and_1000G_gold_standard.indels.hg19.sites.fixed.vcf \
-maxReads 720000 -maxInMemory 5400000 \
-o $DATA/${array[2]}.indel.bam

# ${array[2]} will have to be changed once final files have been given