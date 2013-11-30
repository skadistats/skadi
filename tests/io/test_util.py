import unittest
import io
import os

from StringIO import StringIO
from skadi.io import util


class TestUtil(unittest.TestCase):
    @classmethod
    def mkfilelike(cls, *b):
        return io.BufferedReader(io.BytesIO(bytearray(b)))

    # 0200 == 0b10000000
    # 0001 == 0b00000001

    def test_read_varint_returns_value_on_valid_data(self):
        filelike = TestUtil.mkfilelike(0001)
        self.assertEqual(1, util.read_varint(filelike))

        filelike = TestUtil.mkfilelike(0200, 0200, 0200, 0200, 0001)
        self.assertEqual(268435456, util.read_varint(filelike))

    def test_read_varint_raises_on_lengthy_data(self):
        filelike = TestUtil.mkfilelike(0200, 0200, 0200, 0200, 0200, 0001)
        self.assertRaises(util.VarintTooLongError, util.read_varint, filelike)

    def test_read_varint_raises_on_incomplete_data(self):
        filelike = TestUtil.mkfilelike(0200)
        self.assertRaises(EOFError, util.read_varint, filelike)


if __name__ == '__main__':
    unittest.main()
