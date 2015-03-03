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
wget https://s3-us-west-2.amazonaws.com/bd2k-artifacts/GenomeAnalysisTK.jar
# Picard Tools - CreateDictionarySequence
wget https://s3-us-west-2.amazonaws.com/bd2k-artifacts/CreateSequenceDictionary.jar
# Contest ArrayFree
wget https://s3-us-west-2.amazonaws.com/bd2k-artifacts/Queue-1.4-437-g6b8a9e1-svn-35362.jar
wget https://s3-us-west-2.amazonaws.com/bd2k-artifacts/ContaminationPipeline.scala
# MuTect
wget https://s3-us-west-2.amazonaws.com/bd2k-artifacts/muTect-1.1.5.jar
cd /home/ubuntu


############
#   Data   #
############
echo
echo Downloading Precursor Data
echo
sleep 3

### From: https://github.com/ucscCancer/pcawg_tools/blob/master/data/download.sh
#genomic data
cd /home/ubuntu/data
wget -r ftp://ftp.sanger.ac.uk/pub/project/PanCancer/
mv ftp.sanger.ac.uk/pub/project/PanCancer/* ./

# Remove unnecessary folder
rm -rf ftp.sanger.ac.uk/

#data for ContEst
wget http://www.broadinstitute.org/~gsaksena/arrayfree_ContEst/arrayfree_ContEst/SNP6.hg19.interval_list
wget http://www.broadinstitute.org/~gsaksena/arrayfree_ContEst/arrayfree_ContEst/hg19_population_stratified_af_hapmap_3.3.fixed.vcf
wget http://www.broadinstitute.org/~gsaksena/arrayfree_ContEst/arrayfree_ContEst/gaf_20111020+broad_wex_1.1_hg19.bed

#data for MuTect
wget http://www.broadinstitute.org/cancer/cga/sites/default/files/data/tools/mutect/b37_cosmic_v54_120711.vcf
wget http://www.broadinstitute.org/cancer/cga/sites/default/files/data/tools/mutect/dbsnp_132_b37.leftAligned.vcf.gz
gunzip dbsnp_132_b37.leftAligned.vcf.gz

wget ftp://gsapubftp-anonymous@ftp.broadinstitute.org/bundle/2.8/hg19/Mills_and_1000G_gold_standard.indels.hg19.sites.vcf.gz
wget ftp://gsapubftp-anonymous@ftp.broadinstitute.org/bundle/2.8/hg19/1000G_phase1.indels.hg19.sites.vcf.gz

# Fix chromosome naming convention
zcat Mills_and_1000G_gold_standard.indels.hg19.sites.vcf.gz \
| perl -pe 's/^chr//' > Mills_and_1000G_gold_standard.indels.hg19.sites.fixed.vcf

zcat 1000G_phase1.indels.hg19.sites.vcf.gz \
| perl -pe 's/^chr//' > 1000G_phase1.indels.hg19.sites.fixed.vcf

### End From: https://github.com/ucscCancer/pcawg_tools/blob/master/data/download.sh


# Cleanup
rm genome.fa.gz.64.sa
rm genome.fa.gz.64.pac
rm genome.fa.gz.64.bwt
rm genome.fa.gz.64.ann
rm genome.fa.gz.64.amb
rm 1000G_phase1.indels.hg19.sites.vcf.gz
rm Mills_and_1000G_gold_standard.indels.hg19.sites.vcf.gz
rm genome.fa.gz.fai
cd /home/ubuntu


#################################
#   Prepare Reference Genome    #
#################################
echo
echo Preparing Reference Genome
echo
gunzip /home/ubuntu/data/genome.fa.gz
cd /home/ubuntu/tools
samtools faidx $DATA/genome.fa
java -jar CreateSequenceDictionary.jar R=$DATA/genome.fa O=$DATA/genome.dict



