#!/bin/bash
# John Vivian
# 3-12-15

#

DATA="/home/ubuntu/new_data"
TOOLS="/home/ubuntu/new_tools"
OUT="/home/ubuntu/brute_VCFs"
NORMAL="testexome.pair0.normal.bam"
TUMOUR="testexome.pair0.tumour.bam"

set -ex

java -Xmx7g -jar $TOOLS/mutect-1.1.5.jar \
--analysis_type MuTect \
--reference_sequence $DATA/Homo_sapiens_assembly19.fasta \
--cosmic  $DATA/b37_cosmic_v54_120711.vcf \
--dbsnp $DATA/dbsnp_132_b37.leftAligned.vcf \
--intervals $DATA/SNP6.hg19.interval_list \
--input_file:normal $DATA/$NORMAL \
--input_file:tumor $DATA/$TUMOUR \
--out $DATA/MuTect.out \
--coverage_file $DATA/MuTect.coverage \
--vcf $OUT/pair0.original.115.b37.vcf \
& \
java -Xmx7g -jar $TOOLS/mutect-1.1.5.jar \
--analysis_type MuTect \
--reference_sequence $DATA/Homo_sapiens_assembly19.fasta \
--cosmic  $DATA/b37_cosmic_v54_120711.vcf \
--dbsnp $DATA/dbsnp_132_b37.leftAligned.vcf \
--intervals $DATA/SNP6.hg19.interval_list \
--input_file:normal $DATA/normal.indel.bam \
--input_file:tumor $DATA/tumour.indel.bam \
--out $DATA/MuTect.out \
--coverage_file $DATA/MuTect.coverage \
--vcf $OUT/pair0.indel.115.b37.vcf \
& \
wait


java -Xmx7g -jar $TOOLS/mutect-1.1.5.jar \
--analysis_type MuTect \
--reference_sequence $DATA/Homo_sapiens_assembly19.fasta \
--cosmic  $DATA/b37_cosmic_v54_120711.vcf \
--dbsnp $DATA/dbsnp_132_b37.leftAligned.vcf \
--intervals $DATA/SNP6.hg19.interval_list \
--input_file:normal $DATA/normal.bqsr.bam \
--input_file:tumor $DATA/tumour.bqsr.bam \
--out $DATA/MuTect.out \
--coverage_file $DATA/MuTect.coverage \
--vcf $OUT/pair0.bqsr.115.b37.vcf


# New Tests --

java -Xmx4g -jar $TOOLS/mutect-1.1.7.jar \
--analysis_type MuTect \
--intervals $DATA/output.tumour.intervals \
--reference_sequence $DATA/Homo_sapiens_assembly19.fasta \
--input_file:normal $DATA/normal.bqsr.bam \
--input_file:tumor $DATA/tumour.bqsr.bam \
--out $DATA/MuTect.out \
--coverage_file $DATA/MuTect.coverage \
--vcf $OUT/pair0.bqsr.base+intervals_tumour.vcf \
& \
java -Xmx4g -jar $TOOLS/mutect-1.1.7.jar \
--analysis_type MuTect \
--intervals $DATA/output.normal.intervals \
--reference_sequence $DATA/Homo_sapiens_assembly19.fasta \
--input_file:normal $DATA/normal.bqsr.bam \
--input_file:tumor $DATA/tumour.bqsr.bam \
--out $DATA/MuTect.out \
--coverage_file $DATA/MuTect.coverage \
--vcf $OUT/pair0.bqsr.base+intervals_normal.vcf \
& \
java -Xmx4g -jar $TOOLS/mutect-1.1.7.jar \
--analysis_type MuTect \
--dbsnp $DATA/dbsnp_138.hg19.vcf \
--reference_sequence $DATA/Homo_sapiens_assembly19.fasta \
--input_file:normal $DATA/normal.bqsr.bam \
--input_file:tumor $DATA/tumour.bqsr.bam \
--out $DATA/MuTect.out \
--coverage_file $DATA/MuTect.coverage \
--vcf $OUT/pair0.bqsr.base+dbsnp_138.vcf \
& \
java -Xmx4g -jar $TOOLS/mutect-1.1.7.jar \
--analysis_type MuTect \
--reference_sequence $DATA/Homo_sapiens_assembly19.fasta \
--input_file:normal $DATA/normal.bqsr.bam \
--input_file:tumor $DATA/tumour.bqsr.bam \
--out $DATA/MuTect.out \
--coverage_file $DATA/MuTect.coverage \
--vcf $OUT/pair0.bqsr.base+cosmic_b37.vcf \
& \
wait
