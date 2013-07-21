import math
import re

from skadi.domain import demo as d_demo
from skadi.domain import dt as d_dt
from skadi.domain import string_table as d_st
from skadi.generated import demo_pb2 as pb_d
from skadi.generated import netmessages_pb2 as pb_n
from skadi.io import bitstream as io_b
from skadi.io import protobuf as io_p
from skadi.reader import chronology as r_chron
from skadi.reader import string_table as r_st

DEMO_PRESYNC = (
  pb_d.CDemoFileHeader, pb_d.CDemoSendTables, pb_d.CDemoClassInfo
)

DEMO_EXTRANEOUS = (pb_d.CDemoStringTables)

SVC_RELEVANT = (
  pb_n.CSVCMsg_ServerInfo, pb_n.CSVCMsg_VoiceInit, pb_n.CSVCMsg_GameEventList,
  pb_n.CSVCMsg_SetView
)

def underscore(_str):
  s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', _str)
  return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()

def read(io):
  dem = d_demo.Demo()

  # Process messages before CDemoSyncTick.
  for pbmsg in iter(io):
    if isinstance(pbmsg, pb_d.CDemoSyncTick):
      break
    elif isinstance(pbmsg, pb_d.CDemoPacket):
      packet_io = io_p.Packet.wrapping(pbmsg.data)
      for _pbmsg in packet_io:
        match = re.match(r'C(SVC|NET)Msg_(.*)$', _pbmsg.__class__.__name__)
        attr = underscore(match.group(2))
        if isinstance(_pbmsg, pb_n.CSVCMsg_CreateStringTable):
          name, flags = _pbmsg.name, _pbmsg.flags
          me, ne = _pbmsg.max_entries, _pbmsg.num_entries
          udfs = _pbmsg.user_data_fixed_size
          uds, udsb = _pbmsg.user_data_size, _pbmsg.user_data_size_bits
          st = d_st.StringTable(name, me, ne, udfs, uds, udsb, flags)

          if _pbmsg.string_data:
            st.items = r_st.read(io_b.Bitstream(_pbmsg.string_data), st)
            dem.string_tables[name] = st
        if isinstance(_pbmsg, SVC_RELEVANT):
          setattr(dem, attr, _pbmsg)
    elif isinstance(pbmsg, DEMO_PRESYNC):
      matches = re.match(r'CDemo(.*)$', pbmsg.__class__.__name__)
      attr = underscore(matches.group(1))
      setattr(dem, attr, pbmsg)
    elif not isinstance(pbmsg, DEMO_EXTRANEOUS):
      err = '! protobuf {0}: open issue at github.com/onethirtyfive/skadi'
      print err.format(pbmsg.__class__.__name__)

  # For array props, we need to associate the element property.
  for send_table in dem.send_tables.values():
    for i, prop in enumerate(send_table.props):
      if prop.type == d_dt.Type.Array:
        prop.array_prop = send_table.props[i - 1]

  # Generate entity templates upon which instances will be based.
  dem.generate_entity_templates()

  dem.post_sync = io.tell()

  # Parse remainder of demo for a chronology of CDemoFullPacket.
  max_classes = dem.server_info['max_classes']
  dem.class_bits = int(math.ceil(math.log(max_classes, 2)))
  dem.chronology = r_chron.read(io)

  return dem
