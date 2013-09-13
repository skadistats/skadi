from __future__ import absolute_import

import collections as c
import copy
import io as _io
import itertools as it
import math


def enum(**enums):
  _enum = type('Enum', (), enums)
  _enum.tuples = enums
  return _enum

Peek = c.namedtuple('Peek', 'tick, kind, tell, size, compressed')


from skadi import *
from skadi.engine import string_table as stab
from skadi.engine.dt import prop as dt_p
from skadi.engine.dt import recv as dt_r
from skadi.engine.dt import send as dt_s
from skadi.index.demo import prologue as id_prologue
from skadi.index.embed import packet as ie_packet
from skadi.index.embed import send_tables as ie_send_tables
from skadi.io.protobuf import demo as d_io
from skadi.io.protobuf import packet as p_io
from skadi.io.unpacker import string_table as u_st
from skadi.protoc import demo_pb2 as pb_d
from skadi.protoc import netmessages_pb2 as pb_n
try:
  from skadi.io import cBitstream as b_io
except ImportError:
  from skadi.io import bitstream as b_io

Meta = c.namedtuple('Meta', ['file_header', 'server_info', 'voice_init'])

FileHeader = c.namedtuple('FileHeader', [
  'demo_file_stamp', 'network_protocol', 'server_name', 'client_name',
  'map_name', 'game_directory', 'fullpackets_version'
])

ServerInfo = c.namedtuple('ServerInfo', [
  'protocol', 'server_count', 'is_dedicated', 'is_hltv', 'c_os', 'map_crc',
  'client_crc', 'string_table_crc', 'max_clients', 'max_classes',
  'player_slot', 'tick_interval', 'game_dir', 'map_name', 'sky_name',
  'host_name'
])

VoiceInit = c.namedtuple('VoiceInit', ['quality', 'codec'])

Prologue = c.namedtuple('Prologue', [
  'meta', 'recv_tables', 'string_tables', 'game_event_list', 'class_bits'
])

test_needs_decoder = lambda st: st.needs_decoder


class InvalidDemo(RuntimeError):
  pass


def load(io, tick=0):
  demo_io = d_io.construct(io)
  prologue = id_prologue.construct(demo_io)

  # mash all packet svc messages together, then index them
  signon_packets = list(prologue.all_dem_signon_packet)
  data = ''.join([pb.data for _, pb in signon_packets])
  packet = ie_packet.construct(p_io.construct(data))

  # meta: file header
  _, pbmsg = prologue.dem_file_header
  file_header = FileHeader(*[getattr(pbmsg, a) for a in FileHeader._fields])

  # meta: server info
  _, pbmsg = packet.svc_server_info
  server_info = ServerInfo(*[getattr(pbmsg, a) for a in ServerInfo._fields])

  # meta: voice init
  _, pbmsg = packet.svc_voice_init
  voice_init = VoiceInit(*[getattr(pbmsg, a) for a in VoiceInit._fields])

  # prologue: meta
  meta = Meta(file_header, server_info, voice_init)

  # prologue: send tables
  _, pbmsg = prologue.dem_send_tables
  _send_tables = ie_send_tables.construct(p_io.construct(pbmsg.data))
  send_tables = c.OrderedDict()

  for pbmsg in [pb for _, pb in _send_tables.all_svc_send_table]:
    if pbmsg.is_end:
      break

    send_table = _parse_cdemo_send_table(pbmsg)
    send_tables[send_table.dt] = send_table

  # prologue: recv tables
  flattener = Flattener(send_tables)
  recv_tables = c.OrderedDict()

  _, pbmsg = prologue.dem_class_info
  class_info = c.OrderedDict()

  for cls in pbmsg.classes:
    _id, dt, name = str(cls.class_id), cls.table_name, cls.network_name
    class_info[_id] = (dt, name)

  for st in filter(test_needs_decoder, send_tables.values()):
    props = flattener.flatten(st)
    cls = next(_id for _id, (dt, _) in class_info.items() if dt == st.dt)
    recv_tables[cls] = dt_r.construct(st.dt, props)

  # prologue: string tables
  pbmsgs = [pb for _, pb in packet.all_svc_create_string_table]
  string_tables = _parse_all_csvc_create_string_tables(pbmsgs)

  # prologue: game event list
  _, pbmsg = packet.svc_game_event_list
  game_event_list = c.OrderedDict()

  for desc in pbmsg.descriptors:
    _id, name = desc.eventid, desc.name
    keys = [(k.type, k.name) for k in desc.keys]
    game_event_list[_id] = (name, keys)

  # prologue: class bits
  class_bits = server_info.max_classes.bit_length()

  return Prologue(meta, recv_tables, string_tables, game_event_list, class_bits)


def _parse_cdemo_send_table(pbmsg):
  dt, props = pbmsg.net_table_name, []

  for p in pbmsg.props:
    attributes = {
      'var_name': p.var_name,
      'type': p.type,
      'flags': p.flags,
      'num_elements': p.num_elements,
      'num_bits': p.num_bits,
      'dt_name': p.dt_name,
      'priority': p.priority,
      'low_value': p.low_value,
      'high_value': p.high_value
    }
    props.append(dt_p.construct(dt, attributes))

  # assign properties used for parsing array elements
  for i, p in enumerate(props):
    if p.type == dt_p.Type.Array:
      p.array_prop = props[i - 1]

  return dt_s.construct(dt, props, pbmsg.is_end, pbmsg.needs_decoder)


def _parse_all_csvc_create_string_tables(pbmsgs):
  string_tables = c.OrderedDict()

  for pbmsg in pbmsgs:
    ne = pbmsg.num_entries
    eb = int(math.ceil(math.log(pbmsg.max_entries, 2)))
    sf = pbmsg.user_data_fixed_size
    sb = pbmsg.user_data_size_bits
    bs = b_io.construct(pbmsg.string_data)

    entries = list(u_st.construct(bs, ne, eb, sf, sb))
    name = pbmsg.name
    string_tables[name] = stab.construct(name, eb, sf, sb, entries)

  return string_tables


class Flattener(object):
  def __init__(self, send_tables):
    self.send_tables = send_tables

  def flatten(self, st):
    aggregate = []
    exclusions = self._aggregate_exclusions(st)
    self._build(st, aggregate, exclusions, [])
    return aggregate

  def _build(self, st, aggregate, exclusions, props, proxy_for=None):
    self._compile(st, aggregate, exclusions, props)
    for p in props:
      if proxy_for:
        _p = copy.copy(p)
        _p.var_name = '{}.{}'.format(p.origin_dt, p.var_name).encode('UTF-8')
        _p.origin_dt = proxy_for
      else:
        _p = p
      aggregate.append(_p)

  def _compile(self, st, aggregate, exclusions, props):
    def test_excluded(p):
      return 

    for p in st.props:
      excluded = (st.dt, p.var_name) in exclusions
      ineligible = p.flags & (dt_p.Flag.Exclude | dt_p.Flag.InsideArray)
      if excluded or ineligible:
        continue

      if p.type == dt_p.Type.DataTable:
        _st = self.send_tables[p.dt_name]
        if dt_p.test_collapsible(p):
          self._compile(_st, aggregate, exclusions, props)
        else:
          self._build(_st, aggregate, exclusions, [], proxy_for=p.origin_dt)
      else:
        props.append(p)

  def _aggregate_exclusions(self, st):
    def recurse(_dt_prop):
      st = self.send_tables[_dt_prop.dt_name]
      return self._aggregate_exclusions(st)

    inherited = map(recurse, st.dt_props)

    return st.exclusions + list(it.chain(*inherited))
