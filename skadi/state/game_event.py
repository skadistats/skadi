class GameEvent(object):
  def __init__(self, _id, name, keys):
    self.id = _id
    self.name = name
    self.keys = keys

  def __repr__(self):
    _id, n= self.id, self.name
    lenkeys = len(self.keys)
    return "<GameEvent {0} '{1}' ({2} keys)>".format(_id, n, lenkeys)
