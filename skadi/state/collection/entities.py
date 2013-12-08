import collections as c

from skadi.state.util import Entity, PVS


MAX_EDICT_BITS = 11


def mk(*args):
    return EntitiesCollection(*args)


def to_e(index, serial):
  return (serial << MAX_EDICT_BITS) | index


def from_e(ehandle):
  index = ehandle & ((1 << MAX_EDICT_BITS) - 1)
  serial = ehandle >> MAX_EDICT_BITS
  return index, serial


class EntitiesCollection(object):
    def __init__(self, entry_by_index=None, recv_table_by_cls=None):
        self.entry_by_index = entry_by_index or {}
        self.recv_table_by_cls = recv_table_by_cls or {}
        self._entry_by_ehandle = None
        self._entries_by_cls = None

        # FIX ME: These need to be properties.

        # entry_by_dt = c.defaultdict(list)
        # entry_pvs_enter = dict() # by index
        # entry_pvs_leave = dict() # by index

        # for _, entry in self.entry_by_index.items():
        #     pvs, entity = entry

        #     entry_by_dt[recv_table_by_cls[entity.cls].dt].append(entry)

        #     if pvs is PVS.Enter:
        #         entry_pvs_enter[entity.ind] = entity
        #     elif pvs is PVS.Leave:
        #         entry_pvs_leave[entity.ind] = entity
        #     else:
        #         raise NotImplementedError()

        # self.entry_by_dt = entry_by_dt
        # self.entry_by_ehandle = entry_by_ehandle
        # self.entry_pvs_enter = entry_pvs_enter
        # self.entry_pvs_leave = entry_pvs_leave

    def __len__(self):
        return len(self.entry_by_index)

    def apply(self, patch):
        entry_by_index = self.entry_by_index.copy()

        for pvs, e in patch:
            if pvs == PVS.Enter:
                entry_by_index[e.ind] = (PVS.Enter, e)
            elif pvs == PVS.Preserve:
                assert e.ind in entry_by_index
                peek, entry = entry_by_index[e.ind]
                state = entry.state.copy()
                state.update(e.state)
                entry = (peek, Entity(e.ind, e.serial, e.cls, state))
                entry_by_index[e.ind] = entry
            elif pvs == PVS.Leave:
                _, entry = entry_by_index[e.ind]
                entry_by_index[entry.ind] = (PVS.Leave, entry)
            elif pvs == PVS.Delete and e.ind in entry_by_index:
                del entry_by_index[e.ind]

        return EntitiesCollection(entry_by_index, self.recv_table_by_cls)

    @property
    def entries_by_cls(self):
        if not self._entries_by_cls:
            _entries_by_cls = c.defaultdict(list)

            for _, entry in self.entry_by_index.items():
                pvs, entity = entry
                _entries_by_cls[entity.cls] = entry

            self._entries_by_cls = _entries_by_cls

        return self._entries_by_cls

    @property
    def entry_by_ehandle(self):
        if not self._entry_by_ehandle:
            _entry_by_ehandle = dict()

            for _, entry in self.entry_by_index.items():
                pvs, entity = entry
                _entry_by_ehandle[to_e(entity.ind, entity.serial)] = entry

            self._entry_by_ehandle = _entry_by_ehandle

        return self._entry_by_ehandle
