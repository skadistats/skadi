from libc.stdint cimport int64_t, uint64_t, uint32_t
from cpython cimport array

cdef class Bitstream:
  cdef public int pos
  cdef int data_n
  cdef uint32_t *data

  cdef uint32_t _read(Bitstream self, int length)
  cdef void _read_data(Bitstream self, array.array[unsigned int] arr)
  cdef _dealloc(Bitstream self)
  cdef bytes _read_long(Bitstream self, int length)
  cdef bytes _read_string(Bitstream self, int length)
  cdef uint64_t _read_varint(Bitstream self)
