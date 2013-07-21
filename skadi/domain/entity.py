class Template(object):
  def __init__(self, class_id, recv_table, baseline):
    self.class_id = class_id
    self.recv_table = recv_table
    self.baseline = baseline

  def __repr__(self):
    return '{0} ({1} props)'.format(self.recv_table.dt, len(self.baseline))

class Instance(object):
  def __init__(self, _id, template, delta=None):
    self.id = _id
    self.template = template
    self.state = template.baseline.copy() if template else {}
    if delta:
      self.apply(delta)

  def __iter__(self):
    return iter(self.state.items())

  def __repr__(self):
    dt, state = self.template.recv_table.dt, self.state
    return '<Instance dt: {0}, state:{1}>'.format(dt, state)

  def apply(self, delta):
    for name, value in delta.items():
      self.state[name] = value
