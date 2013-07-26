from skadi import enum


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

  def __getattr__(self, name):
    if name in Prop.DELEGATED:
      return self._attributes[name]
    else:
      return object.__getattr__(self, name)

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
