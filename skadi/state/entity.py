class Template(object):
  def __init__(self, class_id, recv_table, baseline):
    self.class_id = class_id
    self.recv_table = recv_table
    self.baseline = baseline

  def __repr__(self):
    return '{0} ({1} props)'.format(self.recv_table.dt, len(self.baseline))


class Instance(object):
  def __init__(self, template, delta=None):
    self.template = template
    self._state = {}
    self._delta = delta or {}

  def __iter__(self):
    return iter(self.state.items())

  def __repr__(self):
    dt, state = self.template.recv_table.dt, self.state
    return '<Instance dt: {0}, state:{1}>'.format(dt, state)

  @property
  def state(self):
    state = self.template.baseline.copy()

    for p, value in self._delta.items():
      state[p] = value

    return state

  def apply(self, delta):
    for p, value in delta.items():
      self._delta[p] = value