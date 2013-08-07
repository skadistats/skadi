import collections
import math
import skadi
import sys

from recordtype import recordtype
from skadi.decoder import string_table as st_dec
from skadi.index import demo as d_index
from skadi.index import packet as p_index
from skadi.io import bitstream as bitstream_io
from skadi.meta import prop
from skadi.meta import recv_table
from skadi.meta import send_table
from skadi.protoc import demo_pb2 as pb_d
from skadi.protoc import netmessages_pb2 as pb_n
from skadi import state


SVC_EXTRANEOUS = (
  pb_n.CNETMsg_Tick, pb_n.CNETMsg_SetConVar, pb_n.CNETMsg_SignonState,
  pb_n.CSVCMsg_ClassInfo, pb_n.CSVCMsg_SetView
)


Meta = recordtype('Meta', [
  'file_header', 'class_info', 'send_tables', 'recv_tables', 'string_tables',
  'server_info', 'class_bits', 'voice_init', 'templates'
])


Class = recordtype('Class', ['id', 'dt', 'name'])


FileHeader = recordtype('FileHeader', [
  'demo_file_stamp', 'network_protocol', 'server_name', 'client_name',
  'map_name', 'game_directory', 'fullpackets_version'
])


ServerInfo = recordtype('ServerInfo', [
  'protocol', 'server_count', 'is_dedicated', 'is_hltv', 'c_os', 'map_crc',
  'client_crc', 'string_table_crc', 'max_clients', 'max_classes',
  'player_slot', 'tick_interval', 'game_dir', 'map_name', 'sky_name',
  'host_name'
])


StringTable = recordtype('StringTable', [
  'name', 'max_entries', 'num_entries', 'user_data_fixed_size',
  'user_data_size', 'user_data_size_bits', 'flags', 'entry_bits', 'items'
])


VoiceInit = recordtype('VoiceInit', ['quality', 'codec'])


RECORD_BY_PBMSG = {
  pb_d.CDemoFileHeader: FileHeader,
  pb_n.CSVCMsg_ServerInfo: ServerInfo,
  pb_n.CSVCMsg_VoiceInit: VoiceInit
}


test_needs_decoder = lambda st: st.needs_decoder


def construct(prologue, stream):
  demo_file_header = d_index.read(stream, prologue.file_header_peek)
  file_header = parse_generic(demo_file_header)

  demo_class_info = d_index.read(stream, prologue.class_info_peek)
  class_info = parse_CDemoClassInfo(demo_class_info)

  demo_send_tables = d_index.read(stream, prologue.send_tables_peek)
  send_tables = parse_send_tables(demo_send_tables)
  recv_tables = flatten(class_info, send_tables)

  server_info = None
  class_bits = None
  voice_init = None
  templates = None
  string_tables = collections.OrderedDict()
 
  for peek in prologue.packet_peeks:
    demo_packet = d_index.read(stream, peek)
    dp_stream = skadi.io.buffer(demo_packet.data)

    for _peek in p_index.construct(dp_stream):
      pbmsg = p_index.read(dp_stream, _peek)

      if isinstance(pbmsg, pb_n.CSVCMsg_CreateStringTable):
        string_table = parse_CSVCMsg_CreateStringTable(pbmsg)
        string_tables[string_table.name] = string_table
      elif isinstance(pbmsg, pb_n.CSVCMsg_GameEventList):
        pass
      elif isinstance(pbmsg, pb_n.CSVCMsg_ServerInfo):
        server_info = parse_generic(pbmsg)
        class_bits = int(math.ceil(math.log(server_info.max_classes, 2)))
      elif isinstance(pbmsg, pb_n.CSVCMsg_VoiceInit):
        voice_init = parse_generic(pbmsg)
      elif not isinstance(pbmsg, SVC_EXTRANEOUS):
        raise RuntimeError('unknown pbmsg {0}', pbmsg.__class__)

  st_ib = string_tables['instancebaseline']
  templates = \
    state.derive_templates(recv_tables, st_ib, collections.OrderedDict())

  return Meta(
    file_header, class_info, send_tables, recv_tables, string_tables,
    server_info, class_bits, voice_init, templates
  )


def parse_generic(pbmsg):
  cls = pbmsg.__class__
  if cls in RECORD_BY_PBMSG:
    impl = RECORD_BY_PBMSG[cls]
    return impl(*[getattr(pbmsg, f) for f in impl.__slots__])

  parser = 'parse_{0}'.format(cls.__name__)
  return getattr(sys.modules[__name__], parser)(pbmsg)


def parse_send_tables(pbmsg):
  send_tables = collections.OrderedDict()
  st_buffer = skadi.io.buffer(pbmsg.data)
  st_index = p_index.construct(st_buffer)

  for peek in st_index.find_all(pb_n.CSVCMsg_SendTable):
    pbmsg = p_index.read(st_buffer, peek)
    send_tables[pbmsg.net_table_name] = parse_CSVCMsg_SendTable(pbmsg)

  return send_tables


def flatten(class_info, send_tables):
  recv_tables = collections.OrderedDict()

  for st in filter(test_needs_decoder, send_tables.values()):
    props = send_table.flatten(st, send_tables)
    cls = next(c.id for c in class_info.values() if c.dt == st.dt)
    recv_tables[cls] = recv_table.construct(st.dt, props)

  return recv_tables


def parse_CDemoClassInfo(pbmsg):
  class_info = collections.OrderedDict()

  for c in pbmsg.classes:
    _id, dt, name = str(c.class_id), c.table_name, c.network_name
    class_info[_id] = Class(_id, dt, name)

  return class_info


def parse_CSVCMsg_SendTable(pbmsg):
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
    props.append(prop.Prop(dt, attributes))

  # assign properties used for parsing array elements
  for i, p in enumerate(props):
    if p.type == prop.Type.Array:
      p.array_prop = props[i - 1]

  return send_table.SendTable(dt, props, pbmsg.is_end, pbmsg.needs_decoder)


def parse_CSVCMsg_CreateStringTable(pbmsg):
  name = pbmsg.name
  me, ne = pbmsg.max_entries, pbmsg.num_entries
  udfs = pbmsg.user_data_fixed_size
  uds, udsb = pbmsg.user_data_size, pbmsg.user_data_size_bits
  flags = pbmsg.flags
  ebits = int(math.ceil(math.log(pbmsg.max_entries, 2)))

  st = StringTable(name, me, ne, udfs, uds, udsb, flags, ebits, None)
  items = collections.OrderedDict()

  for raw in st_dec.decode(bitstream_io.wrap(pbmsg.string_data), st):
    index, name, data = raw
    items[index] = (name, data)

  st.items = items

  return st
