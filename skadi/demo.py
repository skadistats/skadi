import collections as c
import copy

from skadi import index as i
from skadi.engine import world as w
from skadi.engine import game_event as e_ge
from skadi.engine import user_message as e_um
from skadi.engine.observer import active_modifier as o_am
from skadi.io import bitstream as b_io
from skadi.io.protobuf import demo as d_io
from skadi.io.protobuf import packet as p_io
from skadi.io.unpacker import entity as u_ent
from skadi.io.unpacker import string_table as u_st
from skadi.protoc import demo_pb2 as pb_d
from skadi.protoc import netmessages_pb2 as pb_n
from skadi.protoc import dota_modifiers_pb2 as pb_dm


def fast_forward(prologue, demo_io, tick=None):
  full_packets, remaining_packets = [], []

  world = w.construct(prologue.recv_tables)
  string_tables = copy.deepcopy(prologue.string_tables)

  if tick:
    iter_bootstrap = iter(demo_io)

    try:
      while True:
        p, m = next(iter_bootstrap)

        if p.kind == pb_d.DEM_FullPacket:
          full_packets.append((p, m))
          remaining_packets = []
        else:
          remaining_packets.append((p, m))

        if p.tick > tick - 2: # hack?
          break
    except StopIteration:
      raise EOFError()

  if full_packets:
    for peek, message in full_packets:
      full_packet = d_io.parse(peek.kind, peek.compressed, message)

      for table in full_packet.string_table.tables:
        assert not table.items_clientside

        entries = [(_i, e.str, e.data) for _i, e in enumerate(table.items)]
        string_tables[table.table_name].update_all(entries)

    peek, message = full_packets[-1]
    pbmsg = d_io.parse(peek.kind, peek.compressed, message)
    packet = i.construct(p_io.construct(pbmsg.packet.data))

    peek, message = packet.find(pb_n.svc_PacketEntities)
    pe = p_io.parse(peek.kind, message)
    ct = pe.updated_entries
    bs = b_io.construct(pe.entity_data)
    unpacker = u_ent.construct(bs, -1, ct, False, prologue.class_bits, world)

    for index, mode, (cls, serial, diff) in unpacker:
      data = string_tables['instancebaseline'].get(cls)[1]
      bs = b_io.construct(data)
      unpacker = u_ent.construct(bs, -1, 1, False, prologue.class_bits, world)

      state = unpacker.unpack_baseline(prologue.recv_tables[cls])
      state.update(diff)

      try:
        world.create(cls, index, serial, state)
      except AssertionError, e:
        # TODO: log here.
        pass

  return world, string_tables, remaining_packets


def construct(*args):
  return Demo(*args)


class Stream(object):
  def __init__(self, prologue, io, world, string_tables, remaining_packets):
    self.prologue = prologue
    self.demo_io = d_io.construct(io)
    self.world = world
    self.string_tables = string_tables

    for peek, message in remaining_packets:
      pbmsg = d_io.parse(peek.kind, peek.compressed, message)
      self.advance(peek.tick, pbmsg)

  def __iter__(self):
    iter_entries = iter(self.demo_io)

    def advance():
      try:
        peek, message = next(iter_entries)

        if peek.kind == pb_d.DEM_FullPacket:
          return advance() # skip
        elif peek.kind == pb_d.DEM_Stop:
          raise StopIteration()

        pbmsg = d_io.parse(peek.kind, peek.compressed, message)

        return self.advance(peek.tick, pbmsg)
      except StopIteration:
        return None

    return iter(advance, None)

  def advance(self, tick, pbmsg):
    packet = i.construct(p_io.construct(pbmsg.data))
    all_ust = packet.find_all(pb_n.svc_UpdateStringTable)

    for _pbmsg in [p_io.parse(p.kind, m) for p, m in all_ust]:
      key = self.string_tables.keys()[_pbmsg.table_id]
      _st = self.string_tables[key]

      bs = b_io.construct(_pbmsg.string_data)
      ne = _pbmsg.num_changed_entries
      eb, sf, sb = _st.entry_bits, _st.size_fixed, _st.size_bits

      for entry in u_st.construct(bs, ne, eb, sf, sb):
        _st.update(entry)

    p, m = packet.find(pb_n.svc_PacketEntities)
    pe = p_io.parse(p.kind, m)
    ct = pe.updated_entries
    bs = b_io.construct(pe.entity_data)

    class_bits = self.prologue.class_bits
    recv_tables = self.prologue.recv_tables

    unpacker = u_ent.construct(bs, -1, ct, False, class_bits, self.world)

    for index, mode, context in unpacker:
      if mode & u_ent.PVS.Entering:
        cls, serial, diff = context

        data = self.string_tables['instancebaseline'].get(cls)[1]
        bs = b_io.construct(data)
        unpacker = u_ent.construct(bs, -1, 1, False, class_bits, self.world)

        state = unpacker.unpack_baseline(self.prologue.recv_tables[cls])
        state.update(diff)

        self.world.create(cls, index, serial, state)
      elif mode & u_ent.PVS.Deleting:
        self.world.delete(index)
      elif mode ^ u_ent.PVS.Leaving:
        state = dict(self.world.find_index(index))
        state.update(context)

        self.world.update(index, state)

    all_um = packet.find_all(pb_n.svc_UserMessage)
    user_messages = [e_um.parse(p_io.parse(p.kind, m)) for p, m in all_um]

    all_ge = packet.find_all(pb_n.svc_GameEvent)
    gel = self.prologue.game_event_list
    game_events = [e_ge.parse(p_io.parse(p.kind, m), gel) for p, m in all_ge]

    modifiers = self.string_tables['ActiveModifiers'].observer

    _, gamerules = self.world.find_by_dt('DT_DOTAGamerulesProxy')
    modifiers.expire(gamerules[('DT_DOTAGamerules', 'm_fGameTime')])

    return tick, user_messages, game_events, self.world, modifiers


class Demo(object):
  def __init__(self, prologue, io):
    self.prologue = prologue
    self.io = io
    self._tell = io.tell()

  def stream(self, tick=0):
    self.io.seek(self._tell)
    args = fast_forward(self.prologue, d_io.construct(self.io), tick=tick)
    return Stream(self.prologue, self.io, *args)
