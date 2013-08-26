from skadi import index


def construct(*args):
  return EpilogueIndex(*args)


class EpilogueIndex(index.Index):
  def __init__(self, iterable):
    super(EpilogueIndex, self).__init__(iterable)

  @property
  def file_info_peek(self):
    return self.find(pb_d.DEM_FileInfo)
