import collections

from skadi.generated import demo_pb2 as pb_d

class Chronology(object):
  def __init__(self):
    self.epochs = collections.OrderedDict()

  def note(self, tick, pos):
    self.epochs[tick] = pos
