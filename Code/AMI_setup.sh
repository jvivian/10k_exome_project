#!/bin/bash

# This script will prepare an Amazon AMI with all of the tools and data necessary to run the pipeline.
# Note: Remove as many possible "SUDO"s

# Schema:  Tools will be run from command line or placed in /home/ubuntu.
# Schema:  Input data will be in in /home/ubuntu/data
# Schema:  It is assumed that all scripts written for this AMI will be run from /home/ubuntu

#############
#   Tools   #
#############


FILE="/home/profile/.profile" # Check?

sudo apt-get update -y
sudo apt-get install -y samtools
sudo apt-get install -y picard-tools
sudo apt-get install -y wget
sudo apt-get install -y install openjdk-7-jre
sudo apt-get install -y git
sudo apt-get install -y python-pip
sudo pip install -y PyVCF

# Contest_arrayfree
wget http://www.broadinstitute.org/~gsaksena/arrayfree_ContEst/arrayfree_ContEst/Queue-1.4-437-g6b8a9e1-svn-35362.jar
wget http://www.broadinstitute.org/~gsaksena/arrayfree_ContEst/arrayfree_ContEst/ContaminationPipeline.scala

# MuTect
wget https://github.com/broadinstitute/mutect/releases/download/1.1.5/muTect-1.1.5-bin.zip
unzip muTect-1.1.5-bin.zip

# Maven/Gatk_from_git is unnecessary if we just host the GATK.jar somewhere.
# Maven ???
sudo wget http://apache.mesi.com.ar/maven/maven-3/3.2.5/binaries/apache-maven-3.2.5-bin.tar.gz
tar zxvf apache-maven-3.2.5-bin.tar.gz
sudo mv apache-maven-3.2.5 /usr/local/bin
sudo rm -f apache-maven-3.2.5-bin.tar.gz
# Add envs & PATH
echo >> $FILE
echo # Maven Attributes
echo export M2_HOME="/usr/local/bin/apache-maven-3.2.5" >> $FILE
echo export M2=$M2_HOME/bin >> $FILE
echo export PATH=$PATH:$M2 >> $FILE
source $FILE

# GATK-JAR (we can just host this?)
sudo git clone https://github.com/broadgsa/gatk-protected/
cd gatk-protected/
sudo mvn package
sudo cp target/GenomeAnalysisTK.jar /home/ubuntu/
cd /home/ubuntu


############
#   Data   #
############

sudo git clone https://github.com/ucscCancer/pcawg_tools
sudo mv pcawg_tools/data /home/ubuntu
sudo rm -f pcawg_tools
sudo ./data/download.sh
gunzip genome.fa.gz
sudo rm -f genome.fa.gz




