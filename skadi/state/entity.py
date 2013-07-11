class Entity(object):
  def __init__(_id, recv_table):
    self.id = _id
    self.recv_table = recv_table
    self.reset()

  def reset(self):
    self._state = {prop.var_name:None for prop in self.recv_table.props}

  def summarize(self):
    return self._state.copy()

  def __getattr__(self, name):
    if name in self._state:
      return self._state[name]
    return super(Entity, self).__getattr__(name)

  def __setattr__(self, name, value):
    if name in self._state:
      self._state[name] = value
    super(Entity, self).__setattr__(name, value)