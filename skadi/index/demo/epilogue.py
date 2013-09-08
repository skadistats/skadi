from skadi import index as i
from skadi.protoc import demo_pb2 as pb_d


def construct(io, tick=0):
  return Index(((p, m) for p, m in iter(io)))


class EpilogueIndex(i.Index):
  def __init__(self, iterable):
    super(EpilogueIndex, self).__init__(iterable)

  @property
  def dem_file_info(self):
    kind = pb_d.DEM_FileInfo
    p, m = self.find(kind)
    return p, d_io.parse(kind, p.compressed, m)
