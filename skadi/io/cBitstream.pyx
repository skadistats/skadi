from libc cimport stdlib
from libc.stdint cimport int64_t, uint32_t, uint64_t, uint8_t
from cpython cimport array

DEF SIZEOF_WORD_BYTES = 4
DEF SIZEOF_WORD_BITS = SIZEOF_WORD_BYTES * 8

def construct(_bytes):
  return Bitstream(_bytes)

cdef extern from "arpa/inet.h":
  uint32_t ntohl(uint32_t)

cdef class Bitstream:
  def __cinit__(Bitstream self):
    self.pos = 0
    self.data = NULL
    self.data_n = 0

  cdef void _read_data(Bitstream self, array.array[unsigned int] arr):
    self.data_n = len(arr)
    self.data = <uint32_t*>stdlib.malloc(self.data_n * sizeof(uint32_t))
    if self.data is NULL:
      raise MemoryError()
    self.pos = 0

    cdef int i = 0
    cdef uint32_t be
    for i in range(self.data_n):
      be = ntohl(<uint32_t>arr[i])
      self.data[i] = (((be & 0xFF) << 24) |
                      ((be & 0xFF00) << 8) |
                      ((be >> 8) & 0xFF00) |
                      (be >> 24))

  def __init__(self, _bytes):
    remainder = len(_bytes) % 4
    if remainder:
      _bytes = _bytes + "\0" * (4 - remainder)
    self._read_data(array.array("I", _bytes))

  cdef uint32_t _get(Bitstream self, int pos):
    return self.data[pos]

  def _read(self, length): # in bits
    try:
      if (self.pos + length - 1) / SIZEOF_WORD_BITS >= self.data_n:
        raise IndexError()
      l = self._get(self.pos / SIZEOF_WORD_BITS)
      r = self._get((self.pos + length - 1) / SIZEOF_WORD_BITS)
    except IndexError:
      raise EOFError('bitstream at end of data')

    pos_shift = self.pos & (SIZEOF_WORD_BITS - 1)
    rebuild = r << (SIZEOF_WORD_BITS - pos_shift) | l >> pos_shift

    self.pos += length

    return int(rebuild & ((1 << length) - 1))

  # cdef int64_t _read(Bitstream self, int length) except -1:
  #   cdef int lp, rp
  #   lp = self.pos / SIZEOF_WORD_BITS
  #   rp = (self.pos + length - 1) / SIZEOF_WORD_BITS

  #   cdef uint32_t l, r
  #   l = self.data[lp]
  #   r = self.data[rp]
  #   if lp >= self.data_n or rp >= self.data_n:
  #     raise EOFError("bitstream at end of data")

  #   cdef uint32_t pos_shift, rebuild
  #   pos_shift = self.pos & (SIZEOF_WORD_BITS - 1)
  #   rebuild = r << (SIZEOF_WORD_BITS - pos_shift) | l >> pos_shift

  #   self.pos += length

  #   return <int64_t>(rebuild & ((1 << length) - 1))

  cdef _dealloc(Bitstream self):
    if self.data != NULL:
      stdlib.free(self.data)

  def __dealloc__(Bitstream self):
    self._dealloc()

  def read(self, length):
    return self._read(length)

  cdef bytes _read_long(Bitstream self, int length):
    cdef unsigned char *data = <unsigned char*>stdlib.malloc(sizeof(char) * (length / 8 + 1))
    cdef int i, remainder
    i = 0
    remainder = length
    while remainder > 7:
      data[i] = <unsigned char>self.read(8)
      remainder -= 8
      i += 1
    
    if remainder:
      data[i] = <unsigned char>self._read(remainder)
      i += 1

    cdef bytes output
    try:
      # Need to specify the length to deal with embedded NULLs
      output = data[:i]
    finally:
      stdlib.free(data)
    return output

  def read_long(self, length):
    return self._read_long(length)

  cdef bytes _read_string(Bitstream self, int length):
    cdef unsigned char *data = <unsigned char*>stdlib.malloc(sizeof(char) * (length + 1))
    cdef int i
    i = 0
    while i < length:
      data[i] = <unsigned char>self.read(8)
      if data[i] == 0:
        break
      i += 1
    
    cdef bytes output
    try:
      # Need to specify the length to deal with embedded NULLs
      output = data[:i]
    finally:
      stdlib.free(data)
    return output

  def read_string(self, length):
    return self._read_string(length)

  cdef uint64_t _read_varint(Bitstream self):
    cdef uint64_t run, value
    run = value = 0

    cdef uint64_t bits
    while True:
      bits = self.read(8)
      value |= (bits & 0x7f) << run
      run += 7

      if not (bits >> 7) or run == 35:
        break

    return value

  def read_varint(self):
    return self._read_varint()
