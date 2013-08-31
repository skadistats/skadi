import unittest

import io as _io
import os
import sys

pwd = os.path.dirname(__file__)
root = os.path.abspath(os.path.join(pwd, '..'))
sys.path.append(root)

from skadi import *
from skadi import demo

DEMO_FILE_PATH = os.path.abspath(os.path.join(pwd, 'data/test.dem'))


class TestDemo(unittest.TestCase):
  demo = None

  @classmethod
  def setUpClass(cls):
    # Cache demo for re-use in multiple tests
    cls.demo = demo.construct(DEMO_FILE_PATH)

  def test_demo_construct(self):
    assert self.demo


if __name__ == '__main__':
  unittest.main()
