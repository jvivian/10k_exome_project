# 4-13-15
# John Vivian

"""
'Hello World' script for JobTree
"""

from jobTree.scriptTree.target import Target
from jobTree.scriptTree.stack import Stack
from optparse import OptionParser

'''
class HelloWorld(object):
    def __init__(self, s1):
        self.s1 = s1
'''

def hello_world(target, s):
    with open ('hello_world.txt', 'w') as file:
        file.write(s)

    target.addChildTargetFn(hello_world_child)


def hello_world_child(target):
    with open ('hello_world_child.txt', 'w') as file:
        file.write('Sorry, the cake is a lie.')


if __name__ == '__main__':

    # Boilerplate -- startJobTree requires options
    parser = OptionParser()
    Stack.addJobTreeOptions(parser)
    options, args = parser.parse_args()

    s1 = 'Test'
    #hw = HelloWorld(s1)
    # Setup the job stack and launch jobTree job
    #i = Stack(Target.makeTargetFn(hello_world, (hw))).startJobTree(options)

    # Complains that I am giving hello_world 5 arguments instead of 2....
    i = Stack(Target.makeTargetFn(hello_world, (s1))).startJobTree(options)

    #i = Stack(Target.makeTargetFn(hello_world)).startJobTree(options) # WORKS!