# John Vivian
# 4-14-15

"""
Unit tests for functions within the
"""

import unittest
from jobtree_gatk_pipeline import *


class DownloadInputTest(unittest.TestCase):

    def test(self):
        pair_dir = 'test_out/pair/'
        inputs = {'test': 'www.google.com/index.html',
                  'normal': 'www.google.com/index.html'}
        download_inputs(pair_dir, inputs, 'test', 'normal')

        self.assertTrue(os.path.exists('test_out/'))
        self.assertTrue(os.path.exists('test_out/pair/'))
        self.assertTrue(os.path.exists('test_out/index.html'))
        self.assertTrue(os.path.exists('test_out/pair/index.html'))


class UploadToS3Test(unittest.TestCase):

    def test(self):
        pair_dir = 'test/pair'
        file1 = 'test_out/index.html'
        file2 = 'test_out/index.fai'

        upload_to_S3(pair_dir, file1)
        upload_to_S3(pair_dir, file2)

        conn = boto.connect_s3()
        bucket = conn.get_bucket('bd2k-jobtree_gatk_pipeline')
        keys = bucket.get_all_keys()

        self.assertTrue('index.fai' in [x.name for x in keys])
        self.assertTrue('pair/index.html' in [x.name for x in keys])


class GetFileNamesTest(unittest.TestCase):

    def test(self):
        inputs = {'test': 'www.google.com/index.html',
                  'normal': 'www.google.com/index.html'}
        file_names = get_filenames(inputs, 'test', 'normal')

        self.assertEqual(file_names['test'], 'index.html')
        self.assertEqual(file_names['normal'], 'index.html')


class GetSharedDirTest(unittest.TestCase):

    def test(self):
        pair_dir = '/mnt/jobTree/{}/pair'.format(os.path.basename(__file__).split('.')[0])
        shared_dir = get_shared_dir(pair_dir)

        self.assertEqual(shared_dir, '/mnt/jobTree/{}'.format(os.path.basename(__file__).split('.')[0]))


def main():
    unittest.main()

if __name__ == '__main__':
    main()