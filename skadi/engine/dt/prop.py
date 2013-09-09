from skadi import enum
from skadi.engine.dt.consts import Flag, Type

test_baseclass = lambda prop: prop.name == 'baseclass'
test_collapsible = lambda prop: prop.flags & Flag.Collapsible
test_data_table = lambda prop: prop.type == Type.DataTable
test_exclude = lambda prop: prop.flags & Flag.Exclude
test_inside_array = lambda prop: prop.flags & Flag.InsideArray
test_not_exclude = lambda prop: prop.flags ^ Flag.Exclude

def construct(*args):
  return Prop(*args)


class Prop(object):
  DELEGATED = (
    'var_name', 'type',    'flags',    'num_elements',
    'num_bits', 'dt_name', 'priority', 'low_value',
    'high_value'
  )

  def __init__(self, origin_dt, attributes):
    self.origin_dt = origin_dt
    for name in self.DELEGATED:
      setattr(self, name, attributes[name])

  def __repr__(self):
    odt, vn, t = self.origin_dt, self.var_name, self._type()
    f = ','.join(self._flags()) if self.flags else '-'
    p = self.priority if self.priority < 128 else 128
    terse = ('num_bits', 'num_elements', 'dt_name')
    b, e, dt = map(lambda i: getattr(self, i) or '-', terse)

    _repr = "<Prop ({0},{1}) t:{2} f:{3} p:{4} b:{5} e:{6} o:{7}>"
    return _repr.format(odt, vn, t, f, p, b, e, dt)

  def _type(self):
    for k, v in Type.tuples.items():
      if self.type == v:
        return k.lower()

  def _flags(self):
    named_flags = []
    for k, v in Flag.tuples.items():
      if self.flags & v:
        named_flags.append(k.lower())
    return named_flags
