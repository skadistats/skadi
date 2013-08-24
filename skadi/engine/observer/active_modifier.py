import collections

from skadi.engine import world as w
from skadi.protoc import dota_modifiers_pb2 as pb_dm


def construct(*args):
  return ActiveModifierObserver(*args)


class ActiveModifierObserver(object):
  optionals = [
    'name', 'ability_level', 'stack_count', 'creation_time', 'caster',
    'ability', 'armor', 'fade_time', 'channel_time', 'portal_loop_appear',
    'portal_loop_disappear', 'hero_loop_appear', 'hero_loop_disappear',
    'movement_speed', 'activity', 'damage'
  ]

  def __init__(self):
    self.reset()

  def __iter__(self):
    return iter(self.by_mhandle.items())

  def reset(self):
    self.by_mhandle = collections.OrderedDict()
    self.by_parent = collections.defaultdict(list)
    self.by_caster = collections.defaultdict(list)

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

      vs = pbmsg.v_start
      vec = (vs.x, vs.y, vs.z)
      if vec != (0, 0, 0):
        attrs['v_start'] = vec

      ve = pbmsg.v_end
      vec = (ve.x, ve.y, ve.z)
      if vec != (0, 0, 0):
        attrs['v_end'] = vec

      if pbmsg.duration == -1:
        attrs['duration'] = None

      attrs['aura'] = pbmsg.aura or False
      attrs['subtle'] = pbmsg.aura or False

      self._add(mhandle, parent, attrs)
    else:
      self._remove(mhandle, parent)

  def find(self, mhandle):
    return self.by_mhandle[mhandle]

  def find_all_by_parent(self, parent):
    coll = [(mhndl, self.find(mhndl)) for mhndl in self.by_parent[parent]]
    return collections.OrderedDict(coll)

  def _add(self, mhandle, parent, attrs):
    self.by_parent[parent].append(mhandle)
    self.by_mhandle[mhandle] = (parent, attrs)

  def _remove(self, mhandle, parent):
    try:
      assert mhandle in self.by_mhandle
      assert mhandle in self.by_parent[parent]
    except AssertionError:
      return

    del self.by_mhandle[mhandle]
    self.by_parent[parent].remove(mhandle)
