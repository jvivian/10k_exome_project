#!/bin/bash
# John Vivian
# 3-3-15

# Script will be run from /home/ubuntu/tool

MEM=15 # This should change based on memory of instance
DATA="/home/ubuntu/data" # Change if necessary

#input BAM
INPUT=$1

# Create .bai file for input.bam
samtools index ${INPUT}
