import collections as c

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
        self._recv_props = recv_props

        self._by_src = None
        self._by_name = None
        self._by_tuple = None

    def __iter__(self):
        return iter(self._recv_props)

    @property
    def by_index(self):
        """
        This instance's Prop (skadi.state.util) instances--a vanilla list.

        """
        return self._recv_props

    @property
    def by_src(self):
        """
        This instance's Prop (skadi.state.util) instances, in a dict, keyed by
        'src' attribute. This dict makes it possible to investigate a recv
        table's properties by DT ancestry.

        Each key corresponds to a list containing (int, Prop) entries. Each
        int is a valid key for the by_index property.

        """
        if self._by_src is None:
            self._by_src = c.defaultdict(list)

            for i, recv_prop in enumerate(self):
                self._by_src[recv_prop.src].append((i, recv_prop))

        return self._by_src

    @property
    def by_name(self):
        """
        This instance's Prop (skadi.state.util) instances, in a dict, keyed by
        'name' attribute. This dict makes it possible to investigate a recv
        table's properties by name, regardless of DT ancestry.

        Each key corresponds to a list containing (int, Prop) entries. Each
        int is a valid key for the by_index property.

        """
        if self._by_name is None:
            self._by_name = c.defaultdict(list)

            for i, recv_prop in enumerate(self):
                self._by_name[recv_prop.name].append((i, recv_prop))

        return self._by_name

    @property
    def by_tuple(self):
        """
        This instance's Prop (skadi.state.util) instances, in a dict, keyed by
        ('src', 'name') tuple. This dict makes it possible to investigate a
        recv table's properties by fully-qualified identifier.

        Each key corresponds to an (int, Prop) tuple. The int is a valid key
        for the by_index property.

        """
        if self._by_tuple is None:
            self._by_tuple = dict()

            for i, recv_prop in enumerate(self):
                _tuple = (recv_prop.src, recv_prop.name)
                self._by_tuple[_tuple] = (i, recv_prop)

        return self._by_tuple
