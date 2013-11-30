

cpdef Index mk(object entries)


cdef class Index:
    cdef public object entries_by_kind

    cdef void _init_entries_by_kind(Index self, object entries)
    cpdef object find_kind(Index self, int kind)
    cpdef object find_all_kind(Index self, int kind)
