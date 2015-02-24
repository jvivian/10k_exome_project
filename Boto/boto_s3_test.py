#!/usr/bin/env python2.7
# John Vivian

'''
Boto S3/SQS Simple Test
'''

import sys
import boto
from boto.sqs.message import Message


def get_bucket_keys(bucket_name='bd2k-test-data'):
    """Retrieves key-names for items in the designated bucket"""

    # Create S3 object
    conn = boto.connect_s3()

    # Set bucket variable for bd2k group
    try:
        bucket = conn.get_bucket(bucket_name)
    except:
        sys.stderr.write('Bucket failed to be retrieved')
        sys.exit(1)

    # Collects keys from S3 related to 10k
    return [ i for i in bucket.list() if 'testexome' in i.name ]


def create_sqs_queue(keys, q_name='john-test'):
    """ Creates an SQS Queue based on keys in a specified bucket """

    conn = boto.sqs.connect_to_region('us-west-2')
    q = conn.create_queue(q_name)

    for key in keys:
        m = Message()
        m.set_body(key.name)
        q.write(m)


def get_sqs_messages(q_name='john-test'):
    """ Retrieve messages -- Mostly a test function """

    conn = boto.sqs.connect_to_region('us-west-2')
    q = conn.get_queue(q_name)
    all_messages=[]
    rs=q.get_messages(10)
    while len(rs)>0:
        all_messages.extend(rs)
        rs=q.get_messages(10)

    for i in all_messages:
        print i.get_body()

    return all_messages



def main():

    # Retrieve keys for items in S3
    keys = get_bucket_keys()

    # Create SQS Queue
    create_sqs_queue(keys)

    # Retrieve messages
    messages = get_sqs_messages()

    # Example download...
    #keys[0].get_contents_to_filename(keys[0].name) # Downloads file where script is run

if __name__ == '__main__':
    main()