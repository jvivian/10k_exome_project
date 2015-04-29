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

# Run RealignerTargetCreator
# nt = # of threads -- talk to Hannes about parallelism
echo "

Realigner Target Creator

"
java -Xmx${MEM}g -jar GenomeAnalysisTK.jar \
-T RealignerTargetCreator \
-nt 20 \
-R $DATA/genome.fa \
-I $DATA/${INPUT} \
-known $DATA/1000G_phase1.indels.hg19.sites.fixed.vcf \
-known $DATA/Mills_and_1000G_gold_standard.indels.hg19.sites.fixed.vcf \
--downsampling_type NONE -o $DATA/output.${array[2]}.intervals

# ${array[2]} will have to be changed once final files have been given
