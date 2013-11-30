import collections as c


cpdef Index mk(entries):
    return Index(entries)


cdef class Index(object):
    cdef void _init_entries_by_kind(Index self, entries):
        entries_by_kind = c.defaultdict(list)

        for entry in entries:
            peek, _ = entry
            entries_by_kind[peek.kind].append(entry)

        self.entries_by_kind = entries_by_kind

    def __init__(Index self, object entries):
        self._init_entries_by_kind(entries)

    cpdef object find_kind(Index self, int kind):
        assert len(self.entries_by_kind[kind]) >= 1
        return self.entries_by_kind[kind][0]

    cpdef object find_all_kind(Index self, int kind):
        return self.entries_by_kind[kind]
