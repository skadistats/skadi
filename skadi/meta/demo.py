import collections

from skadi.io import protobuf as io_p
from skadi.meta import class_info, game_event_list, string_table
from skadi.meta import misc
from skadi.meta import prop, recv_table, send_table
from skadi.protoc import demo_pb2 as pb_d
from skadi.protoc import netmessages_pb2 as pb_n


DEMO_EXTRANEOUS = (pb_d.CDemoStringTables)
SVC_EXTRANEOUS = (
  pb_n.CNETMsg_SetConVar, pb_n.CNETMsg_SignonState, pb_n.CNETMsg_Tick,
  pb_n.CSVCMsg_ClassInfo
)

test_needs_decoder = lambda st: st.needs_decoder


def parse(io):
  meta = {
    'string_tables': collections.OrderedDict(),
    'send_tables': collections.OrderedDict(),
    'recv_tables': collections.OrderedDict()
  }

  for tick, pbmsg in io:
    if isinstance(pbmsg, pb_d.CDemoSyncTick):
      break
    elif isinstance(pbmsg, pb_d.CDemoClassInfo):
      meta['class_info'] = class_info.parse(pbmsg)
    elif isinstance(pbmsg, pb_d.CDemoFileHeader):
      meta['file_header'] = misc.parse(pbmsg, 'FileHeader')
    elif isinstance(pbmsg, pb_d.CDemoSendTables):
      # parse send tables
      for _pbmsg in iter(io_p.Packet.wrapping(pbmsg.data)):
        st = send_table.parse(_pbmsg)
        meta['send_tables'][st.dt] = st

      # flatten send tables into recv tables
      for st in filter(test_needs_decoder, meta['send_tables'].values()):
        props = send_table.flatten(st, meta['send_tables'])
        meta['recv_tables'][st.dt] = recv_table.construct(st.dt, props)
    elif isinstance(pbmsg, pb_d.CDemoPacket):
      for _pbmsg in io_p.Packet.wrapping(pbmsg.data):
        if isinstance(_pbmsg, pb_n.CSVCMsg_CreateStringTable):
          st = string_table.parse(_pbmsg)
          meta['string_tables'][st.name] = st
        elif isinstance(_pbmsg, pb_n.CSVCMsg_GameEventList):
          meta['game_event_list'] = game_event_list.parse(_pbmsg)
        elif isinstance(_pbmsg, pb_n.CSVCMsg_ServerInfo):
          meta['server_info'] = misc.parse(_pbmsg, 'ServerInfo')
        elif isinstance(_pbmsg, pb_n.CSVCMsg_VoiceInit):
          meta['voice_init'] = misc.parse(_pbmsg, 'VoiceInit')
        elif isinstance(_pbmsg, pb_n.CSVCMsg_SetView):
          meta['set_view'] = misc.parse(_pbmsg, 'SetView')
        elif not isinstance(_pbmsg, SVC_EXTRANEOUS):
          print "! ignoring: {0}".format(_pbmsg.__class__)
    elif not isinstance(pbmsg, DEMO_EXTRANEOUS):
      err = '! protobuf {0}: open issue at github.com/onethirtyfive/skadi'
      print err.format(pbmsg.__class__.__name__)

  full = collections.OrderedDict()
  norm = collections.OrderedDict()

  tell = io.tell()
  for tick, pbmsg in io:
    if isinstance(pbmsg, pb_d.CDemoFullPacket):
      full[tick] = tell
    elif isinstance(pbmsg, pb_d.CDemoPacket):
      norm[tick] = tell
    else:
      break
    tell = io.tell()

  io.seek(norm[0])

  return Demo(meta, full, norm)

class Demo(object):
  DELEGATED = (
    'game_event_list', 'file_header', 'recv_tables', 'set_view', 'voice_init',
    'server_info', 'class_info', 'string_tables', 'send_tables'
  )

  def __init__(self, meta, full, norm):
    self.meta = meta
    self.full = full
    self.norm = norm

  def at(self, tick):
    # This needs serious optimization.
    norm_gen = (t for t in reversed(self.norm.keys()) if t <= tick)
    full_gen = (t for t in reversed(self.full.keys()) if t <= tick)
    return self.full[next(full_gen)], self.norm[next(norm_gen)]

  def __getitem__(self, key):
    if key in self._attributes:
      return self._attributes[key]

    raise KeyError('unknown attribute {0}'.format(key))
