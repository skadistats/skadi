import itertools

from skadi.meta import prop


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

  return SendTable(dt, props, pbmsg.is_end, pbmsg.needs_decoder)

def flatten(send_table, send_tables):
  return Flattener(send_tables).flatten(send_table)

def construct(cls, dt, props):
  rt = RecvTable(dt, props)
  priorities = [64]

  for p in rt.props:
    gen = (pr for pr in priorities if pr == p.priority)
    if not next(gen, None):
      priorities.append(p.priority)

  priorities, p_offset = sorted(priorities), 0

  for pr in priorities:
    proplen = len(rt.props)
    hole = p_offset
    cursor = p_offset

    while cursor < proplen:
      p = rt.props[cursor]
      is_co = (pr == 64 and (p.flags & prop.Flag.ChangesOften))

      if is_co or p.priority == pr:
        rt = rt.swap(rt.props[hole], p)
        hole += 1
        p_offset += 1
      cursor += 1

  return rt


class Flattener(object):
  def __init__(self, send_tables):
    self.send_tables = send_tables

  def flatten(self, st):
    return self._build(st, [], self._aggregate_exclusions(st))

  def _build(self, st, onto, excl):
    [onto.append(p) for p in self._compile(st, onto, excl)]
    return onto

  def _compile(self, st, onto, excl, collapsed=None):
    collapsed = collapsed or []

    def test_excluded(p):
      return (st.dt, p.var_name) not in excl

    for p in st.dt_props:
      if prop.test_data_table(p) and test_excluded(p):
        _st = self.send_tables[p.dt_name]
        if prop.test_collapsible(p):
          collapsed += self._compile(_st, onto, excl, collapsed)
        else:
          self._build(_st, onto, excl)

    return collapsed + filter(test_excluded, st.non_dt_props)

  def _aggregate_exclusions(self, st):
    def recurse(_dt_prop):
      st = self.send_tables[_dt_prop.dt_name]
      return self._aggregate_exclusions(st)

    inherited = map(recurse, st.dt_props)

    return st.exclusions + list(itertools.chain(*inherited))


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
      data_table = prop.test_data_table(p)
      inside_array = prop.test_inside_array(p)
      return not data_table and not inside_array

    return filter(test_eligible, self.non_exclusion_props)
