from skadi import index as i
from skadi.io.protobuf import demo as d_io
from skadi.protoc import demo_pb2 as pb_d


def construct(io, tick=0):
  iter_entries = iter(io)

  def advance():
    p, m = next(iter_entries)
    if p.kind == pb_d.DEM_SyncTick:
      raise StopIteration()
    return (p, m)

  return Index(((p, m) for p, m in iter(advance, None)))


class Index(i.Index):
  def __init__(self, iterable):
    super(Index, self).__init__(iterable)

  @property
  def dem_file_header(self):
    kind = pb_d.DEM_FileHeader
    p, m = self.find(kind)
    return p, d_io.parse(kind, p.compressed, m)

  @property
  def dem_class_info(self):
    kind = pb_d.DEM_ClassInfo
    p, m = self.find(kind)
    return p, d_io.parse(kind, p.compressed, m)

  @property
  def dem_send_tables(self):
    kind = pb_d.DEM_SendTables
    p, m = self.find(kind)
    return p, d_io.parse(kind, p.compressed, m)

  @property
  def all_dem_signon_packet(self):
    kind = pb_d.DEM_SignonPacket
    ee = self.find_all(kind)
    return ((p, d_io.parse(kind, p.compressed, m)) for p, m in ee)
