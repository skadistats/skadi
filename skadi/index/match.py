import itertools as it

from skadi import index
from skadi.protoc import demo_pb2 as pb_d


test_full_packet = lambda p: p.kind == pb_d.DEM_FullPacket
test_packet = lambda p: p.kind == pb_d.DEM_Packet


def construct(*args):
  return MatchIndex(*args)


class MatchIndex(index.Index):
  def __init__(self, iterable):
    super(MatchIndex, self).__init__(iterable)
    self.full_ticks = map(lambda (p, _): p.tick, list(self.full_packets))
    self.ticks = map(lambda (p, _): p.tick, list(self.packets))
    self._t = reversed(self.ticks)
    self._ft = reversed(self.full_ticks)

  def find_earlier(self, tick):
    return it.ifilter(lambda (p, _): p.tick < tick, self)

  def find_when(self, tick):
    return it.ifilter(lambda (p, _): p.tick == tick, self)

  def find_later(self, tick):
    return it.ifilter(lambda (p, _): p.tick > tick, self)

  def locate_full_tick(self, near):
    return next(ft for ft in self._ft if ft <= near)

  def locate_tick(self, near):
    return next(t for t in self._t if t <= near)

  def locate(self, near):
    return self.locate_full_tick(near), self.locate_tick(near)

  def locate_between(self, low, high):
    return (t for t in self.ticks if low <= t <= high)

  def lookup_full(self, tick):
    g = ((p, m) for p, m in self if p.tick == tick and test_full_packet(p))
    return next(g, None)

  def lookup_full_between(self, l, h):
    g = ((p, m) for p, m in self if l <= p.tick <= h and test_full_packet(p))
    return g

  def lookup(self, tick):
    g = ((p, m) for p, m in self if p.tick == tick and test_packet(p))
    return next(g, None)

  def lookup_between(self, l, h):
    return ((p, m) for p, m in self if l <= p.tick <= h and test_packet(p))

  @property
  def full_packets(self):
    return it.ifilter(lambda (p, _): test_full_packet(p), self)

  @property
  def packets(self):
    return it.ifilter(lambda (p, _): test_packet(p), self)
