# 4-13-15
# John Vivian

"""
'Hello World' script for JobTree
"""

from jobTree.scriptTree.target import Target
from jobTree.scriptTree.stack import Stack
from optparse import OptionParser


class HelloWorld(object):
    def __init__(self, s1, s2):
        self.s1 = s1
        self.s2 = s2

def hello_world(target, hw):
    with open ('hello_world.txt', 'w') as file:
        file.write(hw.s1)

    target.addChildTargetFn(hello_world_child, (hw,))


def hello_world_child(target, hw):
    with open ('hello_world_child.txt', 'w') as file:
        file.write(hw.s2)


if __name__ == '__main__':

    # Boilerplate -- startJobTree requires options
    parser = OptionParser()
    Stack.addJobTreeOptions(parser)
    options, args = parser.parse_args()

    s1 = 'This is a Triumph'
    s2 = "I'm making a note here; huge success"
    hw = HelloWorld(s1, s2)
    # Setup the job stack and launch jobTree job
    i = Stack(Target.makeTargetFn(hello_world, (hw,))).startJobTree(options)

    if i != 0:
        raise RuntimeError("Some of the jobs failed")