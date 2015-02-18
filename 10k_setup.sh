#!/bin/bash

# John Vivian
# 2-13-15

##################
## Dependencies ##
##################

FILE="/home/ec2-user/.bash_profile"

# Update Package Manager
echo Updating yum
sudo yum update

# Java
echo Installing Java
sudo yum install java-1.7.0-openjdk -y

# Git
echo Installing Git
sudo yum install git -y

# Docker
sudo yum install docker -y

# Maven
wget http://apache.mesi.com.ar/maven/maven-3/3.2.5/binaries/apache-maven-3.2.5-bin.tar.gz
tar zxvf apache-maven-3.2.5-bin.tar.gz
sudo mv apache-maven-3.2.5 /usr/local/bin
# Add envs & PATH
echo >> $FILE
echo # Maven Attributes
echo export M2_HOME="/usr/local/bin/apache-maven-3.2.5" >> $FILE
echo export M2=$M2_HOME/bin >> $FILE
echo export PATH=$PATH:$M2 >> $FILE

# GeneTorrent
echo Installing GeneTorrent
wget --no-check-certificate https://cghub.ucsc.edu/software/downloads/GeneTorrent/3.8.7/GeneTorrent-download-3.8.7-207-Ubuntu14.04.x86_64.tar.gz
tar zxvf GeneTorrent-download-3.8.7-207-CentOS6.4.x86_64.tar.gz
mv cghub /usr/local/bin
# Add to PATH
echo PATH="$PATH:/usr/local/bin/cghub/bin" >> $FILE

source $FILE
#########################
## GATK Best Practices ##
#########################

# BWA
wget http://sourceforge.net/projects/bio-bwa/files/bwa-0.7.12.tar.bz2
tar zxvf bwa-0.7.12.tar.bz2
cd bwa-0.7.12
make
sudo mv bwa /usr/local/bin

# SAMTools
wget http://sourceforge.net/projects/samtools/files/samtools/1.2/samtools-1.2.tar.bz2/download
tar zxvf samtools-1.2.tar.bz2
cd samtools-1.2
make
sudo mv samtools /usr/local/bin

# Picard
# export CLASSPATH=/path/to/picard-1.33.jar:/path/to/sam-1.33.jar

# GATK (Jar)
sudo git clone https://github.com/broadgsa/gatk-protected/
cd gatk-protected/
mvn package

#################
## PCAWG Tools ##
#################

# Nebula
git clone https://github.com/kellrott/nebula.git
mv nebula /usr/local/bin
echo PYTHONPATH=/usr/local/bin/nebula >> $FILE

# Download Data
echo Downloading Normal
gtdownload -c https://cghub.ucsc.edu/software/downloads/cghub_public.key -vv -d ebdb53ae-6386-4bc4-90b1-4f249ff9fcdf

echo Downloading Tumor
gtdownload -c https://cghub.ucsc.edu/software/downloads/cghub_public.key -vv -d 2cce1d67-ad6f-4f08-af7e-2a6fbc1fb459




