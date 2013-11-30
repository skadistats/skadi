

cdef int MAX_NAME_LENGTH
cdef int KEY_HISTORY_SIZE


cpdef StringTableDecoder mk(object pb)


cdef class StringTableDecoder(object):
    cdef object entry_sz_bits
    cdef object user_data_sz_fixed
    cdef object user_data_sz_bits

    cpdef object decode(StringTableDecoder self, object stream, object num_entries)
    cdef int _decode_index(StringTableDecoder self, object stream, int i)
    cdef object _decode_name(StringTableDecoder self, object stream, object mystery_flag, object key_history)
    cdef object _decode_value(StringTableDecoder self, object stream)
