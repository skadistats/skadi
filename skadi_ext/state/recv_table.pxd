

cpdef RecvTable mk(object dt, object recv_props)


cdef class RecvTable(object):
    cdef public object dt
    cdef public object recv_props
    cdef object _cache
