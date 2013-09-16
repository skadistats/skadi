from skadi.engine.dt import prop as dt_prop


def construct(dt, props):
  return _construct(dt, props)

cdef _construct(object dt, object props):
  cdef RecvTable rt
  cdef object properties, p

  rt = RecvTable(dt, props)
  priorities = set([64])

  for p in rt.props:
    priorities.add(p.priority)

  priorities = sorted(list(priorities))
  cdef int p_offset = 0

  cdef int pr, hole, cursor, proplen
  cdef object is_co

  for pr in priorities:
    proplen = len(rt.props)
    hole = p_offset
    cursor = p_offset

    while cursor < proplen:
      p = rt.props[cursor]
      is_co = (pr == 64 and (p.flags & dt_prop.Flag.ChangesOften))

      if is_co or p.priority == pr:
        rt.props[hole], rt.props[cursor] = rt.props[cursor], rt.props[hole]
        hole += 1
        p_offset += 1
      cursor += 1

  return rt


cdef class RecvTable(object):
  cdef public object dt, props

  def __init__(self, dt, props):
    self.dt = dt
    self.props = props

  def __repr__(self):
    cls = self.__class__.__name__
    lenprops = len(self.props)
    return '<{0} {1} ({2} props)>'.format(cls, self.dt, lenprops)