import bitstring
import math
import sys

from skadi import enum
from skadi.domain import dt as d_dt

PVS = enum(Enter = 0x01, Leave = 0x02, Delete = 0x04)
TYPE_EXCL = ('DataTable')
BY_TYPE = {v:k for k,v in d_dt.Type.tuples.items() if k not in TYPE_EXCL}

def read(io, count, delta, cb, ci, rt, ent):
  create, update, delete = {}, {}, []
  index, i = -1, 0

  while i < count:
    index, flags = read_header(io, index)
    if flags & PVS.Enter:
      cls, serial, pl = io.read(cb), io.read(10), read_prop_list(io)
      create[(index, cls, serial)] = read_props(io, pl, rt[ci[cls].dt])
    elif flags & (PVS.Leave | PVS.Delete):
      delete.append(index)
    else:
      pl = read_prop_list(io)
      _rt = ent[index].template.recv_table
      update[index] = read_props(io, pl, _rt)
    i += 1

  while delta and io.read(1):
    index = io.read(11)

  return create, update, delete

def read_header(io, base_index):
  try:
    index = io.read(6)
    if index & 0x30:
      a = (index >> 0x04) & 0x03
      b = 16 if a == 0x03 else 0
      index = io.read(4 * a + b) << 4 | (index & 0x0f)

    flags = 0
    if not io.read(1):
      if io.read(1):
        flags |= PVS.Enter
    else:
      flags |= PVS.Leave
      if io.read(1):
        flags |= PVS.Delete
  except IndexError:
    raise ReadError('unable to read entity header')

  return base_index + index + 1, flags

def read_prop_list(io):
  pl, cursor = [], -1
  while True:
    consecutive = io.read(1)
    if consecutive:
      cursor += 1
    else:
      offset = io.read_varint_35()
      if offset == 0x3fff:
        return pl
      else:
        cursor += offset + 1
    pl.append(cursor)

def read_props(io, prop_list, recv_table):
  delta = {}

  for prop_index in prop_list:
    prop = recv_table.props[prop_index]
    key = '{0}.{1}'.format(prop.origin_dt, prop.var_name)
    delta[key] = read_prop(io, prop)

  return delta

def read_prop(io, prop):
  fn_reader = '_read_{0}'.format(BY_TYPE[prop.type])
  return getattr(sys.modules[__name__], fn_reader)(io, prop)

def _read_Int(io, prop):
  if prop.flags & d_dt.Flag.EncodedAgainstTickcount:
    if prop.flags & d_dt.Flag.Unsigned:
      return io.read_varint_35()
    else:
      value = io.read_varint_35()
      return (-(value & 1)) ^ (value >> 1)

  value = io.read(prop.num_bits)
  l = 0x80000000 >> (32 - prop.num_bits)
  r = (prop.flags & d_dt.Flag.Unsigned) - 1

  return (value ^ (l & r)) - (l & r)

def _read_Float(io, prop):
  if prop.flags & d_dt.Flag.Coord:
    integer = io.read(1)
    fraction = io.read(1)

    if not integer and not fraction:
      return 0.0

    negate = io.read(1)

    if integer:
      integer = io.read(0x0e) + 1

    if fraction:
      fraction = io.read(5)

    value = 0.03125 * fraction
    value += integer

    if negate:
      value *= -1

    return value
  elif prop.flags & d_dt.Flag.CoordMP:
    raise NotImplementedError('! CoordMP')
  elif prop.flags & d_dt.Flag.CoordMPLowPrecision:
    raise NotImplementedError('! CoordMPLowPrecision')
  elif prop.flags & d_dt.Flag.CoordMPIntegral:
    raise NotImplementedError('! CoordMPIntegral')
  elif prop.flags & d_dt.Flag.NoScale:
    bit_array = bitstring.BitArray(uint=io.read(32), length=32)
    return bit_array.float
  elif prop.flags & d_dt.Flag.Normal:
    sign = io.read(1)
    bit_array = bitstring.BitArray(uint=io.read(11), length=32)

    value = bit_array.float
    if (bit_array >> 31):
      value += 4.2949673e9
    value *= 4.885197850512946e-4
    if sign:
      value *= -1

    return value
  elif prop.flags & d_dt.Flag.CellCoord:
    value = io.read(prop.num_bits)
    return value + 0.03125 * io.read(5)
  elif prop.flags & d_dt.Flag.CellCoordLowPrecision:
    raise NotImplementedError('! CellCoordLowPrecision')
  elif prop.flags & d_dt.Flag.CellCoordIntegral:
    value = io.read(prop.num_bits)
    if value >> 31:
      value += 4.2949673e9 # wat, edith?
    return float(value)

  dividend = io.read(prop.num_bits);
  divisor = (1 << prop.num_bits) - 1;

  f = float(dividend) / divisor
  r = prop.high_value - prop.low_value
  return f * r + prop.low_value;

def _read_Vector(io, prop):
  x = _read_Float(io, prop)
  y = _read_Float(io, prop)

  if prop.flags & d_dt.Flag.Normal:
    f = x * x + y * y
    z = 0 if (f <= 1) else math.sqrt(1 - f)

    sign = io.read(1)
    if sign:
      z *= -1
  else:
    z = _read_Float(io, prop)

  return x, y, z

def _read_VectorXY(io, prop):
  x = _read_Float(io, prop)
  y = _read_Float(io, prop)
  return x, y

def _read_String(io, prop):
  length = io.read(9)
  return io.read_string(length)

def _read_Array(io, prop):
  n, bits = prop.num_elements, 0
  while n:
    bits += 1
    n >>= 1

  count, i, elements = io.read(bits), 0, []
  while i < count:
    elements.append(read_prop(io, prop.array_prop))
    i += 1

  return elements

def _read_Int64(io, prop):
  if prop.flags & d_dt.Flag.EncodedAgainstTickcount:
    raise NotImplementedError('int64 cant be encoded against tickcount')

  negate = False
  second_bits = prop.num_bits - 32

  if not (prop.flags & d_dt.Flag.Unsigned):
    second_bits -= 1
    if io.read(1):
      negate = True

  a = io.read(32)
  b = io.read(second_bits)

  value = (a << 32) | b
  if negate:
    value *= -1

  return value