from __future__ import absolute_import

import collections
import io
import itertools
import math
import re

from skadi.generated import demo_pb2 as pb_d
from skadi.generated import netmessages_pb2 as pb_n
from skadi.io import bitstream as io_bs
from skadi.io import entity as io_en
from skadi.io import property as io_pr
from skadi.io import protobuf as io_pb

from skadi.state import class_info as ci
from skadi.state import dt
from skadi.state import entity as ent
from skadi.state import game_event as ge
from skadi.state import string_table as st

class Snapshot(object):
  def __init__(self):
    self.instances = {}

DEMO_PRESYNC = (
  pb_d.CDemoFileHeader, pb_d.CDemoSendTables, pb_d.CDemoClassInfo,
  pb_d.CDemoStringTables
)

SVC_RELEVANT = (
  pb_n.CSVCMsg_ServerInfo, pb_n.CSVCMsg_VoiceInit, pb_n.CSVCMsg_GameEventList,
  pb_n.CSVCMsg_SetView
)

def underscore(_str):
  s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', _str)
  return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()

class Flattener(object):
  def __init__(self, demo):
    self.demo = demo

  def flatten(self, st):
    props = self._build(st, [], self._aggregate_exclusions(st))
    return dt.RecvTable.construct(st.dt, props)

  def _build(self, st, onto, excl):
    non_dt_props = self._compile(st, onto, excl)

    for prop in non_dt_props:
      onto.append(prop)

    return onto

  def _compile(self, st, onto, excl, collapsed=None):
    collapsed = collapsed or []

    def test_excluded(prop):
      return (st.dt, prop.var_name) not in excl

    for prop in st.dt_props:
      if dt.test_data_table(prop) and test_excluded(prop):
        _st = self.demo.send_tables[prop.dt_name]
        if dt.test_collapsible(prop):
          collapsed += self._compile(_st, onto, excl, collapsed)
        else:
          self._build(_st, onto, excl)

    return collapsed + filter(test_excluded, st.non_dt_props)

  def _aggregate_exclusions(self, st):
    def recurse(_dt_prop):
      st = self.demo.send_tables[_dt_prop.dt_name]
      return self._aggregate_exclusions(st)

    inherited = map(recurse, st.dt_props)

    return st.exclusions + list(itertools.chain(*inherited))

class Demo(object):
  @classmethod
  def build(cls, demo_io):
    dem = cls()

    # Process messages before CDemoSyncTick.
    for pbmsg in iter(demo_io):
      if isinstance(pbmsg, pb_d.CDemoSyncTick):
        break
      elif isinstance(pbmsg, pb_d.CDemoPacket):
        packet_io = io_pb.PacketIO.wrapping(pbmsg.data)
        for _pbmsg in packet_io:
          match = re.match(r'C(SVC|NET)Msg_(.*)$', _pbmsg.__class__.__name__)
          attr = underscore(match.group(2))
          if isinstance(_pbmsg, SVC_RELEVANT):
            setattr(dem, attr, _pbmsg)
      elif isinstance(pbmsg, DEMO_PRESYNC):
        matches = re.match(r'CDemo(.*)$', pbmsg.__class__.__name__)
        attr = underscore(matches.group(1))
        setattr(dem, attr, pbmsg)
      else:
        err = '! io_pb {0}: open an issue at github.com/onethirtyfive/skadi'
        print err.format(pbmsg.__class__.__name__)

    # For array props, we need to associate the element property.
    for send_table in dem.send_tables.values():
      for i, prop in enumerate(send_table.props):
        if prop.type == dt.Type.Array:
          prop.array_prop = send_table.props[i - 1]

    # Flatten 'send tables' into 'receive tables' of communicable prop specs.
    dem.flatten_send_tables()

    # Parse remainder of demo for a chronology of CDemoFullPacket.
    max_classes = dem.server_info['max_classes']
    dem.class_bits = int(math.ceil(math.log(max_classes, 2)))
    dem.chronology = demo_io.chronologize()

    # Generate entity templates upon which instances will be based.
    dem.generate_entity_templates()

    return dem

  def __init__(self):
    self._file_header = None
    self._server_info = None
    self._voice_init = None
    self._game_event_list = None
    self._set_view = None
    self._class_info = None
    self._string_tables = None
    self._send_tables = None
    self._recv_tables = None

  def __repr__(self):
    lenst = len(self._send_tables)
    lenrt = len(self._recv_tables)
    return '<Demo ({0} send, {1} recv)>'.format(lenst, lenrt)

  @property
  def file_header(self):
    return self._file_header

  @file_header.setter
  def file_header(self, pbmsg):
    file_header = {}
    to_extract = (
      'demo_file_stamp', 'network_protocol', 'server_name', 'client_name',
      'map_name', 'game_directory', 'fullpackets_version'
    )
    for attr in to_extract:
      file_header[attr] = getattr(pbmsg, attr)
    self._file_header = file_header

  @property
  def server_info(self):
    return self._server_info

  @server_info.setter
  def server_info(self, pbmsg):
    to_extract = (
      'protocol', 'server_count', 'is_dedicated', 'is_hltv',
      'c_os', 'map_crc', 'client_crc', 'string_table_crc',
      'max_clients', 'max_classes', 'player_slot',
      'tick_interval', 'game_dir', 'map_name', 'sky_name',
      'host_name'
    )
    self._server_info = {v:getattr(pbmsg,v) for v in to_extract}

  @property
  def voice_init(self):
    return self._voice_init

  @voice_init.setter
  def voice_init(self, pbmsg):
    to_extract = ('quality', 'codec')
    self._voice_init = {v:getattr(pbmsg,v) for v in to_extract}

  @property
  def game_event_list(self):
    return self._game_event_list

  @game_event_list.setter
  def game_event_list(self, pbmsg):
    game_event_list = {}
    for desc in pbmsg.descriptors:
      _id, name = desc.eventid, desc.name
      keys = [(k.type, k.name) for k in desc.keys]
      game_event_list[_id] = ge.GameEvent(_id, name, keys)
    self._game_event_list = game_event_list

  @property
  def send_tables(self):
    return self._send_tables

  @send_tables.setter
  def send_tables(self, pbmsg):
    packet_io = io_pb.PacketIO.wrapping(pbmsg.data)
    send_tables = {}
    for svc_message in iter(packet_io):
      st = dt.SendTable.construct(svc_message)
      send_tables[st.dt] = st
    self._send_tables = send_tables

  @property
  def recv_tables(self):
    return self._recv_tables

  @property
  def class_info(self):
    return self._class_info

  @class_info.setter
  def class_info(self, pbmsg):
    class_info = {}
    for c in pbmsg.classes:
      _id, dt, name = c.class_id, c.table_name, c.network_name
      class_info[c.class_id] = ci.Class(_id, name, dt)
    self._class_info = class_info

  @property
  def string_tables(self):
    return self._string_tables

  @string_tables.setter
  def string_tables(self, pbmsg):
    string_tables = {}
    for t in pbmsg.tables:
      _ii, _iic = [], []
      for i in t.items:
        _ii.append(st.String(i.str, i.data))
      for i in t.items_clientside:
        _iic.append(st.String(i.str, i.data))
      name, flags = t.table_name, t.table_flags
      string_tables[name] = st.StringTable(name, flags, _ii, _iic)
    self._string_tables = string_tables

  def flatten_send_tables(self):
    test_needs_decoder = lambda st: st.needs_decoder
    recv_tables = {}
    for st in filter(test_needs_decoder, self.send_tables.values()):
      recv_tables[st.dt] = Flattener(self).flatten(st)
    self._recv_tables = recv_tables

  def generate_entity_templates(self):
    ib_st = self.string_tables['instancebaseline']

    templates = {}
    for string in ib_st.items:
      cls = int(string.name)
      bs_io = io_bs.BitstreamIO(string.data)
      dp = io_en.PropListReader(bs_io).read()
      recv_table = self.recv_tables[self.class_info[cls].dt]

      baseline = collections.OrderedDict()
      for prop_index in dp:
        prop = recv_table.props[prop_index]
        baseline[prop.var_name] = io_pr.Reader.read(prop, bs_io)

      templates[cls] = ent.Template(cls, recv_table, baseline)

    self.templates = templates
