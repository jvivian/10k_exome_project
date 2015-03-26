#!/bin/bash
set -ex
# John Vivian
# 3-2-15

# This script will prepare an Amazon AMI with all of the tools and data necessary to run the pipeline.

# Schema:  Tools will be run from command line or placed in /home/ubuntu/tools.
# Schema:  Input data will be in in /home/ubuntu/data
# Schema:  It is assumed that all scripts written for this AMI will be run from /home/ubuntu/tools

#############
#   Tools   #
#############
echo
echo Downloading Tools via Apt-get
echo
sleep 3

sudo apt-get update -y
sudo apt-get install -y samtools wget openjdk-7-jre git python-pip
sudo pip install PyVCF


# Make data and tool dirs
mkdir /home/ubuntu/data
mkdir /home/ubuntu/tools

echo
echo Obtaining .jars and tools from S3
echo
sleep 3

# GenomeAnalysisTK.jar
cd /home/ubuntu/tools
wget https://s3-us-west-2.amazonaws.com/bd2k-artifacts/10k-exomes/GenomeAnalysisTK.jar
# Picard Tools - CreateDictionarySequence
wget https://s3-us-west-2.amazonaws.com/bd2k-artifacts/10k-exomes/CreateSequenceDictionary.jar
# Contest ArrayFree
wget https://s3-us-west-2.amazonaws.com/bd2k-artifacts/10k-exomes/Queue-1.4-437-g6b8a9e1-svn-35362.jar
wget https://s3-us-west-2.amazonaws.com/bd2k-artifacts/10k-exomes/ContaminationPipeline.scala
# MuTect
wget https://s3-us-west-2.amazonaws.com/bd2k-artifacts/10k-exomes/mutect-1.1.7.jar


############
#   Data   #
############
echo
echo Downloading Precursor Data
echo
sleep 3

cd /home/ubuntu/data
# Phase1 VCF
wget https://s3-us-west-2.amazonaws.com/bd2k-artifacts/10k-exomes/1000G_phase1.indels.hg19.sites.fixed.vcf
# Gold VCF
wget https://s3-us-west-2.amazonaws.com/bd2k-artifacts/10k-exomes/Mills_and_1000G_gold_standard.indels.hg19.sites.fixed.vcf
# SNP Interval_List
wget https://s3-us-west-2.amazonaws.com/bd2k-artifacts/10k-exomes/SNP6.hg19.interval_list
# Cosmic VCF
wget https://s3-us-west-2.amazonaws.com/bd2k-artifacts/10k-exomes/b37_cosmic_v54_120711.vcf
# DBSNP VCF
wget https://s3-us-west-2.amazonaws.com/bd2k-artifacts/10k-exomes/dbsnp_132_b37.leftAligned.vcf
# PopHap VCF
wget https://s3-us-west-2.amazonaws.com/bd2k-artifacts/10k-exomes/hg19_population_stratified_af_hapmap_3.3.fixed.vcf
# BED file
wget https://s3-us-west-2.amazonaws.com/bd2k-artifacts/10k-exomes/gaf_20111020%2Bbroad_wex_1.1_hg19.bed
# Genome.dict
wget https://s3-us-west-2.amazonaws.com/bd2k-artifacts/10k-exomes/Homo_sapiens_assembly19.dict
# Genome.fa.fai
wget https://s3-us-west-2.amazonaws.com/bd2k-artifacts/10k-exomes/Homo_sapiens_assembly19.fasta.fai
# Genome.fa
wget https://s3-us-west-2.amazonaws.com/bd2k-artifacts/10k-exomes/Homo_sapiens_assembly19.fasta
# DBSNP HG19
wget https://s3-us-west-2.amazonaws.com/bd2k-artifacts/10k-exomes/dbsnp_138.hg19.fixed.vcf



echo All Tools and Data have been acquired





