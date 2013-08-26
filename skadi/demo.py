from __future__ import absolute_import

import copy
import io

from skadi import stream
from skadi import index as i
from skadi.engine import world as w
from skadi.engine.observer import active_modifier as o_am
from skadi.index import match as i_m
from skadi.index import epilogue as i_e
from skadi.io import bitstream as b_io
from skadi.io.protobuf import demo as d_io
from skadi.io.protobuf import packet as p_io
from skadi.io.unpacker import entity as uent
from skadi.io.unpacker.entity import PVS
from skadi.protoc import demo_pb2 as pb_d
from skadi.protoc import netmessages_pb2 as pb_n


def construct(*args):
  return Demo(*args)


class Demo(object):
  class Index(i.Index):
    def __init__(self, iterable):
      super(Demo.Index, self).__init__(iterable)

    @property
    def match(self):
      peek, _ = self._stop
      return i_m.construct(self.find_behind(peek.tell))

    @property
    def epilogue(self):
      peek, _ = self._stop
      return i_e.construct(self.find_ahead(peek.tell))

    @property
    def _stop(self):
      return self.find(pb_d.DEM_Stop)

  def __init__(self, prologue, io):
    self.meta = prologue.meta
    self.recv_tables = prologue.recv_tables
    self.string_tables = prologue.string_tables
    self.game_event_list = prologue.game_event_list

    self.io = io
    self.index = Demo.Index(d_io.construct(self.io))

  def stream(self, tick=0):
    match = self.index.match
    cb, rt = self.meta.class_bits, self.recv_tables
    mm = o_am.construct()
    st = copy.deepcopy(self.string_tables)
    st_ib = st['instancebaseline']

    full_packets = filter(lambda (p, _): p.tick <= tick, match.full_packets)
    for peek, message in full_packets:
      full_packet = d_io.parse(peek.kind, peek.compressed, message)

      for table in full_packet.string_table.tables:
        assert not table.items_clientside

        if table.table_name == 'ActiveModifiers':
          observer = mm
        else:
          observer = None

        entries = [(_i, e.str, e.data) for _i, e in enumerate(table.items)]
        st[table.table_name].update_all(entries)

    peek, message = full_packets[-1]
    pbmsg = d_io.parse(peek.kind, peek.compressed, message)
    packet_index = i.construct(p_io.construct(pbmsg.packet.data))

    world = w.construct(rt)

    peek, message = packet_index.find(pb_n.svc_PacketEntities)
    pe = p_io.parse(peek.kind, message)
    ct = pe.updated_entries
    bs = b_io.construct(pe.entity_data)
    unpacker = uent.unpack(bs, -1, ct, False, cb, world)

    for index, mode, (cls, serial, diff) in unpacker:
      data = st['instancebaseline'].get(cls)[1]
      bs = b_io.construct(data)
      unpacker = uent.unpack(bs, -1, 1, False, cb, world)
      state = dict(unpacker.unpack_baseline(rt[cls]))
      state.update(diff)

      try:
        world.create(cls, index, serial, state)
      except AssertionError, e:
        print e

    return stream.construct(self.io, match, tick, cb, rt, st, mm, world)
