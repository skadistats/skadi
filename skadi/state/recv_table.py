from skadi.state.util import Flag


def _sorted(recv_props):
    """
    Flattening a SendTable (skadi.state.send_table) yields a list of unsorted
    "recv props." To be useful, this list must be sorted deterministically.

    Returns a duplicate, sorted list.

    FIXME: This is difficult to test.

    Arguments:
    recv_props -- an array of unsorted recv_props

    """
    recv_props = list(recv_props) # copy
    priorities = sorted(set([rp.pri for rp in recv_props] + [64]))
    offset = 0

    for priority in priorities:
        hole, cursor = offset, offset

        while cursor < len(recv_props):
            recv_prop = recv_props[cursor]

            flagged_changes_often = recv_prop.flags & Flag.ChangesOften
            changes_often = flagged_changes_often and priority is 64

            if changes_often or recv_prop.pri == priority:
                recv_props[hole], recv_props[cursor] = \
                    recv_props[cursor], recv_props[hole]
                hole, offset = hole + 1, offset + 1

            cursor += 1

    return recv_props


def mk(*args):
    dt, recv_props = args
    return RecvTable(dt, _sorted(recv_props))


class RecvTable(object):
    """
    A collection of "flattened" and sorted send table props (aka "recv props")
    and associated behaviors.

    A RecvTable instance and its recv props are used by a DTDecoder
    (skadi.decoder.dt) to decode updates from a packet entities Stream
    (skadi.decoder.stream).

    """

    def __init__(self, dt, recv_props):
        self.dt = dt
        self.recv_props = recv_props
        self._cache = dict()

    def __iter__(self):
        return iter(self.recv_props)

    def __getitem__(self, int_or_tuple):
        """
        Recv props are accessible in one of two ways, depending on arg type.

        Tuple-based access is cached to avoid multiple O(n) performance hits.

        Argument int_or_tuple, depending on type:
        integer -- an index into the recv props array
        tuple -- where tuple is (recv_prop.src, recv_prop.name)

        """
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
