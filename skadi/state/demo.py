import itertools

from skadi import enum

class Class(object):
  def __init__(self, _id, name, dt):
    self.id = _id
    self.dt = dt
    self.name = name

  def __repr__(self):
    _id = self.id
    dtn = self.dt
    name = self.name
    return "<Class {0} '{1}' ({2})>".format(_id, name, dtn)

class GameEvent(object):
  def __init__(self, _id, name, keys):
    self.id = _id
    self.name = name
    self.keys = keys

  def __repr__(self):
    _id, n= self.id, self.name
    lenkeys = len(self.keys)
    return "<GameEvent {0} '{1}' ({2} keys)>".format(_id, n, lenkeys)

class String(object):
  def __init__(self, name, data):
    self.name = name
    self.data = data

  def __repr__(self):
    n, d = self.name, self.data
    return "<String '{0}' ({1} bytes)>".format(n, d)

class StringTable(object):
  def __init__(self, name, flags, items, items_clientside):
    self.name = name
    self.items = items
    self.items_clientside = items_clientside
    self.flags = flags

  def __repr__(self):
    n, f = self.name, hex(int(self.flags))
    lenitems = len(self.items)
    lenitemsc = len(self.items_clientside)
    _repr = "<StringTable '{0}' f:{1} ({2} items, {3} items clientside)"
    return _repr.format(n, f, lenitems, lenitemsc)

test_collapsible = lambda prop: prop.flags & Flag.Collapsible

class Flattener(object):
  def __init__(self, demo):
    self.demo = demo

  def flatten(self, st):
    props = self._build(st, [], self._aggregate_exclusions(st))
    return RecvTable.construct(st.dt, props)

  def _build(self, st, onto, excl):
    non_dt_props = self._compile(st, onto, excl)

    for prop in non_dt_props:
      onto.append(prop)

    return onto

  def _compile(self, st, onto, excl, collapsed=None):
    collapsed = collapsed or []

    def test_excluded(prop):
      return (st.dt, prop.var_name) not in excl

    for prop in st.dt_props:
      if test_data_table(prop) and test_excluded(prop):
        _st = self.demo.send_tables[prop.dt_name]
        if test_collapsible(prop):
          collapsed += self._compile(_st, onto, excl, collapsed)
        else:
          self._build(_st, onto, excl)

    return collapsed + filter(test_excluded, st.non_dt_props)

  def _aggregate_exclusions(self, st):
    def recurse(_dt_prop):
      st = self.demo.send_tables[_dt_prop.dt_name]
      return self._aggregate_exclusions(st)

    inherited = map(recurse, st.dt_props)

    return st.exclusions + list(itertools.chain(*inherited))

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

test_exclude = lambda prop: prop.flags & Flag.Exclude
test_not_exclude = lambda prop: prop.flags ^ Flag.Exclude
test_inside_array = lambda prop: prop.flags & Flag.InsideArray
test_data_table = lambda prop: prop.type == Type.DataTable
test_baseclass = lambda prop: prop.name == 'baseclass'

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
