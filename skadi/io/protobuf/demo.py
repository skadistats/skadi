import snappy

from skadi import *
from skadi import index
from skadi.io import protobuf
from skadi.protoc import demo_pb2 as pb_d


IMPL_BY_KIND = {
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


def construct(io):
  return DemoIO(io)


def parse(kind, compressed, message):
  if compressed:
    message = snappy.uncompress(message)

  return protobuf.parse(IMPL_BY_KIND[kind], message)


class DemoIO(protobuf.ProtobufIO):
  def __init__(self, io):
    super(DemoIO, self).__init__(io)

  def read(self):
    try:
      kind = self.read_varint()
      comp = bool(kind & pb_d.DEM_IsCompressed)
      kind = (kind & ~pb_d.DEM_IsCompressed) if comp else kind

      tick = self.read_varint()
      size = self.read_varint()
    except EOFError:
      raise StopIteration()

    if kind in IMPL_BY_KIND:
      message = self.io.read(size)
    else:
      # TODO: log here.
      print 'unknown kind {}'.format(kind)
      message = None
      self.io.read(size)

    return Peek(tick, kind, self.io.tell(), size, comp), message
