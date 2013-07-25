import itertools

from skadi.meta import prop


def flatten(send_table, send_tables):
  flattener = Flattener(send_tables)
  return RecvTable.construct(send_table.dt, flattener.flatten(send_table))


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


class RecvTable(object):
  @classmethod
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

  def __init__(self, dt, props):
    self.dt = dt
    self.props = props

  def __repr__(self):
    cls = self.__class__.__name__
    lenprops = len(self.props)
    return '<{0} {1} ({2} props)>'.format(cls, self.dt, lenprops)

  def swap(self, first, second):
    l = list(self.props)
    i = l.index(first)
    j = l.index(second)
    l[i], l[j] = l[j], l[i]
    return RecvTable(self.dt, l)
