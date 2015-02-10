# John Vivian
# 2-10-15

"""
Boto test script for accessing the Amazon EC2 cloud service.
"""

import time
import sys
import boto.ec2
from boto.exception import EC2ResponseError


def delete_sec_group(ec2, sec_group_name):
    """ Deletes security group, swallowing the exception if the group is not found """
    try:
        ec2.delete_security_group(sec_group_name)
    except EC2ResponseError as e:
        if e.error_code == 'InvalidGroup.NotFound':
            pass
        else:
            raise e


def create_sec_group(ec2, sec_group_name):
    """ Creates Security Group -- Make sure to call delete_sec_group() first """
    sec = ec2.create_security_group(sec_group_name, 'Jvivian Boto SecGroup')
    port = 22
    sec.authorize('tcp', port, port, '0.0.0.0/0')


def check_key_pair(ec2, kp_name):
    """ Checks if key_pair exists -- key_pair should be setup prior to running  """
    if not [i for i in ec2.get_all_key_pairs() if str(i).split(':')[1] == kp_name]:
        sys.stderr.write("Key pair: {} does not exist, please import_key_pair prior to running.\n".format(kp_name))
        sys.exit(1)


def launch_instance(ec2, kp_name, sec_group_name):
    """ Launches the AWS EC2 Instance """
    instance = ec2.run_instances(
        'ami-dfc39aef',
        key_name=kp_name,
        instance_type='t2.micro',
        security_groups=[sec_group_name]
    ).instances[0]

    while instance.state != 'running':
        print 'Waiting for instance: {}, at DNS: {} to start'.format(instance.id, instance.dns_name)
        time.sleep(5)
        instance.update()

    print 'Success! EC2 Instance Launched \nInstance_Type: {} in {}'.format(instance.instance_type, instance.placement)


def main():
    # Create an EC2 object
    ec2 = boto.ec2.connect_to_region('us-west-2')

    # Define Key-Pair and Security Group names
    sec_group_name = 'jvboto'
    kp_name = 'jtvivian@gmail.com'

    # Delete and Create Security Group
    delete_sec_group(ec2, sec_group_name)
    create_sec_group(ec2, sec_group_name)

    # Check that key-pair exists
    check_key_pair(ec2, kp_name)

    # Launch the EC2-Instance
    #launch_instance(ec2, kp_name, sec_group_name)


if __name__ == "__main__":
    main()

    ''' Code snippet that handles import of key_pair '''
    # with open(os.path.expanduser('~/.ssh/aws.pub'), 'r') as f:
    # material = f.read()
    #ec2.import_key_pair(key_name, material)