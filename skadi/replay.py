from __future__ import absolute_import

import collections
import copy
import io
import sys

from skadi.decoder import entity as d_entity
from skadi.decoder import prop as d_prop
from skadi.decoder import string_table as d_string_table
from skadi.io import bitstream as bitstream_io
from skadi.io.protobuf import demo as demo_io
from skadi.io.protobuf import packet as packet_io
from skadi.meta import string_table
from skadi.protoc import netmessages_pb2 as pb_n
from skadi.state import entity
from skadi.state import snapshot
from skadi.state import derive_string_tables
from skadi.state import derive_templates, derive_entities


test_update_st = lambda m: m.cls is pb_n.CSVCMsg_UpdateStringTable
test_packet_entities = lambda m: m.cls is pb_n.CSVCMsg_PacketEntities
test_voice_data = lambda m: m.cls is pb_n.CSVCMsg_VoiceData


def construct(demo, stream):
  return Replay(demo, stream)


class Replay(object):
  def __init__(self, demo, stream, tick=0, full_snapshots=None):
    self.demo = demo
    self.stream = stream
    self.tick = tick
    self._full_snapshots = full_snapshots or collections.OrderedDict()
    self._snapshots = collections.OrderedDict()

  @property
  def snapshot(self):
    def snapshots_stale():
      current_full_packet = self.demo.full_tick(self.tick)
      earlier_full_packet = self.demo.full_tick(self.tick - 1)
      return current_full_packet != earlier_full_packet

    if not self._snapshots or snapshots_stale():
      self._snapshots = collections.OrderedDict()

    self._populate_snapshots()

    return self._snapshots[self.tick]

  @property
  def full_snapshot(self):
    if self.tick in self._full_snapshots:
      return self._full_snapshots[self.tick]

    full_tick = self.demo.full_tick(self.tick)

    peek = self.demo.full_packets[full_tick]
    self.stream.seek(peek.offset)
    pb_full_p = demo_io.read(self.stream, peek)
    pb_packet = pb_full_p.packet
    packet_stream = packet_io.wrap(pb_packet.data)
    messages = list(packet_io.scan(packet_stream))

    peek = next((m for m in messages if test_packet_entities(m)), None)
    pb_pent = packet_io.read(packet_stream, peek)

    pb_stt, stt = pb_full_p.string_table, self.demo.string_tables
    stt = derive_string_tables(pb_stt, stt)
    templates = copy.copy(self.demo.templates)

    ci, rt = self.demo.class_info, self.demo.recv_tables
    tt = derive_templates(ci, rt, stt['instancebaseline'], templates)
    ee = derive_entities(self.demo, pb_pent, tt, collections.OrderedDict())

    s = snapshot.construct(stt, tt, ee)
    self._full_snapshots[self.tick] = s
    return s

  def _populate_snapshots(self):
    string_tables, templates, entities = self.full_snapshot.unpack()

    full_tick = self.demo.full_tick(self.tick)

    for tick in self.demo.ticks_between(full_tick, self.tick):
      if tick in self._snapshots:
        continue

      peek = self.demo.packets[tick]
      self.stream.seek(peek.offset)

      pb_packet = demo_io.read(self.stream, peek)
      packet_stream = packet_io.wrap(pb_packet.data)
      messages = list(packet_io.scan(packet_stream))

      pb_st_updates = filter(test_update_st, messages)
      if pb_st_updates:
        string_tables = copy.copy(string_tables)

        for peek in pb_st_updates:
          pb_st_update = packet_io.read(packet_stream, peek)

          st_name = string_tables.keys()[pb_st_update.table_id]
          st = string_tables[st_name]
          bs_wrap = bitstream_io.wrap(pb_st_update.string_data)
          num_ent = pb_st_update.num_changed_entries

          for entry in d_string_table.decode(bs_wrap, st, num_ent):
            index, name, data = entry
            if name:
              string = string_table.String(name, data)
              st.items[name] = string
            else:
              string = st.items.values()[index]
              string.data = data

          if st_name == 'instancebaseline':
            st_ib = string_tables['instancebaseline']
            ci, rt = self.demo.class_info, self.demo.recv_tables
            templates = derive_templates(ci, rt, st_ib, templates)

      peek = next((m for m in messages if test_packet_entities(m)), None)
      pb_pent = packet_io.read(packet_stream, peek)
      if pb_pent:
        entities = derive_entities(self.demo, pb_pent, templates, entities)

      s = snapshot.construct(string_tables, templates, entities)
      self._snapshots[tick] = s
