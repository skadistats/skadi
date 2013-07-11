import collections as c
import io
import math
import snappy

from skadi.generated import demo_pb2 as pb_d
from skadi.generated import netmessages_pb2 as pb_n

VI_BIT_MAX = 32
VI_SHIFT = 7
VI_MAX_BYTES = int(math.ceil(float(VI_BIT_MAX) / VI_SHIFT))
VI_MASK = (1 << 32) - 1

class InvalidVarint32(Exception):
  pass
class InvalidProtobufMessage(Exception):
  pass
class InvalidDemo(Exception):
  pass

class IOWrapper(object):
  def __init__(self, io):
    self._io = io

  def __iter__(self):
    def next_message():
      return self.read_message()
    return iter(next_message, None)

  # Algorithm "borrowed" from Google protobuf library.
  def peek_varint_32(self):
    peeked = self._io.peek(VI_MAX_BYTES)
    bytesize, value, shift = 0, 0, 0

    while True:
      if bytesize >= len(peeked):
        raise EOFError()

      byte = ord(peeked[bytesize])
      bytesize += 1
      value |= ((byte & 0x7f) << shift)
      shift += VI_SHIFT

      if not (byte & 0x80):
        value &= VI_MASK
        return (value, bytesize)

      if shift >= VI_BIT_MAX:
        raise InvalidVarint32()

  def read_varint_32(self):
    value, bytesize = self.peek_varint_32()
    self._io.read(bytesize)
    return value

class PacketIO(IOWrapper):
  PARSER_BY_SIGNATURE = {
    pb_n.net_SetConVar:         pb_n.CNETMsg_SetConVar,
    pb_n.net_SignonState:       pb_n.CNETMsg_SignonState,
    pb_n.net_Tick:              pb_n.CNETMsg_Tick,
    pb_n.svc_ClassInfo:         pb_n.CSVCMsg_ClassInfo,
    pb_n.svc_CreateStringTable: pb_n.CSVCMsg_CreateStringTable,
    pb_n.svc_GameEvent:         pb_n.CSVCMsg_GameEvent,
    pb_n.svc_GameEventList:     pb_n.CSVCMsg_GameEventList,
    pb_n.svc_Menu:              pb_n.CSVCMsg_Menu,
    pb_n.svc_PacketEntities:    pb_n.CSVCMsg_PacketEntities,
    pb_n.svc_SendTable:         pb_n.CSVCMsg_SendTable,
    pb_n.svc_ServerInfo:        pb_n.CSVCMsg_ServerInfo,
    pb_n.svc_SetView:           pb_n.CSVCMsg_SetView,
    pb_n.svc_Sounds:            pb_n.CSVCMsg_Sounds,
    pb_n.svc_TempEntities:      pb_n.CSVCMsg_TempEntities,
    pb_n.svc_UpdateStringTable: pb_n.CSVCMsg_UpdateStringTable,
    pb_n.svc_UserMessage:       pb_n.CSVCMsg_UserMessage,
    pb_n.svc_VoiceInit:         pb_n.CSVCMsg_VoiceInit,
    pb_n.svc_VoiceData:         pb_n.CSVCMsg_VoiceData
  }

  @classmethod
  def wrapping(cls, bytes):
    return cls(io.BufferedReader(io.BytesIO(bytes)))

  def __init__(self, io):
    super(PacketIO, self).__init__(io)

  def read_message(self):
    try:
      sig = self.read_varint_32()
      size = self.read_varint_32()
      data = self._io.read(size)
    except EOFError, e:
      return None

    if sig not in PacketIO.PARSER_BY_SIGNATURE:
      msg = 'please update protobuf definitions: {0}'.format(sig)
      raise InvalidProtobufMessage(msg)

    message = PacketIO.PARSER_BY_SIGNATURE[sig]()
    message.ParseFromString(data)

    return message

  def rewind(self):
    self._io.seek(0)

class Chronology(object):
  def __init__(self):
    self.epochs = c.OrderedDict()

  def note(self, tick, pos):
    self.epochs[tick] = pos

class DemoIO(IOWrapper):
  HEADER = "PBUFDEM\0"

  PROTOBUF_CLASS_BY_SIGNATURE = {
    pb_d.DEM_Stop:                pb_d.CDemoStop,
    pb_d.DEM_FileHeader:          pb_d.CDemoFileHeader,
    pb_d.DEM_FileInfo:            pb_d.CDemoFileInfo,
    pb_d.DEM_SendTables:          pb_d.CDemoSendTables,
    pb_d.DEM_SyncTick:            pb_d.CDemoSyncTick,
    pb_d.DEM_ClassInfo:           pb_d.CDemoClassInfo,
    pb_d.DEM_StringTables:        pb_d.CDemoStringTables,
    pb_d.DEM_Packet:              pb_d.CDemoPacket,
    pb_d.DEM_SignonPacket:        pb_d.CDemoPacket,
    pb_d.DEM_ConsoleCmd:          pb_d.CDemoConsoleCmd,
    pb_d.DEM_CustomData:          pb_d.CDemoCustomData,
    pb_d.DEM_CustomDataCallbacks: pb_d.CDemoCustomDataCallbacks,
    pb_d.DEM_UserCmd:             pb_d.CDemoUserCmd,
    pb_d.DEM_FullPacket:          pb_d.CDemoFullPacket
  }

  def __init__(self, io):
    super(DemoIO, self).__init__(io)
    self._verify()

  def read_message(self):
    try:
      sig = self.read_varint_32()
      tick = self.read_varint_32()
      size = self.read_varint_32()
      data = self._io.read(size)

      if (pb_d.DEM_IsCompressed & sig) == pb_d.DEM_IsCompressed:
        sig ^= pb_d.DEM_IsCompressed
        data = snappy.uncompress(data)
    except EOFError, e:
      return None

    if sig not in DemoIO.PROTOBUF_CLASS_BY_SIGNATURE:
      msg = 'please update protobuf definitions: {0}'.format(sig)
      raise InvalidProtobufMessage(msg)

    message = DemoIO.PROTOBUF_CLASS_BY_SIGNATURE[sig]()
    message.ParseFromString(data)

    return message

  def seek(self, offset, whence=io.SEEK_SET):
    self._io.seek(offset, whence)

  def tell(self):
    return self._io.tell()

  def chronologize(self):
    chronology = Chronology()
    iter_d = iter(self)
    pbmsg = next(iter_d, None) # skip the stray CDemoPacket
    pos = self.tell()
    pbmsg = next(iter_d, None)
    while not isinstance(pbmsg, pb_d.CDemoStop):
      if isinstance(pbmsg, pb_d.CDemoFullPacket):
        packet_io = PacketIO.wrapping(pbmsg.packet.data)
        for _pbmsg in iter(packet_io):
          if isinstance(_pbmsg, pb_n.CNETMsg_Tick):
            chronology.note(_pbmsg.tick, pos)
            break
      pos = self.tell()
      pbmsg = next(iter_d, None)
    return chronology

  def rewind(self):
    self._io.seek(len(DemoIO.HEADER) + 4)

  def _verify(self):
    header = self._io.read(len(DemoIO.HEADER))
    next_4 = self._io.read(4) # offset of game info at end of file
    if header != DemoIO.HEADER:
      raise InvalidDemo()
