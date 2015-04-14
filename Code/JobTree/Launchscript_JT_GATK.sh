#!/usr/bin/env bash

python JT_GATK.py \
--reference_genome "https://s3-us-west-2.amazonaws.com/bd2k-artifacts/10k-exomes/Homo_sapiens_assembly19.fasta" \
--normal "https://s3-us-west-2.amazonaws.com/bd2k-test-data/testexome.pair9.normal.bam" \
--tumor "https://s3-us-west-2.amazonaws.com/bd2k-test-data/testexome.pair9.tumor.bam" \
--phase "https://s3-us-west-2.amazonaws.com/bd2k-artifacts/10k-exomes/1000G_phase1.indels.hg19.sites.fixed.vcf" \
--mills "https://s3-us-west-2.amazonaws.com/bd2k-artifacts/10k-exomes/Mills_and_1000G_gold_standard.indels.hg19.sites.fixed.vcf" \
--dbsnp "https://s3-us-west-2.amazonaws.com/bd2k-artifacts/10k-exomes/dbsnp_132_b37.leftAligned.vcf" \
--cosmic "https://s3-us-west-2.amazonaws.com/bd2k-artifacts/10k-exomes/b37_cosmic_v54_120711.vcf"