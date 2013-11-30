from skadi.state.util import Flag


cpdef RecvTable mk(object dt, object recv_props):
    cdef object priorities
    cdef int offset = 0
    cdef int hole, cursor
    cdef object recv_prop
    cdef int flagged_changes_often, changes_often

    recv_props = list(recv_props) # copy
    priorities = sorted(set([rp.pri for rp in recv_props] + [64]))

    for priority in priorities:

        hole = cursor = offset

        while cursor < len(recv_props):
            recv_prop = recv_props[cursor]
            flagged_changes_often = recv_prop.flags & Flag.ChangesOften
            changes_often = flagged_changes_often and priority is 64

            if changes_often or recv_prop.pri == priority:
                recv_props[hole], recv_props[cursor] = \
                    recv_props[cursor], recv_props[hole]
                hole, offset = hole + 1, offset + 1

            cursor += 1

    return RecvTable(dt, recv_props)


cdef class RecvTable(object):
    def __init__(self, dt, recv_props):
        self.dt = dt
        self.recv_props = recv_props
        self._cache = dict()

    def __iter__(self):
        return iter(self.recv_props)

    def __getitem__(self, int_or_tuple):
        ind = int_or_tuple

        if type(ind) in (int, long):
            return self.recv_props[ind]
        elif isinstance(ind, tuple):
            assert len(ind) == 2

            if ind in self._cache:
                return self._cache[ind]

            for recv_prop in self:
                _ind = (recv_prop.src, recv_prop.name)
                if _ind in self._cache:
                    continue

                self._cache[_ind] = recv_prop
                if _ind == ind:
                    return recv_prop

            return None

        raise NotImplementedError()
