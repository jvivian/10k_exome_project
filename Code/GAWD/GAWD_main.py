#!/usr/bin/env python2.7
# John Vivian

'''
Galaxy Automatic Workflow Decomposer

Accepts a Galaxy Workflow (.ga) and tool-descriptors (.xml) to decompose a galaxy's graph structure
into discrete steps.
'''


import json
import xml.etree.ElementTree as ET
import os
import fnmatch
import argparse

def parse_arguments():
    parser = argparse.ArgumentParser()

    parser.add_argument('-d', '--galaxy_dir', required=True, default=None, help='Specify Galaxy Directory' )
    return parser.parse_args()


def find_files(pattern, path):
    '''Find file in path'''
    result = []
    for root, dirs, files in os.walk(path):
        for name in files:
            if fnmatch.fnmatch(name, pattern):
                result.append(os.path.join(root, name))
    return result


def parse_gal_workflow( gal_wflow ):
    '''Parses Galaxy Workflow'''
    print gal_wflow
    json_data=open( gal_wflow[0] )
    parsed = json.load( json_data )

    return parsed['steps']

def main():
    args = parse_arguments()

    print "\nGalaxy Workflow Dir:  {}".format( args.galaxy_dir )

    # Fetch Workflow and XML file names
    tool_xmls = find_files('*.xml', args.galaxy_dir)
    gal_wflow = find_files('*Slim.ga', args.galaxy_dir)  # Change to *.ga when appropriate

    # Parse Galaxy Workflow
    parse_gal_workflow( gal_wflow )






if __name__ == '__main__':
    main()