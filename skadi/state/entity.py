import pprint

class Template(object):
  def __init__(self, class_id, recv_table, baseline):
    self.class_id = class_id
    self.recv_table = recv_table
    self.baseline = baseline

  def __repr__(self):
    return '{0} ({1} props)'.format(self.recv_table.dt, len(self.baseline))

class Instance(object):
  native_attrs = ('template', '_state')

  def __init__(self, _id, template, delta=None):
    self.id = _id
    self.template = template
    self._state = template.baseline.copy()
    if delta:
      self.apply(delta)

  def __iter__(self):
    return iter(self._state.items())

  def __repr__(self):
    dt, state = self.template.recv_table.dt, self._state
    return '<Instance dt: {0}, state:{1}>'.format(dt, state)

  def get(self, name):
    return self._state[name]

  def set(self, name, value):
    self._state[name] = value

  def apply(self, delta):
    [self.set(n, v) for n,v in delta.items()]
