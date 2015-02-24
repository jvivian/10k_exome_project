#!/usr/bin/env python2.7

import boto.ec2
import subprocess
import sys
import time

def start_instance(conn_ec2, id='i-256f5229'):
    instances=conn_ec2.get_only_instances(instance_ids=[id])
    instance = instances[0]
    instance.start()
    while instance.state != 'running':
        sys.stdout.write('Waiting for instance: {}, at DNS: {} to start\n'.format(instance.id,
                                                                                str(instance.dns_name).split('.')[0]))
        time.sleep(5)
        instance.update()

    sys.stdout.write('\nSuccess! EC2 Instance Launched \nInstance_Type: {} in {}'.format(instance.instance_type,
                                                                                         instance.placement))
    return instance


def ssh_instance(instance):
    dest = 'ubuntu@' + str(instance.dns_name())
    print dest
    dest = 'ubuntu@' + 'ec2-52-10-225-111.us-west-2.compute.amazonaws.com'
    print dest
    #subprocess.check_call(['ssh', dest])


def main():
    # Create ec2 object
    conn_ec2 = boto.ec2.connect_to_region('us-west-2')
    instance = start_instance(conn_ec2)
    ssh_instance(instance)


if __name__ == '__main__':
    main()