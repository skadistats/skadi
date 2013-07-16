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

