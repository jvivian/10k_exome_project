#!/bin/bash
# John Vivian
# 3-3-15

# Script will be run from /home/ubuntu/tool

NCT=4 # This should change based on # of cores in the instance
DATA="/home/ubuntu/data" # Change if necessary

# Parse input into array
IFS='.' read -a array <<< $INPUT

# ContestArrayFree
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