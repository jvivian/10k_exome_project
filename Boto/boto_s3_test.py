#!/usr/bin/env python2.7
# John Vivian

'''
Boto S3/SQS Simple Test
'''

import boto


# Create S3 object
conn = boto.connect_s3()

conn.get_all_buckets()