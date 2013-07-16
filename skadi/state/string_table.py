class String(object):
  def __init__(self, name, data):
    self.name = name
    self.data = data

  def __repr__(self):
    n, d = self.name, self.data
    return "<String '{0}' ({1} bytes)>".format(n, len(d))

class StringTable(object):
  def __init__(self, name, flags, items, items_clientside):
    self.name = name
    self.items = items
    self.items_clientside = items_clientside
    self.flags = flags

    if self.items_clientside:
      raise NotImplementedError('skadi does not handle clientside items!')

  def __repr__(self):
    n, f = self.name, hex(int(self.flags))
    lenitems = len(self.items)
    lenitemsc = len(self.items_clientside)
    _repr = "<StringTable '{0}' f:{1} ({2} items, {3} items clientside)"
    return _repr.format(n, f, lenitems, lenitemsc)
