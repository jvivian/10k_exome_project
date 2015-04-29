#!/bin/bash
# John Vivian
# 3-12-15

#

DATA="/home/ubuntu/data"
TOOLS="/home/ubuntu/tools"
OUT="/home/ubuntu/brute_VCFs"
NORMAL="testexome.pair0.normal.bam"
TUMOUR="testexome.pair0.tumour.bam"

# New Tests --

java -Xmx4g -jar $TOOLS/mutect-1.1.7.jar \
--analysis_type MuTect \
--reference_sequence $DATA/Homo_sapiens_assembly19.fasta \
--tumor_lod 10 \
--input_file:normal $DATA/normal.bqsr.bam \
--input_file:tumor $DATA/tumour.bqsr.bam \
--out $DATA/MuTect.out \
--coverage_file $DATA/MuTect.coverage \
--vcf $OUT/pair8.lod10.vcf \
& \
java -Xmx4g -jar $TOOLS/mutect-1.1.7.jar \
--analysis_type MuTect \
--reference_sequence $DATA/Homo_sapiens_assembly19.fasta \
--tumor_lod 10 \
--cosmic  $DATA/b37_cosmic_v54_120711.vcf \
--input_file:normal $DATA/normal.bqsr.bam \
--input_file:tumor $DATA/tumour.bqsr.bam \
--out $DATA/MuTect.out \
--coverage_file $DATA/MuTect.coverage \
--vcf $OUT/pair8.lod10.cosmic.vcf \
& \
java -Xmx4g -jar $TOOLS/mutect-1.1.7.jar \
--analysis_type MuTect \
--reference_sequence $DATA/Homo_sapiens_assembly19.fasta \
--tumor_lod 10 \
--dbsnp $DATA/dbsnp_132_b37.leftAligned.vcf \
--input_file:normal $DATA/normal.bqsr.bam \
--input_file:tumor $DATA/tumour.bqsr.bam \
--out $DATA/MuTect.out \
--coverage_file $DATA/MuTect.coverage \
--vcf $OUT/pair8.lod10.dbsnp_b37.vcf \
& \
java -Xmx4g -jar $TOOLS/mutect-1.1.7.jar \
--analysis_type MuTect \
--reference_sequence $DATA/Homo_sapiens_assembly19.fasta \
--tumor_lod 10 \
--dbsnp $DATA/dbsnp_138.hg19.fixed.vcf \
--input_file:normal $DATA/normal.bqsr.bam \
--input_file:tumor $DATA/tumour.bqsr.bam \
--out $DATA/MuTect.out \
--coverage_file $DATA/MuTect.coverage \
--vcf $OUT/pair8.lod10.dbsnp_hg19.vcf \
& wait

#--intervals $DATA/whole_exome_agilent_1.1_refseq_plus_3_boosters.targetIntervals.bed \