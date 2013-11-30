import unittest
import io
import os

from StringIO import StringIO
from skadi.io import demo as io_demo


class TestDemo(unittest.TestCase):
    @classmethod
    def mk(cls, handle):
        return io_demo.mk(handle)

    @classmethod
    def mkfilelike(cls, s):
        s = map(ord, s)
        return io.BufferedReader(io.BytesIO(bytearray(s)))

    def test_bootstrap_raises_on_invalid_header(self):
        filelike = TestDemo.mkfilelike('INVALID\0\0\0\0\0')
        fn = lambda: TestDemo.mk(filelike).bootstrap()
        self.assertRaises(io_demo.InvalidHeaderError, fn)

    def test_bootstrap_returns_game_info_offset_with_valid_data(self):
        filelike = TestDemo.mkfilelike('PBUFDEM\0\1\0\0\0')
        offset = TestDemo.mk(filelike).bootstrap()
        self.assertEqual(1, offset)

    def test_read_returns_peek_and_message_and_advances_stream(self):
        filelike = TestDemo.mkfilelike('\1\2\3\0\0\0')
        peek, message = TestDemo.mk(filelike).read()
        self.assertEqual(2, peek.tick)
        self.assertEqual(1, peek.kind)
        self.assertEqual(3, peek.size)
        self.assertFalse(peek.compressed)
        self.assertEqual('\0\0\0', message)

    def test_read_raises_on_incomplete_data(self):
        filelike = TestDemo.mkfilelike('\1\2\3')
        self.assertRaises(EOFError, lambda: TestDemo.mk(filelike).read())


if __name__ == '__main__':
    unittest.main()
