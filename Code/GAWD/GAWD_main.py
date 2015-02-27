#!/usr/bin/env python2.7
# John Vivian

'''
Galaxy Automatic Workflow Decomposer

Accepts a Galaxy Workflow (.ga) and tool-descriptors (.xml) to decompose a galaxy's graph structure
into discrete steps.

-==-

1.  User provides workflow and tools directory
2.  Parse .GA into input_data and tool objects.
3.

'''


import json
import xml.etree.ElementTree as ET
import os
import fnmatch
import argparse


class input_data():
    '''Input Data Object'''
    def __init__(self, attributes):
        self.name = attributes['name']          # This should be "Input dataset".
        self.id = attributes['id']              # Reference number for the input data
        self.tool_id = attributes['tool_id']    # For input data should be null (Except for Genetorrent)
        self.inputs = attributes['inputs']      # self.inputs['name'] yields actual name
        self.input_connections = attributes['input_connections'] # All inputs should have this field be empty
        self.outputs = attributes['outputs']    # Should be empty
        self.type = attributes['type']          # Should be: "data_input"
        self.level = 0                          # Level in the graph structure


class tool():
    '''Tool Object'''
    def __init__(self, attributes):
        self.name = attributes['name']          # Informal name; use tool_id
        self.id = attributes['id']              # Reference number for the tool
        self.tool_id = attributes['tool_id']    # Specifies tool_id (name)
        self.input_connections = attributes['input_connections']
        self.outputs = attributes['outputs']    # 
        self.type = attributes['type']          # Should be: "tool"
        self.postjob = attributes['post_job_actions'] #
        self.level = None                       # Set to None until defined

    def get_input_vals(self):
        '''Returns a list of input IDs -- This information helps establish precedence in the graph'''
        return [ x['id'] for x in self.input_connections ]


def parse_arguments():
    parser = argparse.ArgumentParser()

    parser.add_argument('-w, --galaxy_workflow', required=True, default=None, help='Specify Galaxy Workflow File (.ga)')
    parser.add_argument('-d', '--tools_dir', required=True, default=None, help='Specify Galaxy Tools Directory (.xmls)' )
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

    steps = parsed['steps']

    for i in steps:
        for item in steps[i]:
            print item
        break

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