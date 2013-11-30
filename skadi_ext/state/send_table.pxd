

cpdef mk(object pb)


cdef object _flatten(object l, object rp, object excl, object anc, object acc=?, object prx=?)


cdef object _flatten_collapsible(object l, object rp, object excl, object anc, object acc)


cpdef object flatten(object lookup, object descendant)


cdef class SendTable(object):
    cdef public object name
    cdef public object send_props
    cdef public object needs_flattening
