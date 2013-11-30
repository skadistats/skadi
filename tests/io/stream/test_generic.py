import importlib as il
import os
import random
import unittest

__impl__ = 'skadi_ext' if os.environ.get('SKADI_EXT') else 'skadi'
c = 'c' if __impl__ == 'skadi_ext' else ''
dcdr_ary = il.import_module(__impl__ + '.decoder.recv_prop.{}array'.format(c))

from skadi_ext.io.stream import generic as io_strm_gnrc
from skadi.io.stream import generic as io_strm_pygnrc


class TestGeneric(unittest.TestCase):
    @unittest.skipIf(__impl__ == 'skadi_ext', 'skadi_ext not supported')
    def test_constructor_converts_string_to_array_of_uint32(self):
        data = '\1\1\0\0\1\2\0\0\1\3\0\0\1\4\0\0'
        stream = io_strm_pygnrc.mk(data)
        print stream
        self.assertEqual([257, 513, 769, 1025], stream.words)

    @unittest.skipIf(__impl__ == 'skadi_ext', 'skadi_ext not supported')
    def test_peek_numeric_bits_returns_value_without_advancing_pos(self):
        data = '\4\3\2\1'
        stream = io_strm_pygnrc.mk(data)
        pos = stream.pos
        self.assertEqual(4, stream.peek_numeric_bits(4))
        self.assertEqual(772, stream.peek_numeric_bits(16))
        self.assertEqual(16909060, stream.peek_numeric_bits(32))
        self.assertEqual(pos, stream.pos)

    def test_read_numeric_bits_returns_value_and_advances_pos(self):
        data = '\4\3\2\1'
        stream = io_strm_gnrc.mk(data)
        pos = stream.pos
        self.assertEqual(772, stream.read_numeric_bits(16))
        self.assertEqual(16, stream.pos)
        self.assertEqual(2, stream.read_numeric_bits(8))
        self.assertEqual(24, stream.pos)
        self.assertEqual(1, stream.read_numeric_bits(1))
        self.assertEqual(25, stream.pos)

    def test_read_bits_returns_value_and_advances_pos(self):
        data = '\4\3\2\1\4\3\2\1\4\3'
        stream = io_strm_gnrc.mk(data)
        pos = stream.pos
        self.assertEqual('\4', stream.read_bits(8))
        self.assertEqual(8, stream.pos)
        self.assertEqual('\3\2\1', stream.read_bits(24))
        self.assertEqual(32, stream.pos)

    def test_read_string_returns_value_and_advances_pos(self):
        data = 'ohai'
        stream = io_strm_gnrc.mk(data)
        self.assertEqual('ohai', stream.read_string(4))
        self.assertEqual(32, stream.pos)

    def test_read_string_terminates_early_and_advances_pos(self):
        data = 'oha\0'
        stream = io_strm_gnrc.mk(data)
        self.assertEqual('oha', stream.read_string(5))
        self.assertEqual(32, stream.pos)


@unittest.skipIf(__impl__ != 'skadi_ext', 'no alternative implementation')
class TestCythonGeneric(unittest.TestCase):
    # Number of times to run randomly generated tests
    ITER_N = 2 ** 8

    def generate_random_streams(self):
        bytes_n = random.randint(8, 8 * 8 - 1)
        input_bytes = bytearray()
        for _ in range(bytes_n):
            byte = random.randint(0, 2 ** 8 - 1)
            input_bytes.append(byte)
        cython_stream = io_strm_gnrc.mk(bytes(input_bytes))
        python_stream = io_strm_pygnrc.mk(bytes(input_bytes))
        return cython_stream, python_stream, input_bytes

    def test_read_numeric_bits(self):
        for _ in range(self.ITER_N):
            python, cython, bytes = self.generate_random_streams()
            read_n = random.randint(1, 8)
            python_out = python.read_numeric_bits(read_n)
            cython_out = cython.read_numeric_bits(read_n)
            err = "{} != {} ({}, {})".format(
                repr(python_out),
                repr(cython_out),
                read_n,
                repr(bytes)
            )
            self.assertEqual(python_out, cython_out, err)

    def test_read_bits(self):
        for _ in range(self.ITER_N):
            python, cython, bytes = self.generate_random_streams()
            read_n = random.randint(1, len(bytes) - 1)
            python_out = python.read_bits(read_n)
            cython_out = cython.read_bits(read_n)
            err = "{} != {} ({}, {})".format(
                repr(python_out),
                repr(cython_out),
                read_n,
                repr(bytes)
            )
            self.assertEqual(python_out, cython_out, err)

    def test_read_string(self):
        for _ in range(self.ITER_N):
            python, cython, bytes = self.generate_random_streams()
            read_n = random.randint(1, len(bytes) - 1)
            python_out = python.read_string(read_n)
            cython_out = cython.read_string(read_n)
            err = "{} != {} ({}, {})".format(
                repr(python_out),
                repr(cython_out),
                read_n,
                repr(bytes)
            )
            self.assertEqual(python_out, cython_out, err)


if __name__ == '__main__':
    unittest.main()
