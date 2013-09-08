from skadi import index as i
from skadi.io.protobuf import packet as p_io
from skadi.protoc import netmessages_pb2 as pb_n


def construct(io, tick=0):
  return SendTablesIndex(((p, m) for p, m in iter(io)))


class SendTablesIndex(i.Index):
  def __init__(self, iterable):
    super(SendTablesIndex, self).__init__(iterable)

  @property
  def all_svc_send_table(self):
    kind = pb_n.svc_SendTable
    ee = self.find_all(kind)
    return ((p, p_io.parse(kind, m)) for p, m in ee)
