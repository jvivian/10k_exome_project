__author__ = 'Jvivian'

"""
Then have another thread prompting the user for numbers and feeding the responses into the queue.
Think about how to terminate all threads cleanly.
"""

from Queue import Queue
from subprocess import check_call
from threading import Thread
import os
import sys


#class Worker(Thread):
#
#    def __init__(self):
#        Thread.__init__(self)
#        # A flag to notify the thread that it should finish up and exit
#        self.kill_received = False

    #def run(self):
        #while not self.kill_received:
        #    self.handler()
    #    self.handler()


def handler():
    item = q.get()
    while item != -1:
        sys.stdout.write("\nSleeping: {}\n".format( item ))
        check_call(["time", "sleep", str(item)])
        item = q.get()

    print "\nSentinel found, thread closing."


def get_val(N):
    while True:
        val = raw_input("\nEnter a number (-1 or Enter to exit): ")
        if val != '':
            try:
                q.put(int(val))
            except ValueError:
                sys.stderr.write("User must enter an integer! Program exiting abruptly.")
                os._exit(1)
        else:
            for i in xrange(N):
                q.put(-1)
            break

if __name__ == '__main__':


    # Number of threads
    N = 2
    sys.stdout.write("\nJobs executing with {} threads\n".format(N))

    # create Queue object
    q = Queue()

    threads = []
    # Create child threads for jobs
    for i in xrange(N):
        t = Thread(target=handler)
        t.start()
        threads.append(t)

    # Create user input thread
    nt = Thread(target=get_val, args=[N])
    nt.daemon = True
    nt.start()

    # Block until jobs threads have been signalled to end
    for t in threads:
        t.join()
    sys.stdout.write("\nAll threads have been joined. Program Exiting...")

    #try:
    #    for t in threads:
    #        t.join()
    #    print 'test'
    #    #threads = [t.join(1) for t in threads]# if t is not None and t.isAlive()]
    #except KeyboardInterrupt:
    #    for t in threads:
    #        t.kill_received = True








