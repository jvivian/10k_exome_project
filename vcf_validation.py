#!/usr/bin/env python 2.7
# John Vivian
# 3-9-15

import vcf

vcf_reader = vcf.Reader(open('/Users/Jvivian/Desktop/MuTect.pair8.vcf', 'r'))


vcf_writer = vcf.Writer(open('/Users/Jvivian/Desktop/test.vcf', 'w'), vcf_reader)
for record in vcf_reader:
	print record.FILTER
	#record.INFO={"SOMATIC" : True }
	#vcf_writer.write_record(record)