import collections


def parse(pbmsg):
  game_events = collections.OrderedDict()

  for desc in pbmsg.descriptors:
    _id, name = desc.eventid, desc.name
    keys = [(k.type, k.name) for k in desc.keys]
    game_events[_id] = GameEvent(_id, name, keys)

  return GameEventList(game_events)


class GameEventList(object):
  def __init__(self, game_events):
    self.game_events = game_events


class GameEvent(object):
  def __init__(self, _id, name, keys):
    self.id = _id
    self.name = name
    self.keys = keys

  def __repr__(self):
    _id, n= self.id, self.name
    lenkeys = len(self.keys)
    return "<GameEvent {0} '{1}' ({2} keys)>".format(_id, n, lenkeys)
