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
import argparse

def parse_arguments():
    parser = argparse.ArgumentParser()

    parser.add_argument('-d', '--galaxy_dir', required=True, default=None, help='Specify Galaxy Directory' )
    return parser.parse_args()


def fetch_files(dir):
    '''Fetches XML and .GA file'''
    tool_xmls = []
    gw_files = []
    for root, folder, files in os.walk( dir ):
        gw = [x for x in files if '.ga' in x]
        if gw:
            gw_files.append( gw )
        xmls = [x for x in files if '.xml' in x]
        if xmls:
            tool_xmls.append( xmls )
    # Flatten and return
    return [i for sublist in tool_xmls for i in sublist], [i for sublist in gw for i in sublist]


def main():
    args = parse_arguments()

    print "\nGalaxy Workflow Dir:  {}".format( args.galaxy_dir )

    tool_xmls, gal_wflow = fetch_files(args.galaxy_dir)


    
    tool_xmls = [item for sublist in tool_xmls for item in sublist]
    print gw_file
    print tool_xmls

if __name__ == '__main__':
    main()