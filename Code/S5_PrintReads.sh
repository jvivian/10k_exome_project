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

# PrintReads
echo "

PrintReads

"
java -jar GenomeAnalysisTK.jar \
-T PrintReads \
-nct 4  \
-R $DATA/genome.fa \
--emit_original_quals  \
-I $DATA/${array[2]}.indel.bam \
-BQSR $DATA/${array[2]}.recal_data.table \
-o $DATA/${array[2]}.bqsr.bam