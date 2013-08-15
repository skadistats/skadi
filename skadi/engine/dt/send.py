import itertools

from skadi.engine.dt import prop


def parse(pbmsg):
  dt, props = pbmsg.net_table_name, []

  for p in pbmsg.props:
    attributes = {
      'var_name': p.var_name,
      'type': p.type,
      'flags': p.flags,
      'num_elements': p.num_elements,
      'num_bits': p.num_bits,
      'dt_name': p.dt_name,
      'priority': p.priority,
      'low_value': p.low_value,
      'high_value': p.high_value
    }
    props.append(prop.Prop(dt, attributes))

  # assign properties used for parsing array elements
  for i, p in enumerate(props):
    if p.type == prop.Type.Array:
      p.array_prop = props[i - 1]

  return SendTable(dt, props, pbmsg.is_end, pbmsg.needs_decoder)


class SendTable(object):
  def __init__(self, dt, props, is_end, needs_decoder):
    self.dt = dt
    self.props = list(props)
    self.is_end = is_end
    self.needs_decoder = needs_decoder

  def __repr__(self):
    cls = self.__class__.__name__
    lenprops = len(self.props)
    return '<{0} {1} ({2} props)>'.format(cls, self.dt, lenprops)

  @property
  def baseclass(self):
    p = next((p for p in self.filter(prop.test_baseclass)), None)
    return p.dt if p else None

  @property
  def exclusions(self):
    def describe_exclusion(p):
      return (p.dt_name, p.var_name)
    return map(describe_exclusion, filter(prop.test_exclude, self.props))

  @property
  def non_exclusion_props(self):
    return filter(prop.test_not_exclude, self.props)

  @property
  def dt_props(self):
    return filter(prop.test_data_table, self.non_exclusion_props)

  @property
  def non_dt_props(self):
    def test_eligible(p):
      return not prop.test_data_table(p)
    return filter(test_eligible, self.non_exclusion_props)
