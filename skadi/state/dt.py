from skadi import enum
from skadi.state import *

test_baseclass = lambda prop: prop.name == 'baseclass'
test_collapsible = lambda prop: prop.flags & Flag.Collapsible
test_data_table = lambda prop: prop.type == Type.DataTable
test_exclude = lambda prop: prop.flags & Flag.Exclude
test_inside_array = lambda prop: prop.flags & Flag.InsideArray
test_not_exclude = lambda prop: prop.flags ^ Flag.Exclude

Flag = enum(
  Unsigned              = 1 <<  0, Coord                   = 1 <<  1,
  NoScale               = 1 <<  2, RoundDown               = 1 <<  3,
  RoundUp               = 1 <<  4, Normal                  = 1 <<  5,
  Exclude               = 1 <<  6, XYZE                    = 1 <<  7,
  InsideArray           = 1 <<  8, ProxyAlways             = 1 <<  9,
  VectorElem            = 1 << 10, Collapsible             = 1 << 11,
  CoordMP               = 1 << 12, CoordMPLowPrecision     = 1 << 13,
  CoordMPIntegral       = 1 << 14, CellCoord               = 1 << 15,
  CellCoordLowPrecision = 1 << 16, CellCoordIntegral       = 1 << 17,
  ChangesOften          = 1 << 18, EncodedAgainstTickcount = 1 << 19
)

Type = enum(
  Int       = 0, Float  = 1, Vector = 2,
  VectorXY  = 3, String = 4, Array  = 5,
  DataTable = 6, Int64  = 7
)

class Prop(object):
  DELEGATED = (
    'var_name', 'type',    'flags',    'num_elements',
    'num_bits', 'dt_name', 'priority', 'low_value',
    'high_value'
  )

  def __init__(self, origin_dt, attributes):
    self.origin_dt = origin_dt
    self._attributes = attributes

  def __getattribute__(self, name):
    if name in Prop.DELEGATED:
      return self._attributes[name]
    else:
      return object.__getattribute__(self, name)

  def __repr__(self):
    odt, vn, t = self.origin_dt, self.var_name, self._type()
    f = ','.join(self._flags()) if self.flags else '-'
    p = self.priority if self.priority < 128 else 128
    terse = ('num_bits', 'num_elements', 'dt_name')
    b, e, dt = map(lambda i: getattr(self, i) or '-', terse)

    _repr = "<Prop {0}.{1} t:{2} f:{3} p:{4} b:{5} e:{6} o:{7}>"
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

class Table(object):
  def __init__(self, dt, props):
    self.dt = dt
    self.props = list(props)

  def __repr__(self):
    cls = self.__class__.__name__
    lenprops = len(self.props)
    return '<{0} {1} ({2} props)>'.format(cls, self.dt, lenprops)

class SendTable(Table):
  @classmethod
  def construct(cls, message):
    dt, props = message.net_table_name, []

    for prop in message.props:
      attributes = {
        'var_name': prop.var_name,
        'type': prop.type,
        'flags': prop.flags,
        'num_elements': prop.num_elements,
        'num_bits': prop.num_bits,
        'dt_name': prop.dt_name,
        'priority': prop.priority,
        'low_value': prop.low_value,
        'high_value': prop.high_value
      }
      props.append(Prop(dt, attributes))

    return SendTable(dt, props, message.is_end, message.needs_decoder)

  def __init__(self, dt, props, is_end, needs_decoder):
    super(SendTable, self).__init__(dt, props)
    self.is_end = is_end
    self.needs_decoder = needs_decoder

  @property
  def baseclass(self):
    prop = next((prop for prop in self.filter(test_baseclass)), None)
    return prop.dt if prop else None

  @property
  def exclusions(self):
    def describe_exclusion(prop):
      return (prop.dt_name, prop.var_name)
    return map(describe_exclusion, filter(test_exclude, self.props))

  @property
  def non_exclusion_props(self):
    return filter(test_not_exclude, self.props)

  @property
  def dt_props(self):
    return filter(test_data_table, self.non_exclusion_props)

  @property
  def non_dt_props(self):
    def test_eligible(prop):
      return not test_data_table(prop) and not test_inside_array(prop)
    return filter(test_eligible, self.non_exclusion_props)

class RecvTable(Table):
  @classmethod
  def construct(cls, dt, props):
    rt = RecvTable(dt, props)
    priorities = [64]

    for prop in rt.props:
      gen = (pr for pr in priorities if pr == prop.priority)
      if not next(gen, None):
        priorities.append(prop.priority)

    priorities, prop_offset = sorted(priorities), 0

    for pr in priorities:
      proplen = len(rt.props)
      hole = prop_offset
      cursor = prop_offset

      while cursor < proplen:
        prop = rt.props[cursor]
        is_co_prop = (pr == 64 and (prop.flags & Flag.ChangesOften))

        if is_co_prop or prop.priority == pr:
          rt = rt.swap(rt.props[hole], prop)
          hole += 1
          prop_offset += 1
        cursor += 1

    return rt

  def swap(self, first, second):
    l = list(self.props)
    i = l.index(first)
    j = l.index(second)
    l[i], l[j] = l[j], l[i]
    return RecvTable(self.dt, l)
