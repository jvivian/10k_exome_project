# 4-13-15
#

"""
"Hello World" script for JobTree testing
"""

from jobTree.scriptTree.target import Target
from jobTree.scriptTree.stack import Stack
from optparse import OptionParser
import sys

'''
class HelloWorld(Target):
    def __init__(self):
        Target.__init__(self)

    def run(self):
        sys.stdout.write("Hello World!")
'''

def HelloWorld(target):
    sys.stdout.write("Hello World")

if __name__ == '__main__':

    # Boilerplate -- startJobTree requires options
    parser = OptionParser()
    Stack.addJobTreeOptions(parser)
    options, args = parser.parse_args()

    i = Stack(Target.makeTargetFn(HelloWorld)).startJobTree(options)

