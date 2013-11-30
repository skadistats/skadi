import collections as c
import math

from skadi.state.util import String


cdef int MAX_NAME_LENGTH = 0x400
cdef int KEY_HISTORY_SIZE = 32


cpdef StringTableDecoder mk(object pb):
    cdef object me = pb.max_entries
    cdef object udfs = pb.user_data_fixed_size
    cdef object udsb = pb.user_data_size_bits

    return StringTableDecoder(me, udfs, udsb)


cdef class StringTableDecoder(object):
    def __init__(StringTableDecoder self, object max_entries, object user_data_sz_fixed, object user_data_sz_bits):
        self.entry_sz_bits = int(math.ceil(math.log(max_entries, 2)))
        self.user_data_sz_fixed = user_data_sz_fixed
        self.user_data_sz_bits = user_data_sz_bits

    cpdef object decode(StringTableDecoder self, object stream, object num_entries):
        cdef int mystery_flag = stream.read_numeric_bits(1)
        cdef object key_history = c.deque()
        cdef index = -1

        diff = []

        while len(diff) < num_entries:
            index = self._decode_index(stream, index)
            name = self._decode_name(stream, mystery_flag, key_history)
            value = self._decode_value(stream)
            diff.append(String(index, name, value))

        return diff

    cdef int _decode_index(StringTableDecoder self, object stream, int i):
        if stream.read_numeric_bits(1):
            i += 1
        else:
            i = stream.read_numeric_bits(self.entry_sz_bits)

        return i

    cdef object _decode_name(StringTableDecoder self, object stream, object mystery_flag, object key_history):
        cdef object name = None
        cdef object basis
        cdef int length

        if stream.read_numeric_bits(1):
            assert not (mystery_flag and stream.read_numeric_bits(1))

            if stream.read_numeric_bits(1):
                basis = stream.read_numeric_bits(5)
                length = stream.read_numeric_bits(5)
                name = key_history[basis][0:length]
                name += stream.read_string(MAX_NAME_LENGTH - length)
            else:
                name = stream.read_string(MAX_NAME_LENGTH)

            if len(key_history) == KEY_HISTORY_SIZE:
                key_history.popleft()

            key_history.append(name)

        return name

    cdef object _decode_value(StringTableDecoder self, object stream):
        cdef object value = ''
        cdef int bit_length

        if stream.read_numeric_bits(1):
            if self.user_data_sz_fixed:
                bit_length = self.user_data_sz_bits
            else:
                bit_length = stream.read_numeric_bits(14) * 8

            value = stream.read_bits(bit_length)

        return value
