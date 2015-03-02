#!/bin/bash
# John Vivian
# 3-2-15

# This script will prepare an Amazon AMI with all of the tools and data necessary to run the pipeline.
# Note: Remove as many possible "SUDO"s

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
sudo apt-get install -y samtools
sudo apt-get install -y picard-tools
sudo apt-get install -y wget
sudo apt-get install -y install openjdk-7-jre
sudo apt-get install -y git
sudo apt-get install -y python-pip
sudo pip install -y PyVCF


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

sudo git clone https://github.com/ucscCancer/pcawg_tools
sudo mv pcawg_tools/data/download.sh /home/ubuntu/data
sudo rm -rf pcawg_tools # =)
cd data/
sudo chmod u+x download.sh
sudo ./download.sh
gunzip genome.fa.gz
sudo rm -rf genome.fa.gz
cd /home/ubuntu




