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
from skadi import index as i
from skadi.engine import string_table as stab
from skadi.engine.dt import prop as dt_p
from skadi.engine.dt import recv as dt_r
from skadi.engine.dt import send as dt_s
from skadi.engine.observer import active_modifier as o_am
from skadi.index import prologue as i_p
from skadi.io import bitstream as b_io
from skadi.io.protobuf import demo as d_io
from skadi.io.protobuf import packet as p_io
from skadi.io.unpacker import string_table as u_st
from skadi.protoc import demo_pb2 as pb_d
from skadi.protoc import netmessages_pb2 as pb_n


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
  prologue = i_p.construct(demo_io)

  # mash all packet svc messages together, then index them
  signon_packets = list(prologue.all_dem_signon_packet)
  pbmsgs = [d_io.parse(p.kind, p.compressed, m) for p, m in signon_packets]
  data = ''.join([p.data for p in pbmsgs])
  packet_io = p_io.construct(data)
  packet = i.construct(packet_io)

  # class info
  peek, message = prologue.dem_class_info
  pbmsg = d_io.parse(peek.kind, peek.compressed, message)
  class_info = c.OrderedDict()

  for _c in pbmsg.classes:
    _id, dt, name = str(_c.class_id), _c.table_name, _c.network_name
    class_info[_id] = (dt, name)

  # send tables
  peek, message = prologue.dem_send_tables
  pbmsg = d_io.parse(peek.kind, peek.compressed, message)
  send_tables = c.OrderedDict()

  for peek, message in p_io.construct(pbmsg.data):
    pbmsg = p_io.parse(peek.kind, message)
    if pbmsg.is_end:
      break

    send_table = _parse_cdemo_send_table(pbmsg)
    send_tables[send_table.dt] = send_table

  # recv tables
  flattener = Flattener(send_tables)
  recv_tables = c.OrderedDict()

  for st in filter(test_needs_decoder, send_tables.values()):
    props = flattener.flatten(st)
    cls = next(_id for _id, (dt, _) in class_info.items() if dt == st.dt)
    recv_tables[cls] = dt_r.construct(st.dt, props)

  # game event list
  peek, message = packet.find(pb_n.svc_GameEventList)
  pbmsg = p_io.parse(peek.kind, message)
  game_event_list = c.OrderedDict()

  for desc in pbmsg.descriptors:
    _id, name = desc.eventid, desc.name
    keys = [(k.type, k.name) for k in desc.keys]
    game_event_list[_id] = (name, keys)

  # string tables
  entries = packet.find_all(pb_n.svc_CreateStringTable)
  pbmsgs = [p_io.parse(p.kind, m) for p, m in entries]
  string_tables = _parse_all_csvc_create_string_tables(pbmsgs)

  # meta: file header
  peek, message = prologue.dem_file_header
  pbmsg = d_io.parse(peek.kind, peek.compressed, message)
  file_header = FileHeader(*[getattr(pbmsg, a) for a in FileHeader._fields])

  # meta: server_info
  peek, message = packet.find(pb_n.svc_ServerInfo)
  pbmsg = p_io.parse(peek.kind, message)
  server_info = ServerInfo(*[getattr(pbmsg, a) for a in ServerInfo._fields])

  # meta: class bits
  class_bits = server_info.max_classes.bit_length()

  # meta: voice init
  peek, message = packet.find(pb_n.svc_VoiceInit)
  pbmsg = p_io.parse(peek.kind, message)
  voice_init = VoiceInit(*[getattr(pbmsg, a) for a in VoiceInit._fields])

  meta = Meta(file_header, server_info, voice_init)

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

  observer = o_am.construct()
  observer.modifier_names = string_tables['ModifierNames']
  string_tables['ActiveModifiers'].observer = observer

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
        _p.var_name = '{}.{}'.format(p.origin_dt, p.var_name)
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
