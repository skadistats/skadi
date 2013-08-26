import collections as c
import copy
import io

from skadi.engine import world as w
from skadi import index as i
from skadi.io import bitstream as b_io
from skadi.io.protobuf import demo as d_io
from skadi.io.protobuf import packet as p_io
from skadi.io.unpacker import entity as uent
from skadi.io.unpacker import string_table as ust
from skadi.io.unpacker.entity import PVS
from skadi.protoc import netmessages_pb2 as pb_n


def construct(*args):
  stream = Stream(*args)
  stream.bootstrap()
  return stream


Snapshot = c.namedtuple('Snapshot', [
  'tick', 'modifiers', 'world'
])


class Stream(object):
  def __init__(self, io, match, tick, cb, rt, st, modifiers, world):
    self.io = io
    self.match = match
    self.tick = 0
    self.class_bits = cb
    self.recv_tables = rt
    self.modifiers = copy.deepcopy(modifiers)
    self.string_tables = copy.deepcopy(st)
    self.world = copy.deepcopy(world)
    self._bootstrap_tick = match.locate_tick(tick)
    self._baseline_cache = {}

  def __iter__(self):
    def advance():
      peek, message = next(self.entries)
      pbmsg = d_io.parse(peek.kind, peek.compressed, message)
      return self.advance(peek.tick, pbmsg)

    return iter(advance, None)

  def bootstrap(self):
    match = self.match

    full_packet_tick = match.locate_full_tick(self._bootstrap_tick)
    self.entries = match.lookup_between(full_packet_tick, match.ticks[-1])

    gen = iter(self)
    while self.tick < self._bootstrap_tick:
      next(gen)

  def advance(self, tick, pbmsg):
    self.tick = tick

    st, cb, rt = self.string_tables, self.class_bits, self.recv_tables
    st_ib = st['instancebaseline']

    index = i.construct(p_io.construct(pbmsg.data))
    upd_st = index.find_all(pb_n.svc_UpdateStringTable)

    for _pbmsg in [p_io.parse(p.kind, m) for p, m in upd_st]:
      key = self.string_tables.keys()[_pbmsg.table_id]
      _st = self.string_tables[key]

      ne = _pbmsg.num_changed_entries
      eb, sf, sb = _st.entry_bits, _st.size_fixed, _st.size_bits
      bs = b_io.construct(_pbmsg.string_data)

      for entry in ust.unpack(bs, ne, eb, sf, sb):
        _st.update(entry)

    p, m = index.find(pb_n.svc_PacketEntities)
    pe = p_io.parse(p.kind, m)
    ct = pe.updated_entries
    bs = b_io.construct(pe.entity_data)

    unpacker = uent.unpack(bs, -1, ct, False, cb, self.world)

    for index, mode, context in unpacker:
      if mode & PVS.Entering:
        cls, serial, diff = context

        if cls not in self._baseline_cache:
          data = st['instancebaseline'].get(cls)[1]
          bs = b_io.construct(data)
          unpacker = uent.unpack(bs, -1, 1, False, cb, self.world)

          self._baseline_cache[cls] = unpacker.unpack_baseline(rt[cls])

        state = dict(self._baseline_cache[cls])
        state.update(diff)

        self.world.create(cls, index, serial, state)
      elif mode & PVS.Deleting:
        self.world.delete(index)
      elif mode ^ PVS.Leaving:
        state = dict(self.world.find_index(index))
        state.update(context)

        self.world.update(index, state)

    return Snapshot(self.tick, self.modifiers, self.world)
