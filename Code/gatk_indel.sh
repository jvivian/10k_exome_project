#!/bin/bash

MEM="3" # This should change based on memory of instance
DATA="/home/ubuntu/data" # Change if necessary

#input BAM
INPUT=$1

# Create .fai file for genome.fa
samtools faidx $DATA/genome.fa
# Create .dict file for genome.fa
picard-tools CreateSequenceDictionary R=$DATA/genome.fa O=$DATA/genome.dict
# Create .bai file for input.bam
samtools index $DATA/${INPUT}

# Run RealignerTargetCreator
# nt = # of threads -- talk to Hannes about parallelism
java -Xmx4g -jar GenomeAnalysisTK.jar \
-T RealignerTargetCreator \
-nt 1 \
-R genome.fa \
-I testexome.pair0.tumour.bam \
-known 1000G_phase1.indels.hg19.sites.fixed.vcf \
-known Mills_and_1000G_gold_standard.indels.hg19.sites.fixed.vcf \
--downsampling_type NONE -o output.intervals

# Run IndelRealigner
java -Xmx4g  -jar ../tools/gatk_bqsr/GenomeAnalysisTK.jar -T IndelRealigner -R genome.fasta -I testexome.pair0.tumour.bam -L GL000207.1:1-4262 -targetIntervals output.intervals --downsampling_type NONE -known 1000G_phase1.indels.hg19.sites.fixed.vcf -known Mills_and_1000G_gold_standard.indels.hg19.sites.fixed.vcf -maxReads 720000 -maxInMemory 5400000 -o test.gatk_indel.bam


