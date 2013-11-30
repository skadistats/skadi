import unittest
import io
import os

from StringIO import StringIO
from skadi.io import embed


class TestEmbed(unittest.TestCase):
    @classmethod
    def mk(cls, handle):
        return embed.mk(handle, tick=1)

    @classmethod
    def mkfilelike(cls, s):
        return bytearray(map(ord, s))

    def test_read_returns_peek_and_message_and_advances_stream(self):
        peek, message = TestEmbed.mk('\1\2\0\0').read()
        self.assertEqual(1, peek.tick)
        self.assertEqual(1, peek.kind)
        self.assertEqual(2, peek.size)
        self.assertFalse(peek.compressed)
        self.assertEqual('\0\0', message)

    def test_read_raises_on_incomplete_data(self):
        self.assertRaises(EOFError, lambda: TestEmbed.mk('\1\2').read())


if __name__ == '__main__':
    unittest.main()
