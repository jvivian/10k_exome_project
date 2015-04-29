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
        self.foo_bam = None
        self.bar_bam = None


def hello_world(target, hw):

    # Create empty FileStoreID for foo_bam
    hw.foo_bam = target.getEmptyFileStoreID()

    with open('foo_bam.txt', 'w') as handle:
        handle.write('\nThis is a triumph...\n')

    # Update FileStoreID with an associated file
    target.updateGlobalFile(hw.foo_bam, 'foo_bam.txt')

    # Spawn child
    target.addChildTargetFn(hello_world_child, (hw,))


def hello_world_child(target, hw):

    path = target.readGlobalFile(hw.foo_bam)

    with open(path, 'a') as handle:
        handle.write("\nFileStoreID works!\n")

    # NOTE: path and the udpated file are stored to /tmp
    # If we want to SAVE our changes to this tmp file, we must write it out.

    # Create empty FileStoreID for bar_bam
    hw.bar_bam = target.getEmptyFileStoreID()

    with open(path, 'r') as r:
        with open('bar_bam.txt', 'w') as handle:
            for line in r.readlines():
                handle.write(line)

    # Update FileStoreID
    target.updateGlobalFile(hw.bar_bam, 'bar_bam.txt')


if __name__ == '__main__':

    # Boilerplate -- startJobTree requires options
    parser = OptionParser()
    Stack.addJobTreeOptions(parser)
    options, args = parser.parse_args()

    # Create object that contains our FileStoreIDs
    hw = HelloWorld()

    # Setup the job stack and launch jobTree job
    i = Stack(Target.makeTargetFn(hello_world, (hw,))).startJobTree(options)