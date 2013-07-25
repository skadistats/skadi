import collections
import math
import re

from skadi.decoder import entity as d_entity
from skadi.decoder import prop as d_prop
from skadi.io import protobuf as io_p
from skadi.io import bitstream as io_b
from skadi.meta import class_info
from skadi.meta import game_event_list
from skadi.meta import misc
from skadi.meta import prop
from skadi.meta import recv_table
from skadi.meta import send_table
from skadi.meta import string_table
from skadi.protoc import demo_pb2 as pb_d
from skadi.protoc import netmessages_pb2 as pb_n
from skadi.snapshot import entity


DEMO_EXTRANEOUS = (pb_d.CDemoStringTables)
SVC_EXTRANEOUS = (
  pb_n.CNETMsg_SetConVar, pb_n.CNETMsg_SignonState, pb_n.CNETMsg_Tick,
  pb_n.CSVCMsg_ClassInfo
)


def decode(io):
  dem = Demo()

  # Process messages before CDemoSyncTick.
  for pbmsg in iter(io):
    if isinstance(pbmsg, pb_d.CDemoSyncTick):
      break
    elif isinstance(pbmsg, pb_d.CDemoClassInfo):
      dem.class_info = class_info.parse(pbmsg)
    elif isinstance(pbmsg, pb_d.CDemoFileHeader):
      dem.file_header = misc.parse(pbmsg, 'FileHeader')
    elif isinstance(pbmsg, pb_d.CDemoSendTables):
      packet_io = io_p.Packet.wrapping(pbmsg.data)
      send_tables = collections.OrderedDict()

      for _pbmsg in iter(packet_io):
        st = send_table.parse(_pbmsg)
        send_tables[st.dt] = st

      dem.send_tables = send_tables
      dem.flatten_send_tables()
    elif isinstance(pbmsg, pb_d.CDemoPacket):
      packet_io = io_p.Packet.wrapping(pbmsg.data)
      for _pbmsg in packet_io:
        if isinstance(_pbmsg, pb_n.CSVCMsg_CreateStringTable):
          st = string_table.parse(_pbmsg)
          dem.string_tables[st.name] = st
        elif isinstance(_pbmsg, pb_n.CSVCMsg_GameEventList):
          dem.game_event_list = game_event_list.parse(_pbmsg)
        elif isinstance(_pbmsg, pb_n.CSVCMsg_ServerInfo):
          dem.server_info = misc.parse(_pbmsg, 'ServerInfo')
        elif isinstance(_pbmsg, pb_n.CSVCMsg_VoiceInit):
          dem.voice_init = misc.parse(_pbmsg, 'VoiceInit')
        elif isinstance(_pbmsg, pb_n.CSVCMsg_SetView):
          dem.set_view = misc.parse(_pbmsg, 'SetView')
        elif not isinstance(_pbmsg, SVC_EXTRANEOUS):
          print "! ignoring: {0}".format(_pbmsg.__class__)
    elif not isinstance(pbmsg, DEMO_EXTRANEOUS):
      err = '! protobuf {0}: open issue at github.com/onethirtyfive/skadi'
      print err.format(pbmsg.__class__.__name__)

  # For array props, we need to associate the element property.
  for st in dem.send_tables.values():
    for i, p in enumerate(st.props):
      if p.type == prop.Type.Array:
        p.array_prop = st.props[i - 1]

  # Generate entity templates upon which instances will be based.
  dem.generate_entity_templates()
  dem.post_sync = io.tell()

  max_classes = dem.server_info['max_classes']
  dem.class_bits = int(math.ceil(math.log(max_classes, 2)))

  return dem


class Demo(object):
  def __init__(self):
    self.recv_tables = {}
    self.string_tables = collections.OrderedDict()

  def __repr__(self):
    lenst = len(self._send_tables)
    lenrt = len(self._recv_tables)
    return '<Demo ({0} send, {1} recv)>'.format(lenst, lenrt)

  def generate_entity_templates(self):
    ib_st = self.string_tables['instancebaseline']

    templates = {}
    for string in ib_st.items:
      io = io_b.Bitstream(string.data)
      cls = int(string.name)
      dt = self.class_info[cls].dt
      recv_table = self.recv_tables[dt]

      baseline = collections.OrderedDict()
      dp = d_entity.read_prop_list(io)
      for prop_index in dp:
        p = recv_table.props[prop_index]
        key = '{0}.{1}'.format(p.origin_dt, p.var_name)
        baseline[key] = d_prop.decode(io, p)

      templates[cls] = entity.Template(cls, recv_table, baseline)

    self.templates = templates

  def flatten_send_tables(self):
    test_needs_decoder = lambda st: st.needs_decoder
    recv_tables = {}
    for st in filter(test_needs_decoder, self.send_tables.values()):
      props = send_table.flatten(st, self.send_tables)
      recv_tables[st.dt] = recv_table.construct(st.dt, props)
    self.recv_tables = recv_tables
