from __future__ import absolute_import

import bitstring
import collections
import io
import math

from skadi.decoder import string_table as d_string_table
from skadi.io import bitstream as bitstream_io
from skadi.io.protobuf import demo as demo_io
from skadi.io.protobuf import packet as packet_io
from skadi.meta import class_info, game_event_list, string_table
from skadi.meta import misc
from skadi.meta import prop, recv_table, send_table
from skadi.protoc import demo_pb2 as pb_d
from skadi.protoc import netmessages_pb2 as pb_n
from skadi.state import derive_templates

DEMO_EXTRANEOUS = (pb_d.CDemoStringTables)

SVC_EXTRANEOUS = (
  pb_n.CNETMsg_SetConVar, pb_n.CNETMsg_SignonState, pb_n.CNETMsg_Tick,
  pb_n.CSVCMsg_ClassInfo
)

test_needs_decoder = lambda st: st.needs_decoder


def parse(stream):
  meta = {
    'string_tables': collections.OrderedDict(),
    'send_tables': collections.OrderedDict(),
    'recv_tables': collections.OrderedDict()
  }

  full_packets = collections.OrderedDict()
  packets = collections.OrderedDict()

  demo_scan = demo_io.scan(stream)

  for tick, peek in demo_scan:
    pbmsg = demo_io.read(stream, peek)

    if isinstance(pbmsg, pb_d.CDemoSyncTick):
      break
    elif isinstance(pbmsg, pb_d.CDemoClassInfo):
      meta['class_info'] = class_info.parse(pbmsg)
    elif isinstance(pbmsg, pb_d.CDemoFileHeader):
      meta['file_header'] = misc.parse(pbmsg, 'FileHeader')
    elif isinstance(pbmsg, pb_d.CDemoSendTables):
      wrap = io.BufferedReader(io.BytesIO(pbmsg.data))

      # parse send tables
      for _peek in packet_io.scan(wrap):
        _pbmsg = packet_io.read(wrap, _peek)
        st = send_table.parse(_pbmsg)
        meta['send_tables'][st.dt] = st

      # flatten send tables into recv tables
      for st in filter(test_needs_decoder, meta['send_tables'].values()):
        props = send_table.flatten(st, meta['send_tables'])
        meta['recv_tables'][st.dt] = recv_table.construct(st.dt, props)
    elif isinstance(pbmsg, pb_d.CDemoPacket):
      wrap = io.BufferedReader(io.BytesIO(pbmsg.data))

      for _peek in packet_io.scan(wrap):
        _pbmsg = packet_io.read(wrap, _peek)

        if isinstance(_pbmsg, pb_n.CSVCMsg_CreateStringTable):
          name, flags = _pbmsg.name, _pbmsg.flags
          me, ne = _pbmsg.max_entries, _pbmsg.num_entries
          udfs = _pbmsg.user_data_fixed_size
          uds, udsb = _pbmsg.user_data_size, _pbmsg.user_data_size_bits

          st = string_table.StringTable(name, me, ne, udfs, uds, udsb, flags)
          items = d_string_table.decode(bitstream_io.wrap(_pbmsg.string_data), st)

          for _, name, data in items:
            st.items[name] = string_table.String(name, data)

          meta['string_tables'][st.name] = st
        elif isinstance(_pbmsg, pb_n.CSVCMsg_GameEventList):
          meta['game_event_list'] = game_event_list.parse(_pbmsg)
        elif isinstance(_pbmsg, pb_n.CSVCMsg_ServerInfo):
          meta['server_info'] = misc.parse(_pbmsg, 'ServerInfo')
          class_bits = math.log(meta['server_info']['max_classes'], 2)
          meta['class_bits'] = int(math.ceil(class_bits))
        elif isinstance(_pbmsg, pb_n.CSVCMsg_VoiceInit):
          meta['voice_init'] = misc.parse(_pbmsg, 'VoiceInit')
        elif isinstance(_pbmsg, pb_n.CSVCMsg_SetView):
          meta['set_view'] = misc.parse(_pbmsg, 'SetView')
        elif not isinstance(_pbmsg, SVC_EXTRANEOUS):
          print "! ignoring: {0}".format(_pbmsg.__class__)
    elif not isinstance(pbmsg, DEMO_EXTRANEOUS):
      err = '! protobuf {0}: open issue at github.com/onethirtyfive/skadi'
      print err.format(pbmsg.__class__.__name__)

  ci, rt = meta['class_info'], meta['recv_tables']
  st_ib = meta['string_tables']['instancebaseline']
  templates = derive_templates(ci, rt, st_ib, collections.OrderedDict())
  meta['templates'] = templates

  for tick, peek in demo_scan:
    if peek.cls not in (pb_d.CDemoFullPacket, pb_d.CDemoPacket):
      break

    coll = full_packets if peek.cls is pb_d.CDemoFullPacket else packets
    coll[tick] = peek

  stream.seek(packets[0].offset)

  return Demo(meta, full_packets, packets)

class Demo(object):
  DELEGATED = (
    'game_event_list', 'file_header', 'recv_tables', 'set_view', 'voice_init',
    'server_info', 'class_info', 'string_tables', 'send_tables', 'class_bits',
    'templates'
  )

  def __init__(self, meta, full_packets, packets):
    self.meta = meta
    self.full_packets = collections.OrderedDict(full_packets.items())
    self.packets = collections.OrderedDict(packets.items())
    self._reversed_full_ticks = list(reversed(self.full_packets.keys()))
    self._reversed_ticks = list(reversed(self.packets.keys()))
    self._ticks = self.packets.keys()

  def full_tick(self, tick):
    return next(k for k in self._reversed_full_ticks if k <= tick)

  def tick(self, tick):
    return next(k for k in self._reversed_ticks if k <= tick)

  def at(self, tick):
    return self.full_tick(tick), self.tick(tick)

  def ticks_between(self, low, high):
    return [t for t in self._ticks if t >= low and t <= high]

  def __getattr__(self, attr):
    if attr in Demo.DELEGATED:
      return self.meta[attr]
    return getattr(super(Demo, self), attr)
