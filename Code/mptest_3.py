__author__ = 'Jvivian'

"""
Then have another thread prompting the user for numbers and feeding the responses into the queue.
Think about how to terminate all threads cleanly.
"""

from Queue import Queue
from subprocess import call
from threading import Thread
import os

def handler():
    while True:
        item = q.get()
        if item != 'S':
            print "Sleeping: {}".format( item )
            call(["time", "sleep", str(item)])
        else:
            print "Sentinel Found"
            os._exit(1) # This is required over sys.exit(1) as sys.exit only exits the thread.

if __name__ == '__main__':

    # create Queue object
    q = Queue()

    # pre-populate queue
    q.put(1)
    q.put(5)
    q.put(2)
    q.put(2)

    # Create child thread for worker
    t = Thread(target=handler)
    t.start()

    # Create "implicit" thread for user input.
    while True:
        val = raw_input("Enter a number (or 'S' to signal exit): ")
        q.put(val)










