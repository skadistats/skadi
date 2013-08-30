from __future__ import absolute_import

from skadi import Peek
from skadi.io import protobuf
from skadi.protoc import netmessages_pb2 as pb_n
from skadi.protoc import networkbasetypes_pb2 as pb_nbt

import io as _io


IMPL_BY_KIND = {
  pb_n.net_SetConVar:         pb_n.CNETMsg_SetConVar,
  pb_n.net_SignonState:       pb_n.CNETMsg_SignonState,
  pb_n.net_Tick:              pb_n.CNETMsg_Tick,
  pb_n.svc_ClassInfo:         pb_n.CSVCMsg_ClassInfo,
  pb_n.svc_CreateStringTable: pb_n.CSVCMsg_CreateStringTable,
  pb_n.svc_GameEventList:     pb_n.CSVCMsg_GameEventList,
  pb_n.svc_Menu:              pb_n.CSVCMsg_Menu,
  pb_n.svc_PacketEntities:    pb_n.CSVCMsg_PacketEntities,
  pb_n.svc_SendTable:         pb_n.CSVCMsg_SendTable,
  pb_n.svc_ServerInfo:        pb_n.CSVCMsg_ServerInfo,
  pb_n.svc_SetView:           pb_n.CSVCMsg_SetView,
  pb_n.svc_Sounds:            pb_n.CSVCMsg_Sounds,
  pb_n.svc_TempEntities:      pb_n.CSVCMsg_TempEntities,
  pb_n.svc_UpdateStringTable: pb_n.CSVCMsg_UpdateStringTable,
  pb_n.svc_VoiceInit:         pb_n.CSVCMsg_VoiceInit,
  pb_n.svc_VoiceData:         pb_n.CSVCMsg_VoiceData,
  pb_n.svc_GameEvent:         pb_nbt.CSVCMsg_GameEvent,
  pb_n.svc_UserMessage:       pb_nbt.CSVCMsg_UserMessage
}


def construct(data):
  buff = _io.BufferedReader(_io.BytesIO(data))
  return PacketIO(buff)


def parse(kind, message):
  return protobuf.parse(IMPL_BY_KIND[kind], message)


class PacketIO(protobuf.ProtobufIO):
  def __init__(self, io, tick=0):
    super(PacketIO, self).__init__(io)
    self.tick = tick

  def read(self):
    try:
      kind = self.read_varint()
      size = self.read_varint()
    except EOFError:
      raise StopIteration()

    if kind in IMPL_BY_KIND:
      message = self.io.read(size)
    else:
      # TODO: log here.
      print 'unknown kind {}'.format(kind)
      message = None

    return Peek(self.tick, kind, self.io.tell(), size, False), message
