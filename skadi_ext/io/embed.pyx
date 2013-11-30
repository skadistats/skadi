import importlib as il
import io
import os
import snappy
import struct
import sys

__impl__ = 'skadi_ext' if os.environ.get('SKADI_EXT') else 'skadi'
io_util = il.import_module(__impl__ + '.io.util')

from skadi.io.util import Peek


cpdef EmbedIO mk(str data, tick=0):
    handle = io.BufferedReader(io.BytesIO(data))
    return EmbedIO(handle, tick=tick)


cdef class EmbedIO(object):
    cdef public object handle
    cdef public int tick

    def __init__(EmbedIO self, handle, tick=0):
        self.handle = handle
        self.tick = tick

    def __iter__(EmbedIO self):
        while True:
            try:
                yield self.read()
            except EOFError:
                raise StopIteration()

    cpdef read(self):
        try:
            kind = io_util.read_varint(self.handle)
            size = io_util.read_varint(self.handle)
            message = self.handle.read(size)

            assert len(message) == size
        except AssertionError:
            return None

        return Peek(False, kind, self.tick, size), message
