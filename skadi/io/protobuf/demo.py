import collections
import snappy

from skadi.io.protobuf import read_varint_32, InvalidProtobufMessage
from skadi.protoc import demo_pb2 as pb_d


PBMSG_BY_ENUM = {
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


Peek = collections.namedtuple('Peek', ['cls', 'offset', 'size', 'compressed'])


def read(stream, peek):
  if peek.cls not in PBMSG_BY_ENUM.values():
    msg = 'please update demo.proto: {0}'.format(peek.cls)
    raise InvalidProtobufMessage(msg)

  stream.seek(peek.offset)

  data = stream.read(peek.size)
  if peek.compressed:
    data = snappy.uncompress(data)

  message = peek.cls()
  message.ParseFromString(data)

  return message


def scan(stream):
  return iter(Scanner(stream))


class Scanner(object):
  def __init__(self, stream):
    self.stream = stream

  def __iter__(self):
    def next_message():
      tick, peek = self.peek()
      self.stream.seek(peek.offset + peek.size)
      return tick, peek
    return iter(next_message, None)

  def peek(self):
    start = self.stream.tell()

    try:
      enum = read_varint_32(self.stream)
      tick = read_varint_32(self.stream)
      size = read_varint_32(self.stream)

      compressed = (pb_d.DEM_IsCompressed & enum) == pb_d.DEM_IsCompressed
      enum = (enum ^ pb_d.DEM_IsCompressed) if compressed else enum

      offset = self.stream.tell()
    except EOFError, e:
      return None
    finally:
      self.stream.seek(start)

    cls, o, s, c = PBMSG_BY_ENUM[enum], offset, size, compressed

    return tick, Peek(cls=cls, offset=o, size=s, compressed=c)
