# 4-13-15
# John Vivian

"""
'Hello World' script for JTree
"""

from jobTree.src.target import Target
from jobTree.src.stack import Stack
from optparse import OptionParser


class HelloWorld(object):
    def __init__(self):
        self.foo_bam = Target.getEmptyFileStoreID()
        self.bar_bam = Target.getEmptyFileStoreID()


def hello_world(target, hw):

    with open('foo_bam.txt', 'w') as handle:
        handle.write('This is a triumph...')
    # Update FileStoreID with an associated file
    target.updateGlobalFile(hw.foo_bam, 'hello_world.txt')

    # Spawn child
    target.addChildTargetFn(hello_world_child, (hw,))


def hello_world_child(target, hw):

    # Return path for file we'd like to append
    path = target.readGlobalFile(hw.foo_bam)

    with open(path, 'a') as handle:
        handle.write("\nI'm making a note here: FileStoreID works!")

    with open('bar_bam.txt') as handle:
        handle.write("Poor bar_bam didn't want to be left out...")


if __name__ == '__main__':

    # Boilerplate -- startJobTree requires options
    parser = OptionParser()
    Stack.addJobTreeOptions(parser)
    options, args = parser.parse_args()

    # Create object that contains our FileStoreIDs
    hw = HelloWorld()
    # Setup the job stack and launch jobTree job
    i = Stack(Target.makeTargetFn(hello_world, (hw,))).startJobTree(options)

    if i != 0:
        raise RuntimeError("Some of the jobs failed")