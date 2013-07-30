import collections
import io

from skadi.index import InvalidProtobufMessage, Index
from skadi.io import read_varint
from skadi.protoc import netmessages_pb2 as pb_n


PBMSG_BY_ENUM = {
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


Peek = collections.namedtuple('Peek', ['cls', 'offset', 'size'])


def construct(stream):
  return PacketIndex(Indexer(stream))


def read(stream, peek):
  if peek.cls not in PBMSG_BY_ENUM.values():
    msg = 'please update netmessages.proto: {0}'.format(peek.cls)
    raise InvalidProtobufMessage(msg)

  stream.seek(peek.offset)

  message = peek.cls()
  message.ParseFromString(stream.read(peek.size))

  return message


class PacketIndex(Index):
  def __init__(self, iterable):
    super(PacketIndex, self).__init__(iterable)

  @property
  def full_packets(self):
    return filter(lambda p: self.find(pb_d.CDemoFullPacket), self.replay)

  @property
  def packets(self):
    return filter(lambda p: self.find(pb_d.CDemoPacket), self.replay)


class Indexer(object):
  def __init__(self, stream):
    self.stream = stream

  def __iter__(self):
    def next():
      return self.next()
    return iter(next, None)

  def next(self):
    start = self.stream.tell()

    try:
      enum = read_varint(self.stream)
      size = read_varint(self.stream)

      offset = self.stream.tell()

      self.stream.seek(offset + size)
    except EOFError, e:
      return None

    return Peek(cls=PBMSG_BY_ENUM[enum], offset=offset, size=size)
