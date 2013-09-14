from __future__ import absolute_import

import collections as c
import copy
import io as _io

from skadi import *
from skadi.engine import world as e_w
from skadi.engine import game_event as e_ge
from skadi.engine import modifiers as e_m
from skadi.engine import user_message as e_um
from skadi.index.embed import packet as ie_packet
from skadi.io.protobuf import demo as d_io
from skadi.io.protobuf import packet as p_io
from skadi.io.unpacker import string_table as u_st
from skadi.protoc import demo_pb2 as pb_d
from skadi.protoc import netmessages_pb2 as pb_n
from skadi.protoc import dota_modifiers_pb2 as pb_dm

try:
  from skadi.io import cBitstream as b_io
except ImportError:
  from skadi.io import bitstream as b_io
try:
  from skadi.io.unpacker import cEntity as u_ent
except ImportError:
  from skadi.io.unpacker import entity as u_ent


def scan(prologue, demo_io, tick=None):
  full_packets, remaining_packets = [], []

  if tick is not None:
    iter_bootstrap = iter(demo_io)

    try:
      p, m = next(iter_bootstrap)
      item = (p, d_io.parse(p.kind, p.compressed, m))

      while True:
        if p.kind == pb_d.DEM_FullPacket:
          full_packets.append(item)
          remaining_packets = []
        else:
          remaining_packets.append(item)

        if p.tick >= tick:
          break

        p, m = next(iter_bootstrap)
        item = (p, d_io.parse(p.kind, p.compressed, m))
    except StopIteration:
      raise EOFError()

  return full_packets, remaining_packets


def reconstitute(full_packets, class_bits, recv_tables, string_tables):
  w = e_w.construct(recv_tables)
  st = string_tables

  st_mn = st['ModifierNames']
  st_am = st['ActiveModifiers']
  m = e_m.construct(st_mn, baseline=st_am)

  for _, fp in full_packets:
    for table in fp.string_table.tables:
      assert not table.items_clientside

      entries = [(_i, e.str, e.data) for _i, e in enumerate(table.items)]
      st[table.table_name].update_all(entries)

      if table.table_name == 'ActiveModifiers':
        m.reset()
        [m.note(e) for e in entries]

  if full_packets:
    _, fp = full_packets[-1]
    packet = ie_packet.construct(p_io.construct(fp.packet.data))

    _, pe = packet.svc_packet_entities
    ct = pe.updated_entries
    bs = b_io.construct(pe.entity_data)
    unpacker = u_ent.construct(bs, -1, ct, False, class_bits, w)

    for index, mode, (cls, serial, diff) in unpacker:
      data = st['instancebaseline'].get(cls)[1]
      bs = b_io.construct(data)
      unpacker = u_ent.construct(bs, -1, 1, False, class_bits, w)

      state = unpacker.unpack_baseline(recv_tables[cls])
      state.update(diff)

      w.create(cls, index, serial, state, dict(diff))

  return w, m, st


def construct(*args):
  return Demo(*args)


class Stream(object):
  def __init__(self, prologue, io, world, mods, sttabs, rem, sparse=False):
    self.prologue = prologue
    self.demo_io = d_io.construct(io)
    self.tick = None
    self.user_messages = None
    self.game_events = None
    self.world = world
    self.modifiers = mods
    self.string_tables = sttabs
    self.sparse = sparse

    for p, pb in rem:
      self.advance(p.tick, pb)

  def __iter__(self):
    iter_entries = iter(self.demo_io)

    if self.tick is not None:
      t = self.tick
      um, ge = self.user_messages, self.game_events
      w, m = self.world, self.modifiers
      yield [t, um, ge, w, m]

    while True:
      peek, message = next(iter_entries)

      if peek.kind == pb_d.DEM_FullPacket:
        continue
      elif peek.kind == pb_d.DEM_Stop:
        raise StopIteration()
      else:
        pbmsg = d_io.parse(peek.kind, peek.compressed, message)
        self.advance(peek.tick, pbmsg)

      t = self.tick
      um, ge = self.user_messages, self.game_events
      w, m = self.world, self.modifiers
      yield [t, um, ge, w, m]

  def iterfullticks(self):
    iter_entries = iter(self.demo_io)

    while True:
      peek, message = next(iter_entries)

      if peek.kind == pb_d.DEM_Stop:
        raise StopIteration()
      elif peek.kind != pb_d.DEM_FullPacket:
        continue

      pro = self.prologue

      full_packet = (peek, d_io.parse(peek.kind, peek.compressed, message))
      self.world, self.modifiers, self.string_tables = reconstitute(
        [full_packet], pro.class_bits, pro.recv_tables, self.string_tables)
      self.tick = peek.tick
      self.user_messages = []
      self.game_events = []
      yield [self.tick, self.user_messages, self.game_events, self.world,
             self.modifiers]

  def advance(self, tick, pbmsg):
    self.tick = tick

    packet = ie_packet.construct(p_io.construct(pbmsg.data))
    am_entries = []

    for _, _pbmsg in packet.all_svc_update_string_table:
      key = self.string_tables.keys()[_pbmsg.table_id]
      _st = self.string_tables[key]

      bs = b_io.construct(_pbmsg.string_data)
      ne = _pbmsg.num_changed_entries
      eb, sf, sb = _st.entry_bits, _st.size_fixed, _st.size_bits

      entries = u_st.construct(bs, ne, eb, sf, sb)
      if key == 'ActiveModifiers':
        am_entries = list(entries)
      else:
        [_st.update(e) for e in entries]

    um = packet.find_all(pb_n.svc_UserMessage)
    self.user_messages = [e_um.parse(p_io.parse(p.kind, m)) for p, m in um]

    ge = packet.find_all(pb_n.svc_GameEvent)
    gel = self.prologue.game_event_list
    self.game_events = [e_ge.parse(p_io.parse(p.kind, m), gel) for p, m in ge]

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

        self.world.create(cls, index, serial, state, dict(diff))
      elif mode & u_ent.PVS.Deleting:
        self.world.delete(index)
      elif mode ^ u_ent.PVS.Leaving:
        state = dict(context) if self.sparse else dict(self.world.find_index(index), **context)
        diff = state if self.sparse else dict(context)

        self.world.update(index, state, diff)

    [self.modifiers.note(e) for e in am_entries]
    self.modifiers.limit(self.world)

    _, gamerules = self.world.find_by_dt('DT_DOTAGamerulesProxy')
    game_time_key = ('DT_DOTAGamerulesProxy', 'DT_DOTAGamerules.m_fGameTime')
    self.modifiers.expire(gamerules[game_time_key])

  def _report(self):
    t = self.tick
    um, ge = self.user_messages, self.game_events
    w, m = self.world, self.modifiers
    return t, um, ge, w, m


class Demo(object):
  def __init__(self, abspath):
    infile = _io.open(abspath, 'r+b')
    if infile.read(8) != "PBUFDEM\0":
      raise InvalidDemo('malformed header')

    gio = bytearray(infile.read(4)) # LE uint file offset
    gio = sum(gio[i] << (i * 8) for i in range(4))

    try:
      tell = infile.tell()
      infile.seek(gio)
      p, m = d_io.construct(infile).read()
      self.file_info = d_io.parse(p.kind, p.compressed, m)
      assert p.kind == pb_d.DEM_FileInfo
      infile.seek(tell)
    except EOFError:
      raise InvalidDemo('no end game summary')

    self.prologue = load(infile)
    self.io = infile
    self._tell = infile.tell()

  def stream(self, tick=None, sparse=False):
    self.io.seek(self._tell)

    p = self.prologue
    fp, rem = scan(p, d_io.construct(self.io), tick=tick)
    clean_st = copy.deepcopy(p.string_tables)
    w, m, st = reconstitute(fp, p.class_bits, p.recv_tables, clean_st)

    return Stream(p, self.io, w, m, st, rem, sparse=sparse)
