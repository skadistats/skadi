import collections

from skadi.engine import world as w
from skadi.protoc import dota_modifiers_pb2 as pb_dm


def construct(*args):
  return ActiveModifierObserver(*args)


class ActiveModifierObserver(object):
  optionals = [
    'name', 'ability_level', 'stack_count', 'creation_time', 'duration',
    'caster', 'ability', 'armor', 'fade_time', 'channel_time',
    'portal_loop_appear', 'portal_loop_disappear', 'hero_loop_appear',
    'hero_loop_disappear', 'movement_speed', 'activity', 'damage'
  ]

  def __init__(self):
    self.reset()

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
        attrs[o] = getattr(pbmsg, o, None)

      vec = pbmsg.v_start
      attrs['v_start'] = (vec.x, vec.y, vec.z)

      vec = pbmsg.v_end
      attrs['v_end'] = (vec.x, vec.y, vec.z)

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
