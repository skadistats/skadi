from __future__ import absolute_import

import collections as c
import io
import itertools

from skadi import enum
from skadi.io import protobuf

Flag = enum(
  UNSIGNED                 = 1 <<  0, COORD                     = 1 <<  1,
  NO_SCALE                 = 1 <<  2, ROUND_DOWN                = 1 <<  3,
  ROUND_UP                 = 1 <<  4, NORMAL                    = 1 <<  5,
  EXCLUDE                  = 1 <<  6, XYZE                      = 1 <<  7,
  INSIDE_ARRAY             = 1 <<  8, PROXY_ALWAYS              = 1 <<  9,
  VECTOR_ELEM              = 1 << 10, COLLAPSIBLE               = 1 << 11,
  COORD_MP                 = 1 << 12, COORD_MP_LOW_PRECISION    = 1 << 13,
  COORD_MP_INTEGRAL        = 1 << 14, CELL_COORD                = 1 << 15,
  CELL_COORD_LOW_PRECISION = 1 << 16, CELL_COORD_INTEGRAL       = 1 << 17,
  CHANGES_OFTEN            = 1 << 18, ENCODED_AGAINST_TICKCOUNT = 1 << 19
)

Type = enum(
  INT        = 0, FLOAT  = 1, VECTOR = 2,
  VECTOR_XY  = 3, STRING = 4, ARRAY  = 5,
  DATA_TABLE = 6, INT64  = 7
)

class Prop(object):
  DELEGATED = (
    'var_name', 'type',    'flags',   'num_elements',
    'num_bits', 'dt_name', 'priority'
  )

  def __init__(self, origin_dt, attributes):
    self.origin_dt = origin_dt
    self._attributes = attributes

  def __getattribute__(self, name):
    if name in Prop.DELEGATED:
      return self._attributes[name]
    else:
      return object.__getattribute__(self, name)

  def __repr__(self):
    odt, vn, t = self.origin_dt, self.var_name, self._type()
    f = ','.join(self._flags()) if self.flags else '-'
    p = self.priority if self.priority < 128 else 128
    terse = ('num_bits', 'num_elements', 'dt_name')
    b, e, dt = map(lambda i: getattr(self, i) or '-', terse)

    _repr = "<Prop {0}.{1} t:{2} f:{3} p:{4} b:{5} e:{6} o:{7}>"
    return _repr.format(odt, vn, t, f, p, b, e, dt)

  def _type(self):
    for k, v in Type._enums.items():
      if self.type == v:
          return k.lower()

  def _flags(self):
    named_flags = []
    for k, v in Flag._enums.items():
      if self.flags & v:
        named_flags.append(k.lower())
    return named_flags

class Table(object):
  def __init__(self, dt, props):
    self.dt = dt
    self.props = list(props)

  def __repr__(self):
    cls = self.__class__.__name__
    lenprops = len(self.props)
    return '<{0} {1} ({2} props)>'.format(cls, self.dt, lenprops)

test_exclude = lambda prop: prop.flags & Flag.EXCLUDE
test_not_exclude = lambda prop: prop.flags ^ Flag.EXCLUDE
test_inside_array = lambda prop: prop.flags & Flag.INSIDE_ARRAY
test_data_table = lambda prop: prop.type == Type.DATA_TABLE
test_baseclass = lambda prop: prop.name == 'baseclass'

class SendTable(Table):
  @classmethod
  def construct(cls, message):
    dt, props = message.net_table_name, []

    for prop in message.props:
      attributes = {
        'var_name': prop.var_name,
        'type': prop.type,
        'flags': prop.flags,
        'num_elements': prop.num_elements,
        'num_bits': prop.num_bits,
        'dt_name': prop.dt_name,
        'priority': prop.priority
      }
      props.append(Prop(dt, attributes))

    return SendTable(dt, props, message.is_end, message.needs_decoder)

  def __init__(self, dt, props, is_end, needs_decoder):
    super(SendTable, self).__init__(dt, props)
    self.is_end = is_end
    self.needs_decoder = needs_decoder

  @property
  def baseclass(self):
    prop = next((prop for prop in self.filter(test_baseclass)), None)
    return prop.dt if prop else None

  @property
  def exclusions(self):
    def describe_exclusion(prop):
      return (prop.dt_name, prop.var_name)
    return map(describe_exclusion, filter(test_exclude, self.props))

  @property
  def non_exclusion_props(self):
    return filter(test_not_exclude, self.props)

  @property
  def dt_props(self):
    return filter(test_data_table, self.non_exclusion_props)

  @property
  def non_dt_props(self):
    def test_eligible(prop):
      return not test_data_table(prop) and not test_inside_array(prop)
    return filter(test_eligible, self.non_exclusion_props)

test_collapsible = lambda prop: prop.flags & Flag.COLLAPSIBLE

class Flattener(object):
  def __init__(self, demo):
    self.demo = demo

  def flatten(self, st):
    props = self._build(st, [], self._aggregate_exclusions(st))
    return RecvTable.construct(st.dt, props)

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
      if test_data_table(prop) and test_excluded(prop):
        _st = self.demo.send_tables[prop.dt_name]
        if test_collapsible(prop):
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

class RecvTable(Table):
  @classmethod
  def construct(cls, dt, props):
    rt = RecvTable(dt, props)
    priorities = [64]

    for prop in rt.props:
      gen = (pr for pr in priorities if pr == prop.priority)
      if not next(gen, None):
        priorities.append(prop.priority)

    priorities, prop_offset = sorted(priorities), 0

    for pr in priorities:
      proplen = len(rt.props)
      hole = prop_offset
      cursor = prop_offset

      while cursor < proplen:
        prop = rt.props[cursor]
        is_co_prop = (pr == 64 and (prop.flags & Flag.CHANGES_OFTEN))

        if is_co_prop or prop.priority == pr:
          rt = rt.swap(rt.props[hole], prop)
          hole += 1
          prop_offset += 1
        cursor += 1

    return rt

  def swap(self, first, second):
    l = list(self.props)
    i = l.index(first)
    j = l.index(second)
    l[i], l[j] = l[j], l[i]
    return RecvTable(self.dt, l)

class GameEvent(object):
  def __init__(self, _id, name, keys):
    self.id = _id
    self.name = name
    self.keys = keys

  def __repr__(self):
    _id, n= self.id, self.name
    lenkeys = len(self.keys)
    return "<GameEvent {0} '{1}' ({2} keys)>".format(_id, n, lenkeys)

class Class(object):
  def __init__(self, _id, name, dt):
    self.id = _id
    self.dt = dt
    self.name = name

  def __repr__(self):
    _id = self.id
    dtn = self.dt
    name = self.name
    return "<Class {0} '{1}' ({2})>".format(_id, name, dtn)

class StringTable(object):
  def __init__(self, name, flags, items, items_clientside):
    self.name = name
    self.items = items
    self.items_clientside = items_clientside
    self.flags = flags

  def __repr__(self):
    n, f = self.name, hex(int(self.flags))
    lenitems = len(self.items)
    lenitemsc = len(self.items_clientside)
    _repr = "<StringTable '{0}' f:{1} ({2} items, {3} items clientside)"
    return _repr.format(n, f, lenitems, lenitemsc)

class String(object):
  def __init__(self, name, data):
    self.name = name
    self.data = data

  def __repr__(self):
    n, d = self.name, self.data
    return "<String '{0}' ({1} bytes)>".format(n, d)

class Demo(object):
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
    self._server_info = {(v,getattr(pbmsg,v)) for v in to_extract}

  @property
  def voice_init(self):
    return self._voice_init

  @voice_init.setter
  def voice_init(self, pbmsg):
    to_extract = ('quality', 'codec')
    self._voice_init = {(v,getattr(pbmsg,v)) for v in to_extract}

  @property
  def game_event_list(self):
    return self._game_event_list

  @game_event_list.setter
  def game_event_list(self, pbmsg):
    game_event_list = {}
    for desc in pbmsg.descriptors:
      _id, name = desc.eventid, desc.name
      keys = [(k.type, k.name) for k in desc.keys]
      game_event_list[_id] = GameEvent(_id, name, keys)
    self._game_event_list = game_event_list

  @property
  def send_tables(self):
    return self._send_tables

  @send_tables.setter
  def send_tables(self, pbmsg):
    packet_io = protobuf.PacketIO.wrapping(pbmsg.data)
    send_tables = {}
    for svc_message in iter(packet_io):
      st = SendTable.construct(svc_message)
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
      class_info[c.class_id] = Class(_id, name, dt)
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
        _ii.append(String(i.str, i.data))
      for i in t.items_clientside:
        _iic.append(String(i.str, i.data))
      name, flags = t.table_name, t.table_flags
      string_tables[name] = StringTable(name, flags, _ii, _iic)
    self._string_tables = string_tables

  def flatten_send_tables(self):
    test_needs_decoder = lambda st: st.needs_decoder
    recv_tables = {}
    for st in filter(test_needs_decoder, self.send_tables.values()):
      recv_tables[st.dt] = Flattener(self).flatten(st)
    self._recv_tables = recv_tables