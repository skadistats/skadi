from __future__ import absolute_import

import collections
import itertools

from skadi.domain import class_info as d_ci
from skadi.domain import dt as d_dt
from skadi.domain import entity as d_ent
from skadi.domain import game_event as d_ge
from skadi.domain import string_table as d_st
from skadi.io import bitstream as io_b
from skadi.io import protobuf as io_p
from skadi.reader import entity as r_ent

class Flattener(object):
  def __init__(self, demo):
    self.demo = demo

  def flatten(self, st):
    props = self._build(st, [], self._aggregate_exclusions(st))
    return d_dt.RecvTable.construct(st.dt, props)

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
      if d_dt.test_data_table(prop) and test_excluded(prop):
        _st = self.demo.send_tables[prop.dt_name]
        if d_dt.test_collapsible(prop):
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
  def __init__(self):
    self._file_header = None
    self._server_info = None
    self._voice_init = None
    self._game_event_list = None
    self._set_view = None
    self._class_info = None
    self._send_tables = None
    self._recv_tables = None
    self.string_tables = collections.OrderedDict()

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
      game_event_list[_id] = d_ge.GameEvent(_id, name, keys)
    self._game_event_list = game_event_list

  @property
  def send_tables(self):
    return self._send_tables

  @send_tables.setter
  def send_tables(self, pbmsg):
    packet_io = io_p.Packet.wrapping(pbmsg.data)
    send_tables = {}
    for svc_message in iter(packet_io):
      st = d_dt.SendTable.construct(svc_message)
      send_tables[st.dt] = st
    self._send_tables = send_tables
    self._flatten_send_tables()

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
      class_info[c.class_id] = d_ci.Class(_id, name, dt)
    self._class_info = class_info

  def generate_entity_templates(self):
    ib_st = self.string_tables['instancebaseline']

    templates = {}
    for string in ib_st.items:
      io = io_b.Bitstream(string.data)
      cls = int(string.name)
      dt = self.class_info[cls].dt
      recv_table = self.recv_tables[dt]

      baseline = collections.OrderedDict()
      dp = r_ent.read_prop_list(io)
      for prop_index in dp:
        prop = recv_table.props[prop_index]
        key = '{0}.{1}'.format(prop.origin_dt, prop.var_name)
        baseline[key] = r_ent.read_prop(io, prop)

      templates[cls] = d_ent.Template(cls, recv_table, baseline)

    self.templates = templates

  def _flatten_send_tables(self):
    test_needs_decoder = lambda st: st.needs_decoder
    recv_tables = {}
    for st in filter(test_needs_decoder, self.send_tables.values()):
      recv_tables[st.dt] = Flattener(self).flatten(st)
    self._recv_tables = recv_tables
