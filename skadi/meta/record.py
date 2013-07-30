import math
import recordtype
import sys

from skadi.protoc import demo_pb2 as pb_d
from skadi.protoc import netmessages_pb2 as pb_n


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


SetView = recordtype('SetView', ['entity_index'])


StringTable = recordtype('StringTable', [
  'name', 'max_entries', 'num_entries', 'user_data_fixed_size',
  'user_data_size', 'user_data_size_bits', 'flags', 'entry_bits', 'items'
])


VoiceInit = recordtype('VoiceInit', ['quality', 'codec'])


RECORD_BY_PBMSG = {
  pb_d.CDemoFileHeader: FileHeader,
  pb_n.CSVCMsg_ServerInfo: ServerInfo,
  pb_n.CSVCMsg_SetView: SetView,
  pb_n.CSVCMsg_VoiceInit: VoiceInit
}


def parse(pbmsg):
  cls = pbmsg.__class__
  if cls in RECORD_BY_PBMSG:
    impl = RECORD_BY_PBMSG[cls]
    return impl([getattr(pbmsg, f) for f in cls._fields])

  parser = 'parse_{0}'.format(cls.__name__)
  return getattr(sys.modules[__name__], parser)(pbmsg)


def parse_CDemoClassInfo(pbmsg):
  class_info = collections.OrderedDict()

  for c in pbmsg.classes:
    _id, dt, name = c.class_id, c.table_name, c.network_name
    class_info[c.class_id] = Class(_id, name, dt)

  return class_info


def parse_CSVCMsg_CreateStringTable(pbmsg):
  name = pbmsg.name
  me, ne = pbmsg.max_entries, pbmsg.num_entries
  udfs = pbmsg.user_data_fixed_size
  uds, udsb = pbmsg.user_data_size, pbmsg.user_data_size_bits
  flags = pbmsg.flags
  ebits = int(math.ceil(math.log(self.max_entries, 2)))

  st = StringTable(name, me, ne, udfs, uds, udsb, flags, ebits, None)
  st.items = d_string_table.decode(bitstream_io.wrap(pbmsg.string_data), st)

  return st
