# 4-13-15
# John Vivian

"""
"Hello World" script for JobTree
"""

from jobTree.scriptTree.target import Target
from jobTree.scriptTree.stack import Stack
from optparse import OptionParser


def HelloWorld(target):
    with open ('HelloWorld.txt', 'w') as file:
        file.write('This is a triumph')

if __name__ == '__main__':

    # Boilerplate -- startJobTree requires options
    parser = OptionParser()
    Stack.addJobTreeOptions(parser)
    options, args = parser.parse_args()

    # Setup the job stack and launch jobTree job
    i = Stack(Target.makeTargetFn(HelloWorld)).startJobTree(options)