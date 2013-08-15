from skadi.engine.dt import prop as dt_prop


def construct(dt, props):
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
      is_co = (pr == 64 and (p.flags & dt_prop.Flag.ChangesOften))

      if is_co or p.priority == pr:
        rt = rt.swap(rt.props[hole], p)
        hole += 1
        p_offset += 1
      cursor += 1

  return rt


class RecvTable(object):
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
