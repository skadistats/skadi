from __future__ import absolute_import

import collections
import copy
import io
import sys

from skadi.decoder import entity as d_entity
from skadi.decoder import string_table as d_string_table
from skadi.io import bitstream as bitstream_io
from skadi.io.protobuf import demo as demo_io
from skadi.io.protobuf import packet as packet_io
from skadi.protoc import netmessages_pb2 as pb_n
from skadi.meta import string_table


test_update_st = lambda m: m.cls is pb_n.CSVCMsg_UpdateStringTable
test_packet_entities = lambda m: m.cls is pb_n.CSVCMsg_PacketEntities
test_voice_data = lambda m: m.cls is pb_n.CSVCMsg_VoiceData


def construct(demo, stream):
  keyframes = collections.OrderedDict()

  stt = demo.string_tables

  for tick, peek in demo._full.items():
    stream.seek(peek.offset)
    pb_full_packet = demo_io.read(stream, peek)

    pb_string_tables, base = pb_full_packet.string_table, stt
    stt = Replay.derive_string_tables(pb_string_tables, base)
    keyframes[tick] = Frame(tick, string_tables=stt)

    wrap = io.BufferedReader(io.BytesIO(pb_full_packet.packet.data))
    messages = list(packet_io.scan(wrap))

    pb_pent = next(m for m in messages if test_packet_entities(m))

    # snapshot = Snapshot(tick, [], [], collections.OrderedDict())
    # c, u, d = d_entity.read(
    #   io_b.Bitstream.wrapping(pb_pent.entity_data),
    #   pb_pent.updated_entries, pb_pent.is_delta,
    #   demo.class_bits, demo.class_info, demo.recv_tables,
    #   snapshot.entities
    # )
    #
    # print c, u, d

  return Replay(demo, stream, keyframes=keyframes)


class Snapshot(object):
  def __init__(self, tick, user_messages, game_events, entities):
    self.tick = tick
    self.user_messages = user_messages
    self.game_events = game_events
    self.entities = entities


class Frame(object):
  def __init__(self, tick, string_tables=None, snapshot=None):
    self.tick = tick
    self.string_tables = string_tables
    self.snapshot = snapshot


class Replay(object):
  @classmethod
  def derive_string_tables(cls, pb_string_tables, base):
    string_tables = collections.OrderedDict()

    def pb_string_tables_find(pb_stt, name):
      gen = (pb_st for pb_st in pb_stt if pb_st.table_name == name)
      return next(gen, None)

    for st_name, st in base.items():
      pb_st = pb_string_tables_find(pb_string_tables.tables, st_name)
      if pb_st:
        strings = [(pb_s.str, pb_s.data) for pb_s in pb_st.items]
        string_tables[st_name] = st.merge(strings)
      else:
        string_tables[st_name] = st

    return string_tables

  def __init__(self, demo, stream, keyframes=None):
    self.demo = demo
    self.stream = stream
    self.keyframes = keyframes or collections.OrderedDict()
    self._frame_cache = None

  def snapshot(self, tick):
    if not self._frame_cache or self._frame_cache_stale(tick):
      self._reset_frame_cache()
    self._populate_frame_cache(tick)

  def _populate_frame_cache(self, upto):
    tick_full, _ = self.demo.at(upto)
    string_tables = self.keyframes[tick_full].string_tables
    snapshot = self.keyframes[tick_full].snapshot

    ticks = self.demo.within(tick_full, upto + 1)

    for tick in ticks:
      if tick in self._frame_cache:
        continue

      _, tick_norm = self.demo.at(tick)
      norm = self.demo.norm(tick_norm)
      self.stream.seek(norm.offset)

      pb_packet = demo_io.read(self.stream, norm)
      wrap = io.BufferedReader(io.BytesIO(pb_packet.data))
      messages = list(packet_io.scan(wrap))

      pb_st_updates = filter(test_update_st, messages)
      pb_pent = next((m for m in messages if test_packet_entities(m)), None)
      pb_voice_data = next((m for m in messages if test_voice_data(m)), None)

      if pb_st_updates:
        string_tables = copy.copy(string_tables)

        for st_update in pb_st_updates:
          pb_st_update = packet_io.read(wrap, st_update)

          st_name = string_tables.keys()[pb_st_update.table_id]
          st = string_tables[st_name]
          bs_wrap = bitstream_io.Bitstream.wrapping(pb_st_update.string_data)
          num_ent = pb_st_update.num_changed_entries

          for entry in d_string_table.decode(bs_wrap, st, num_ent):
            index, name, data = entry
            if name:
              string = string_table.String(name, data)
              st.items[name] = string
            else:
              string = st.items.values()[index]
              string.data = data

      # if pb_pent:
      #   io = io_b.Bitstream.wrapping(pb_pent.entity_data)
      #
      #   c, u, d = d_entity.read(
      #     io,
      #     pb_pent.updated_entries, pb_pent.is_delta,
      #     self.demo.class_bits, self.demo.class_info, self.demo.recv_tables,
      #     snapshot.entities
      #   )
      #
      #   print c, u, d

      self._frame_cache[tick] = Frame(tick, string_tables)

  def _frame_cache_empty(self):
    return len(self._frame_cache) == 0

  def _frame_cache_stale(self, tick):
    full1, _ = self.demo.at(tick)
    full2, _ = self.demo.at(tick - 1)
    return full1 != full2

  def _reset_frame_cache(self):
    self._frame_cache = collections.OrderedDict()

  # templates = dem.templates      # entity templates (via baseline)
  # for spec, delta in c.items():
  #   i, cls, serial = spec
  #   snapshot[i] = entity.Instance(i, templates[cls], delta=delta)
  # for i, delta in u.items():
  #   dt = snapshot[i].template.recv_table.dt
  #   snapshot[i].apply(delta)
  # for i in d:
  #   dt = snapshot[i].template.recv_table.dt
  #   del snapshot[i]
