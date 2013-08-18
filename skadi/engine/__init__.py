import collections
import io
import itertools
import math

from skadi import bitlength
from skadi.index import packet as pi
from skadi.engine import bitstream as bs
from skadi.engine import string_table as stab
from skadi.engine.dt import prop as dt_prop
from skadi.engine.dt import recv as dt_recv
from skadi.engine.dt import send as dt_send
from skadi.engine.unpacker import string_table as ust


test_needs_decoder = lambda st: st.needs_decoder


def parse_cdemo_file_header(pbmsg):
  attrs = [
    'demo_file_stamp', 'network_protocol', 'server_name', 'client_name',
    'map_name', 'game_directory', 'fullpackets_version'
  ]

  return {attr:getattr(pbmsg, attr) for attr in attrs}


def parse_cdemo_class_info(pbmsg):
  class_info = collections.OrderedDict()

  for c in pbmsg.classes:
    _id, dt, name = str(c.class_id), c.table_name, c.network_name
    class_info[_id] = (dt, name)

  return class_info


def parse_cdemo_send_tables(pbmsg):
  send_tables = collections.OrderedDict()
  p_io = io.BufferedReader(io.BytesIO(pbmsg.data))

  for peek in pi.index(p_io):
    csvc_create_send_table = pi.read(p_io, peek)

    if csvc_create_send_table.is_end:
      break

    send_table = dt_send.parse(csvc_create_send_table)
    send_tables[send_table.dt] = send_table

  return send_tables


class Flattener(object):
  def __init__(self, send_tables):
    self.send_tables = send_tables

  def flatten(self, st):
    aggregate = []
    exclusions = self._aggregate_exclusions(st)
    self._build(st, aggregate, exclusions, [])
    return aggregate

  def _build(self, st, aggregate, exclusions, props):
    self._compile(st, aggregate, exclusions, props)
    for p in props:
      aggregate.append(p)

  def _compile(self, st, aggregate, exclusions, props):
    def test_excluded(p):
      return 

    for p in st.props:
      excluded = (st.dt, p.var_name) in exclusions
      ineligible = p.flags & (dt_prop.Flag.Exclude | dt_prop.Flag.InsideArray)
      if excluded or ineligible:
        continue

      if p.type == dt_prop.Type.DataTable:
        _st = self.send_tables[p.dt_name]
        if dt_prop.test_collapsible(p):
          self._compile(_st, aggregate, exclusions, props)
        else:
          self._build(_st, aggregate, exclusions, [])
      else:
        props.append(p)

  def _aggregate_exclusions(self, st):
    def recurse(_dt_prop):
      st = self.send_tables[_dt_prop.dt_name]
      return self._aggregate_exclusions(st)

    inherited = map(recurse, st.dt_props)

    return st.exclusions + list(itertools.chain(*inherited))


def flatten(class_info, send_tables):
  flattener = Flattener(send_tables)
  recv_tables = collections.OrderedDict()

  for st in filter(test_needs_decoder, send_tables.values()):
    props = flattener.flatten(st)
    cls = next(_id for _id, (dt, _) in class_info.items() if dt == st.dt)
    recv_tables[cls] = dt_recv.construct(st.dt, props)

  return recv_tables


def parse_all_csvc_create_string_table(pbmsgs):
  string_tables = collections.OrderedDict()

  for pbmsg in pbmsgs:
    bitstream = bs.construct(pbmsg.string_data)
    ne = pbmsg.num_entries
    eb = bitlength(pbmsg.max_entries)
    sf = pbmsg.user_data_fixed_size
    sb = pbmsg.user_data_size_bits
    entries = list(ust.Unpacker(bitstream, ne, eb, sf, sb))

    name = pbmsg.name
    string_tables[name] = stab.construct(name, eb, sf, sb, entries)

  return string_tables


def parse_csvc_voice_init(pbmsg):
  attrs = ['quality', 'codec']

  return {attr:getattr(pbmsg, attr) for attr in attrs}


def parse_csvc_server_info(pbmsg):
  attrs = [
    'protocol', 'server_count', 'is_dedicated', 'is_hltv', 'c_os', 'map_crc',
    'client_crc', 'string_table_crc', 'max_clients', 'max_classes',
    'player_slot', 'tick_interval', 'game_dir', 'map_name', 'sky_name',
    'host_name'
  ]

  return {attr:getattr(pbmsg, attr) for attr in attrs}


def parse_csvc_game_event_list(pbmsg):
  game_event_list = collections.OrderedDict()

  for desc in pbmsg.descriptors:
    _id, name = desc.eventid, desc.name
    keys = [(k.type, k.name) for k in desc.keys]
    game_event_list[_id] = (name, keys)

  return game_event_list