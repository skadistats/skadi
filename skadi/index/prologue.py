from skadi import index
from skadi.protoc import demo_pb2 as pb_d


def construct(*args):
  return PrologueIndex(*args)


class PrologueIndex(index.Index):
  def __init__(self, iterable):
    super(PrologueIndex, self).__init__(iterable)

  @property
  def file_header(self):
    return self.find(pb_d.DEM_FileHeader)

  @property
  def class_info(self):
    return self.find(pb_d.DEM_ClassInfo)

  @property
  def send_tables(self):
    return self.find(pb_d.DEM_SendTables)

  @property
  def signon_packets(self):
    return self.find_all(pb_d.DEM_SignonPacket)
