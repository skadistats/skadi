import collections
import math
import sys

from skadi import enum
from skadi.decoder import prop as d_prop


PVS = enum(Enter = 0x01, Leave = 0x02, Delete = 0x04)


def read(io, count, delta, cb, rt, ent):
  create, update, delete = {}, {}, []
  index, i = -1, 0

  while i < count:
    index, flags = read_header(io, index)
    if flags & PVS.Enter:
      cls, serial, pl = io.read(cb), io.read(10), read_prop_list(io)
      create[(index, cls, serial)] = read_delta(io, pl, rt[str(cls)])
    elif flags & (PVS.Leave | PVS.Delete):
      delete.append(index)
    else:
      pl = read_prop_list(io)
      _rt = ent[index].template.recv_table
      update[index] = read_delta(io, pl, _rt)
    i += 1

  while delta and io.read(1):
    delete.append(io.read(11))

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

def read_delta(io, prop_list, recv_table):
  delta = {}

  for prop_index in prop_list:
    p = recv_table.props[prop_index]
    delta[p] = d_prop.decode(io, p)

  return delta
