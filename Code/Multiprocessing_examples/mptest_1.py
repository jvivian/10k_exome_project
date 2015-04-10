__author__ = 'Jvivian'

"""
Start by writing a function that handles one child reading from a queue that
is pre-populated at the start of the program.
Run that function in the main thread of your program.
"""

from Queue import Queue
from subprocess import Popen, PIPE, call
from threading import Thread
import sys

def handler():
    item = q.get()
    if item != 'S':
        print "Sleeping: {}".format( item )
        call(["time", "sleep", str(item)])#, stdout=PIPE, stderr=PIPE)
    else:
        print "Sentinel Found"


if __name__ == '__main__':

    # Num_Threads
    N = 1

    # create Queue object
    q = Queue()

    # pre-populate queue
    q.put(1)
    q.put(5)
    q.put(2)
    q.put(2)


    while not q.empty():
        for i in xrange(N):
            t = Thread(target=handler)
            t.start()
        t.join()
