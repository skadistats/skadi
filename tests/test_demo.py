import unittest

import io
import os
import sys

pwd = os.path.dirname(__file__)
root = os.path.abspath(os.path.join(pwd, '..'))
sys.path.append(root)

from skadi.replay import demo as rd

DEMO_FILE_PATH = os.path.abspath(os.path.join(pwd, 'data/test.dem'))


class TestDemo(unittest.TestCase):
  demo = None

  @classmethod
  def setUpClass(cls):
    # Cache demo for re-use in multiple tests
    with io.open(DEMO_FILE_PATH, 'r+b') as infile:
      cls.demo = rd.construct(infile)

  def test_demo_construct(self):
    self.assertEqual(self.demo.server_info['map_name'], u'dota')


if __name__ == '__main__':
  unittest.main()
