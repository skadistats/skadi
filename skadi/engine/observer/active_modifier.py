import collections as c

from skadi.engine import world as w
from skadi.protoc import dota_modifiers_pb2 as pb_dm


def humanize(modifier, world):
  pass


def construct(*args):
  return ActiveModifierObserver(*args)


class ActiveModifierObserver(object):
  optionals = [
    'ability_level', 'stack_count', 'creation_time', 'caster', 'ability',
    'armor', 'fade_time', 'channel_time', 'portal_loop_appear',
    'portal_loop_disappear', 'hero_loop_appear', 'hero_loop_disappear',
    'movement_speed', 'activity', 'damage', 'duration'
  ]

  def __init__(self):
    self.reset()

  def __iter__(self):
    return self.by_parent.iteritems()

  def reset(self):
    self.by_parent = c.defaultdict(c.OrderedDict)
    self.to_expire = []

  def note(self, entry):
    i, n, d = entry

    pbmsg = pb_dm.CDOTAModifierBuffTableEntry()
    pbmsg.ParseFromString(d)

    parent = pbmsg.parent
    mhandle = w.to_ehandle(pbmsg.index, pbmsg.serial_num)

    if pbmsg.entry_type == pb_dm.DOTA_MODIFIER_ENTRY_TYPE_ACTIVE:
      attrs = {}
      for o in ActiveModifierObserver.optionals:
        val = getattr(pbmsg, o, None)
        if val:
          attrs[o] = val

      name, _ = self.modifier_names.by_index[pbmsg.name]
      attrs['name'] = name

      vs = pbmsg.v_start
      vec = (vs.x, vs.y, vs.z)
      if vec != (0, 0, 0):
        attrs['v_start'] = vec

      ve = pbmsg.v_end
      vec = (ve.x, ve.y, ve.z)
      if vec != (0, 0, 0):
        attrs['v_end'] = vec

      if 'duration' in attrs and attrs['duration'] <= 0:
        del attrs['duration']

      attrs['aura'] = pbmsg.aura or False
      attrs['subtle'] = pbmsg.aura or False

      if 'creation_time' in attrs and 'duration' in attrs:
        expiry = attrs['creation_time'] + attrs['duration']
      else:
        expiry = None

      self._add(parent, mhandle, attrs, until=expiry)
    else:
      self._remove(parent, mhandle)

  def expire(self, epoch):
    gone = [(e, (p, m)) for e, (p, m) in self.to_expire if epoch >= e]
    [self._remove(p, m) for _, (p, m) in gone]
    [self.to_expire.remove(record) for record in gone]

  def _add(self, parent, mhandle, attrs, until):
    self.by_parent[parent][mhandle] = attrs
    if until:
      record = (until, (parent, mhandle))
      self.to_expire.append(record)

  def _remove(self, parent, mhandle):
    try:
      del self.by_parent[parent][mhandle]
    except KeyError, e:
      # TODO: log here.
      pass
    finally:
      if not self.by_parent[parent]:
        del self.by_parent[parent]
