import copy

from skadi.engine import *
from skadi.engine import world as w
from skadi.engine.unpacker import entity as uent
from skadi.engine.unpacker.entity import PVS
from skadi.index import demo as di
from skadi.protoc import netmessages_pb2 as pb_n
from skadi.replay import stream


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

    self.class_bits = bitlength(self.server_info['max_classes'])

  def stream(self, tick=0):
    match = self.index.match
    cb, rt = self.class_bits, self.recv_tables
    st = copy.deepcopy(self.string_tables)
    st_ib = st['instancebaseline']

    full_packet_peeks = \
      filter(lambda peek: peek.tick <= tick, match.full_packet_peeks)

    for peek in full_packet_peeks:
      full_packet = di.read(self.io, peek)

      for table in full_packet.string_table.tables:
        assert not table.items_clientside

        entries = [(i, e.str, e.data) for i, e in enumerate(table.items)]
        st[table.table_name].update_all(entries)

    full_packet = di.read(self.io, full_packet_peeks[-1])
    p_io = io.BufferedReader(io.BytesIO(full_packet.packet.data))
    index = pi.index(p_io)

    csvc_packet_entities = \
      pi.read(p_io, index.find(pb_n.CSVCMsg_PacketEntities))

    world = w.construct(rt)

    bitstream = bs.construct(csvc_packet_entities.entity_data)
    ct = csvc_packet_entities.updated_entries
    unpacker = uent.unpack(bitstream, -1, ct, False, cb, world)

    for index, mode, (cls, serial, diff) in unpacker:
      bitstream = bs.construct(st['instancebaseline'].get(cls)[1])
      unpacker = uent.unpack(bitstream, -1, 1, False, cb, world)
      state = dict(unpacker.unpack_baseline(rt[cls]))
      state.update(diff)

      try:
        world.create(cls, index, serial, state)
      except AssertionError, e:
        print e

    return stream.construct(self.io, match, tick, cb, rt, st, world)
