import importlib as il
import io
import os
import snappy
import struct
import sys

__impl__ = 'skadi_ext' if os.environ.get('SKADI_EXT') else 'skadi'
io_util = il.import_module(__impl__ + '.io.util')

from skadi.io.util import Peek


COMPRESSED_MASK = 0b01110000
LEN_HEADER = 8
LEN_OFFSET = 4


cpdef DemoIO mk(object handle):
    return DemoIO(handle)


cdef object InvalidHeaderError(RuntimeError):
    pass


cdef class DemoIO(object):
    cdef public object handle

    def __init__(DemoIO self, object handle):
        self.handle = handle

    def __iter__(self):
        while True:
            try:
                yield self.read()
            except EOFError:
                raise StopIteration()

    cpdef int bootstrap(DemoIO self) except -1:
        header = self.handle.read(LEN_HEADER)
        offset = self.handle.read(LEN_OFFSET)
        if header != 'PBUFDEM\0':
            raise InvalidHeaderError('header invalid')

        return struct.unpack('I', bytearray(offset))[0]

    cpdef object read(DemoIO self):
        try:
            kind = io_util.read_varint(self.handle)
            comp = bool(kind & COMPRESSED_MASK)
            kind = (kind & ~COMPRESSED_MASK) if comp else kind
            tick = io_util.read_varint(self.handle)
            size = io_util.read_varint(self.handle)
            message = self.handle.read(size)

            assert len(message) == size

            if comp:
                message = snappy.uncompress(message)
        except AssertionError:
            return None

        return Peek(comp, kind, tick, size), message
