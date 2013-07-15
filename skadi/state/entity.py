from skadi.io import property as io_pr

class Instance(object):
  native_attrs = ('template', '_state')

  def __init__(_id, template, delta=None):
    self.id = _id
    self.template = template
    self._state = template.baseline.deepcopy()
    if delta:
      self.apply(delta)

  def __getattr__(self, name):
    prop = next((p for p in self.entity.props if p.var_name == name), None)
    if not prop or name in Snapshot.native_attrs:
      return super(Snapshot, self).__getattr__(name)
    return self._state[name]

  def __setattr__(self, name, value):
    prop = next((p for p in self.entity.props if p.var_name == name), None)
    if not prop or name in Snapshot.native_attrs:
      super(Snapshot, self).__setattr__(name, value)
    self._state[name] = value

  def apply(delta):
    [setattr(copy, n, v) for n,v in delta.items()]

class Template(object):
  def __init__(recv_table, baseline):
    self.recv_table = recv_table
    self.baseline = baseline
