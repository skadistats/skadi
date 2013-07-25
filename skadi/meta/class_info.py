import collections


def parse(pbmsg):
  class_info = collections.OrderedDict()

  for c in pbmsg.classes:
    _id, dt, name = c.class_id, c.table_name, c.network_name
    class_info[c.class_id] = Class(_id, name, dt)

  return class_info


class ClassInfo(object):
  def __init__(self, classes):
    self.classes = classes


class Class(object):
  def __init__(self, _id, name, dt):
    self.id = _id
    self.dt = dt
    self.name = name

  def __repr__(self):
    _id = self.id
    dtn = self.dt
    name = self.name
    return "<Class {0} '{1}' ({2})>".format(_id, name, dtn)

