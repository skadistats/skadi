from __future__ import absolute_import

import collections
import copy
import io
import sys

from skadi import io as skadi_io
from skadi.decoder import entity as d_entity
from skadi.decoder import prop as d_prop
from skadi.decoder import string_table as d_string_table
from skadi.index import demo as d_index
from skadi.index import packet as p_index
from skadi.io import bitstream as bitstream_io
from skadi.protoc import demo_pb2 as pb_d
from skadi.protoc import netmessages_pb2 as pb_n
from skadi.state import entity
from skadi.state import snapshot
from skadi.state import derive_templates, derive_entities


test_update_st = lambda m: m.cls is pb_n.CSVCMsg_UpdateStringTable
test_packet_entities = lambda m: m.cls is pb_n.CSVCMsg_PacketEntities
test_voice_data = lambda m: m.cls is pb_n.CSVCMsg_VoiceData


def pb_string_tables_find(pb_stt, name):
  gen = (pb_st for pb_st in pb_stt if pb_st.table_name == name)
  return next(gen, None)


def construct(meta, match_index, stream, tick=None):
  # index string tables, templates at each tick
  stt = collections.OrderedDict()
  tpl = collections.OrderedDict()

  string_tables = meta.string_tables
  templates = meta.templates

  for peek in match_index.find_all(pb_d.CDemoPacket):
    pbmsg = d_index.read(stream, peek)
    packet_stream = skadi_io.buffer(pbmsg.data)
    packet_index = p_index.construct(packet_stream)

    pb_st_updates = packet_index.find_all(pb_n.CSVCMsg_UpdateStringTable)
    if pb_st_updates:
      string_tables = copy.copy(string_tables)

      for _peek in pb_st_updates:
        pb_st_update = p_index.read(packet_stream, _peek)

        st_name = string_tables.keys()[pb_st_update.table_id]
        bs = bitstream_io.wrap(pb_st_update.string_data)
        st = string_tables[st_name]
        ne = pb_st_update.num_changed_entries

        for entry in d_string_table.decode(bs, st, ne):
          st = copy.copy(st)
          i, name, data = entry
          try:
            _name, _ = st.items[i]
            st.items[name] = (_name, data)
          except KeyError:
            st.items[name] = (name, data)

        if st.name == 'instancebaseline':
          templates = derive_templates(meta.recv_tables, st, templates)

    stt[peek.tick] = string_tables
    tpl[peek.tick] = templates

  return Replay(meta, match_index, stream, stt, tpl, tick=tick)


class Replay(object):
  def __init__(self, meta, match_index, stream, stt, tpl, tick=None):
    self.meta = meta
    self.match_index = match_index
    self.stream = stream
    self.stt_by_tick = stt
    self.tpl_by_tick = tpl
    self.tick = match_index.locate_tick(tick)
    self._full_snapshot = None
    self._snapshots = collections.OrderedDict()

  @property
  def snapshot(self):
    def snapshots_stale():
      prev_tick = self.match_index.locate_tick(self.tick - 1)
      current_full_packet = self.match_index.locate_full_tick(self.tick)
      earlier_full_packet = self.match_index.locate_full_tick(prev_tick)
      return current_full_packet != earlier_full_packet

    if not self._snapshots or snapshots_stale():
      self._full_snapshot = None
      self.full_snapshot
      self._snapshots = collections.OrderedDict()

    self._populate_snapshots()

    return self._snapshots[self.tick]

  @property
  def full_snapshot(self):
    if self._full_snapshot:
      return self._full_snapshot

    full_tick = self.match_index.locate_full_tick(self.tick)

    strtab = self.stt_by_tick[full_tick]
    templates = self.tpl_by_tick[full_tick]

    peek = self.match_index.lookup_full(full_tick)

    pb_full_p = d_index.read(self.stream, peek)
    packet_stream = skadi_io.buffer(pb_full_p.packet.data)
    packet_index = p_index.construct(packet_stream)

    peek = packet_index.find(pb_n.CSVCMsg_PacketEntities)
    pb_pent = p_index.read(packet_stream, peek)
    entcoll = collections.OrderedDict()
    entities = derive_entities(self.meta, pb_pent, templates, entcoll)

    s = snapshot.construct(strtab, templates, entities)
    self._full_snapshot = s
    return s

  def _populate_snapshots(self):
    string_tables, templates, entities = self._full_snapshot.unpack()

    full_tick = self.match_index.locate_full_tick(self.tick)
    entities = self.full_snapshot.entities

    for tick in self.match_index.locate_between(full_tick, self.tick):
      if tick in self._snapshots:
        entities = self._snapshots[tick].entities
        continue

      strtab = self.stt_by_tick[tick]
      templates = self.tpl_by_tick[tick]

      peek = self.match_index.lookup(tick)
      pb_packet = d_index.read(self.stream, peek)
      packet_stream = skadi_io.buffer(pb_packet.data)
      packet_index = p_index.construct(packet_stream)

      peek = packet_index.find(pb_n.CSVCMsg_PacketEntities)
      pb_pent = p_index.read(packet_stream, peek)
      entities = derive_entities(self.meta, pb_pent, templates, entities)

      s = snapshot.construct(strtab, templates, entities)
      self._snapshots[tick] = s
