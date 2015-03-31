__author__ = 'Jvivian'

"""
Then have another thread prompting the user for numbers and feeding the responses into the queue.
Think about how to terminate all threads cleanly.
"""

from Queue import Queue
from subprocess import call, PIPE
from threading import Thread
import os
import sys

def handler():
    item = q.get()
    while item != 'S':
        sys.stdout.write("\nSleeping: {}\n".format( item ))
        call(["time", "sleep", str(item)], stdout=PIPE, stderr=PIPE)
        item = q.get()

    print "\nSentinel Found, Thread Ending"

def get_val():
    while True:
        val = raw_input("\nEnter a number (or 'S' to signal exit): ")
        q.put(val)

if __name__ == '__main__':

    # Number of threads
    N = 2

    # create Queue object
    q = Queue()

    # pre-populate queue
    q.put(1)
    q.put(5)
    q.put(2)
    q.put(2)

    threads = []
    # Create child threads for jobs
    for i in xrange(N):
        t = Thread(target=handler)
        t.start()
        threads.append(t)

    nt = Thread(target=get_val)
    nt.daemon = True
    nt.start()

    # Wait for job threads to die
    for thread in threads:
        thread.join()
    print "\nThreads joined, program terminating."










