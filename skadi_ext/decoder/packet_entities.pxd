

cpdef PacketEntitiesDecoder mk(object recv_table_by_cls)


cdef class PacketEntitiesDecoder(object):
    cdef public object recv_table_by_cls
    cdef public int class_bits
    cdef public object decoders

    cpdef decode(PacketEntitiesDecoder self, object stream, int is_delta, int count, object world)
    cdef _decode_diff(PacketEntitiesDecoder self, object stream, int index, object entities)
    cdef _decode_deletion_diffs(PacketEntitiesDecoder self, stream)
