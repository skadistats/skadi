

class InvalidProtobufMessage(Exception):
  pass


class Index(object):
  def __init__(self, iterable):
    self.peeks = list(iterable)

  def __iter__(self):
    return iter(self.peeks)

  def find(self, cls):
    return next(iter(filter(lambda p: p.cls == cls, self.peeks)), None)

  def find_all(self, cls):
    return filter(lambda p: p.cls == cls, self.peeks)

  def find_behind(self, offset):
    return filter(lambda p: p.offset < offset, self.peeks)

  def find_at(self, offset):
    return filter(lambda p: p.offset == offset, self.peeks)

  def find_ahead(self, offset):
    return filter(lambda p: p.offset > offset, self.peeks)
