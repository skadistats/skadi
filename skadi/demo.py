import collections
import copy
import math

from skadi.engine import *
from skadi.engine import bitstream as bs
from skadi.engine.unpacker import entity as uent
from skadi.engine.unpacker import string_table as ust
from skadi.index import demo as di
from skadi.index import packet as pi
from skadi.protoc import demo_pb2 as pb_d
from skadi.protoc import netmessages_pb2 as pb_n


HEADER = "PBUFDEM\0"


class InvalidDemo(RuntimeError):
  pass


def construct(io):
  io.seek(0)

  if io.read(len(HEADER)) != HEADER:
    raise InvalidDemo('malformed header')

  io.read(4) # game summary offset in file in bytes

  demo = Demo(io, di.index(io))
  demo.bootstrap()

  return demo


class StreamComplete(RuntimeError):
  pass


class Stream(object):
  def __init__(self, io, index, tick, cb, rt, string_tables, entities):
    self.io = io
    self.index = index
    self.tick = tick
    self.class_bits = cb
    self.recv_tables = rt
    self.string_tables = copy.deepcopy(string_tables)
    self.entities = copy.deepcopy(entities)

  def __iter__(self):
    def _apply():
      peek = next(self.peeks)
      return self.apply(peek)

    return iter(_apply, None)

  def bootstrap(self):
    full_packet_tick = self.index.locate_full_tick(self.tick)
    peeks = self.index.lookup_between(full_packet_tick, self.index.ticks[-1])

    for peek in peeks:
      self.apply(peek)
      if self.tick == peek.tick:
        break

    self.peeks = peeks # use the generator from here on out

  def apply(self, peek):
    self.tick = peek.tick

    packet = di.read(self.io, peek)
    p_io = io.BufferedReader(io.BytesIO(packet.data))
    index = pi.index(p_io)

    csvc_update_string_table_peeks = \
      index.find_all(pb_n.CSVCMsg_UpdateStringTable)
    all_csvc_update_string_table = \
      [pi.read(p_io, p) for p in csvc_update_string_table_peeks]

    for pbmsg in all_csvc_update_string_table:
      key = self.string_tables.keys()[pbmsg.table_id]
      dest = self.string_tables[key]
      ne = pbmsg.num_changed_entries
      eb = dest['entry_bits']
      udfs = dest['user_data_fixed_size']
      udbs = dest['user_data_size_bits']

      bitstream = bs.construct(pbmsg.string_data)
      unpacked = list(ust.Unpacker(bitstream, ne, eb, udfs, udbs))

      for i, n, d in unpacked:
        if n:
          dest['by_name'][n] = (i, d)
          dest['by_index'][i] = (n, d)
        else:
          name, _ = dest['by_index'][i]
          dest['by_name'][n] = (i, d)
          dest['by_index'][i] = (n, d)

    csvc_packet_entities = \
      pi.read(p_io, index.find(pb_n.CSVCMsg_PacketEntities))

    bitstream = bs.construct(csvc_packet_entities.entity_data)
    ct = csvc_packet_entities.updated_entries
    cb, rt = self.class_bits, self.recv_tables

    unpacker = uent.Unpacker(bitstream, -1, ct, False, cb, rt, self.entities)
    unpacked = list(unpacker)

    baselines = self.string_tables['instancebaseline']

    for mode, index, context in unpacked:
      if mode & uent.PVS.Entering:
        cls, serial, diff = context

        bitstream = bs.construct(baselines['by_name'][cls][1]) # baseline data
        _unpacker = uent.Unpacker(bitstream, -1, 1, False, cb, rt, {})

        state = _unpacker.unpack_baseline(self.recv_tables[cls])
        state.update(diff)

        self.entities[index] = (cls, serial, state)
      elif mode & uent.PVS.Deleting:
        try:
          del self.entities[index]
        except KeyError, e:
          pass
      elif mode ^ uent.PVS.Leaving:
        # otherwise, we're "preserving" (aka "updating") the entity
        entity = self.entities[index]

        cls, serial, state = self.entities[index]
        state.update(context)

        self.entities[index] = (cls, serial, state)

    return peek.tick, self.string_tables, self.entities


class Demo(object):
  def __init__(self, io, index):
    self.io = io
    self.index = index
 
  def bootstrap(self):
    prologue_index = self.index.prologue

    cdemo_file_header = di.read(self.io, prologue_index.file_header_peek)
    self.file_header = parse_cdemo_file_header(cdemo_file_header)

    cdemo_class_info = di.read(self.io, prologue_index.class_info_peek)
    self.class_info = parse_cdemo_class_info(cdemo_class_info)

    cdemo_send_tables = di.read(self.io, prologue_index.send_tables_peek)
    self.send_tables = parse_cdemo_send_tables(cdemo_send_tables)
    self.recv_tables = flatten(self.class_info, self.send_tables)

    # for prologue packets, concat and index their data for easy access
    prologue_cdemo_packets = \
      [di.read(self.io, p) for p in prologue_index.packet_peeks]

    cdemo_packet_data = ''.join([cdp.data for cdp in prologue_cdemo_packets])
    p_io = io.BufferedReader(io.BytesIO(cdemo_packet_data))
    packet_index = pi.index(p_io)

    csvc_create_string_table_peeks = \
      packet_index.find_all(pb_n.CSVCMsg_CreateStringTable)
    all_csvc_create_string_table = \
      [pi.read(p_io, peek) for peek in csvc_create_string_table_peeks]
    self.string_tables = \
      parse_all_csvc_create_string_table(all_csvc_create_string_table)

    csvc_voice_init = pi.read(p_io, packet_index.find(pb_n.CSVCMsg_VoiceInit))
    self.voice_init = parse_csvc_voice_init(csvc_voice_init)

    csvc_server_info = \
      pi.read(p_io, packet_index.find(pb_n.CSVCMsg_ServerInfo))
    self.server_info = parse_csvc_server_info(csvc_server_info)

    csvc_game_event_list = \
      pi.read(p_io, packet_index.find(pb_n.CSVCMsg_GameEventList))
    self.game_event_list = parse_csvc_game_event_list(csvc_game_event_list)

    max_classes = self.server_info['max_classes']
    self.class_bits = int(math.ceil(math.log(max_classes, 2)))

  def stream(self, tick=0):
    match = self.index.match
    state = filter(lambda peek: peek.tick <= tick, match.full_packet_peeks)

    string_tables = copy.deepcopy(self.string_tables)
    entities = collections.OrderedDict()

    for peek in state:
      full_packet = di.read(self.io, peek)
      string_table_updates = full_packet.string_table.tables

      for table in string_table_updates:
        assert not table.items_clientside # unsupported, not used

        pick = table.table_name
        entries = [(i, _i.str, _i.data) for i, _i in enumerate(table.items)]

        mapped = map(lambda (i,n,d): (i,(n,d)), entries)
        string_tables[pick]['by_index'] = collections.OrderedDict(mapped)

        mapped = map(lambda (i,n,d): (n,(i,d)), entries)
        string_tables[pick]['by_name'] = collections.OrderedDict(mapped)

    entities = collections.OrderedDict()
    cb, rt = self.class_bits, self.recv_tables

    full_packet = di.read(self.io, state[-1])
    p_io = io.BufferedReader(io.BytesIO(full_packet.packet.data))
    index = pi.index(p_io)

    csvc_packet_entities = \
      pi.read(p_io, index.find(pb_n.CSVCMsg_PacketEntities))

    bitstream = bs.construct(csvc_packet_entities.entity_data)
    ct = csvc_packet_entities.updated_entries

    unpacker = uent.Unpacker(bitstream, -1, ct, False, cb, rt, {})
    baselines = string_tables['instancebaseline']

    for mode, index, context in list(unpacker):
      if mode ^ uent.PVS.Entering:
        continue

      cls, serial, diff = context
      bitstream = bs.construct(baselines['by_name'][cls][1]) # baseline data
      _unpacker = uent.Unpacker(bitstream, -1, 1, False, cb, rt, {})

      state = _unpacker.unpack_baseline(self.recv_tables[cls])
      state.update(diff)

      entities[index] = (cls, serial, state)

    stream = Stream(self.io, match, tick, cb, rt, string_tables, entities)
    stream.bootstrap()

    return stream