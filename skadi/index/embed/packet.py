from skadi import index as i
from skadi.io.protobuf import packet as p_io
from skadi.protoc import netmessages_pb2 as pb_n


def construct(io, tick=0):
  return PacketIndex(((p, m) for p, m in iter(io)))


class PacketIndex(i.Index):
  def __init__(self, iterable):
    super(PacketIndex, self).__init__(iterable)

  # DEM_SignonPacket:

  @property
  def svc_game_event_list(self):
    kind = pb_n.svc_GameEventList
    p, m = self.find(kind)
    return p, p_io.parse(kind, m)

  @property
  def svc_server_info(self):
    kind = pb_n.svc_ServerInfo
    p, m = self.find(kind)
    return p, p_io.parse(kind, m)

  @property
  def svc_voice_init(self):
    kind = pb_n.svc_VoiceInit
    p, m = self.find(kind)
    return p, p_io.parse(kind, m)

  @property
  def all_svc_create_string_table(self):
    kind = pb_n.svc_CreateStringTable
    return ((p, p_io.parse(kind, m)) for p, m in self.find_all(kind))

  # DEM_Packet:

  @property
  def net_tick(self):
    kind = pb_n.net_Tick
    p, m = self.find(kind)
    return p, p_io.parse(kind, m)

  @property
  def svc_packet_entities(self):
    kind = pb_n.svc_PacketEntities
    p, m = self.find(kind)
    return p, p_io.parse(kind, m)

  @property
  def all_svc_update_string_table(self):
    kind = pb_n.svc_UpdateStringTable
    return ((p, p_io.parse(kind, m)) for p, m in self.find_all(kind))

  @property
  def all_svc_game_event(self):
    kind = pb_n.svc_GameEvent
    return ((p, p_io.parse(kind, m)) for p, m in self.find_all(kind))

  @property
  def all_svc_user_message(self):
    kind = pb_n.svc_UserMessage
    return ((p, p_io.parse(kind, m)) for p, m in self.find_all(kind))
