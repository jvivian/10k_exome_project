# John Vivian
# 4-14-15

"""
Unit tests for functions within the
"""

import unittest
#import jobTree_GATK_Pipeline

class DownloadInputTests(unittest.TestCase):



# Here's our "unit".
def IsOdd(n):
    return n % 2 == 1

# Here's our "unit tests".
class IsOddTests(unittest.TestCase):

    def testOne(self):
        self.assertTrue(IsOdd(1))

    def testTwo(self):
        self.assertFalse(IsOdd(2))

def main():
    unittest.main()

if __name__ == '__main__':
    main()