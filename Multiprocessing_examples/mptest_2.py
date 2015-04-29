__author__ = 'Jvivian'

"""
Run the function in N threads
"""

from Queue import Queue
from subprocess import Popen, PIPE, call
from threading import Thread
import os

def handler():
    item = q.get()
    if item != 'S':
        print "Sleeping: {}".format( item )
        call(["time", "sleep", str(item)])#, stdout=PIPE, stderr=PIPE)
    else:
        print "Sentinel Found"
        os._exit(1) # This is required over sys.exit(1) as sys.exit only exits the thread.

if __name__ == '__main__':

    # Num_Threads
    N = 2

    # create Queue object
    q = Queue()

    # pre-populate queue
    q.put(1)
    q.put(5)
    q.put(2)
    q.put(2)
    q.put('S')

    threads = []

    while not q.empty():
        for i in xrange(N):
            t = Thread(target=handler)
            threads.append(t)

        for t in threads:
            t.start()

        for t in threads:
            t.join()

        threads = []
