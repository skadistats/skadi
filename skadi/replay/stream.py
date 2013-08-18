import copy
import io

from skadi.engine import bitstream as bs
from skadi.engine.unpacker import entity as uent
from skadi.engine.unpacker import string_table as ust
from skadi.engine.unpacker.entity import PVS
from skadi.index import demo as di
from skadi.index import packet as pi
from skadi.protoc import netmessages_pb2 as pb_n


def construct(*args):
  stream = Stream(*args)
  stream.bootstrap()
  return stream


class Stream(object):
  def __init__(self, io, index, tick, cb, rt, string_tables, entities):
    self.io = io
    self.index = index
    self.tick = None
    self.class_bits = cb
    self.recv_tables = rt
    self.string_tables = copy.deepcopy(string_tables)
    self.entities = copy.deepcopy(entities)
    self._bootstrap_tick = tick

  def __iter__(self):
    def _apply():
      peek = next(self.peeks)
      return self.apply(peek)

    return iter(_apply, None)

  def bootstrap(self):
    full_packet_tick = self.index.locate_full_tick(self._bootstrap_tick)
    peeks = self.index.lookup_between(full_packet_tick, self.index.ticks[-1])

    for peek in peeks:
      self.apply(peek)
      if self._bootstrap_tick == peek.tick:
        break

    self.peeks = peeks # peeks is a generator, so will continue from here

  def apply(self, peek):
    self.tick = peek.tick
    st, cb, rt = self.string_tables, self.class_bits, self.recv_tables
    st_ib = st['instancebaseline']

    packet = di.read(self.io, peek)
    p_io = io.BufferedReader(io.BytesIO(packet.data))
    index = pi.index(p_io)

    csvc_update_string_table_peeks = \
      index.find_all(pb_n.CSVCMsg_UpdateStringTable)
    all_csvc_update_string_table = \
      [pi.read(p_io, p) for p in csvc_update_string_table_peeks]

    for pbmsg in all_csvc_update_string_table:
      key = self.string_tables.keys()[pbmsg.table_id]
      _st = self.string_tables[key]

      bitstream = bs.construct(pbmsg.string_data)
      ne = pbmsg.num_changed_entries
      eb, sf, sb = _st.entry_bits, _st.size_fixed, _st.size_bits

      for entry in ust.unpack(bitstream, ne, eb, sf, sb):
        _st.update(entry)

    csvc_packet_entities = \
      pi.read(p_io, index.find(pb_n.CSVCMsg_PacketEntities))

    bitstream = bs.construct(csvc_packet_entities.entity_data)
    ct = csvc_packet_entities.updated_entries

    unpacker = uent.unpack(bitstream, -1, ct, False, cb, rt, self.entities)

    for mode, index, context in unpacker:
      if mode & PVS.Entering:
        cls, serial, diff = context

        state = st_ib.getbaseline(cls, cb, rt)
        state.update(diff)

        self.entities[index] = (cls, serial, state)
      elif mode & PVS.Deleting:
        del self.entities[index]
      elif mode ^ PVS.Leaving:
        cls, serial, state = self.entities[index]
        state.update(context)

        self.entities[index] = (cls, serial, state)

    return peek.tick, self.string_tables, self.entities
