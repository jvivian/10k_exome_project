# John Vivian
# 4-14-15

"""
Unit tests for functions within the
"""

import unittest
import os
from jobTree_GATK_Pipeline import *


class DownloadInputTest(unittest.TestCase):

    def test(self):
        shared_dir = 'test_out/'
        pair_dir = 'test_out/pair/'
        inputs = {'test': 'www.google.com/index.html',
                  'normal': 'www.google.com/index.html'}
        file_names = download_inputs(shared_dir, pair_dir, inputs, 'test', 'normal')

        self.assertTrue(os.path.exists('test_out/'))
        self.assertTrue(os.path.exists('test_out/pair/'))
        self.assertTrue(os.path.exists('test_out/index.html'))
        self.assertTrue(os.path.exists('test_out/pair/index.html'))

        self.assertEqual(file_names['test'], 'index.html')
        self.assertEqual(file_names['normal'], 'index.html')


def main():
    unittest.main()

if __name__ == '__main__':
    main()