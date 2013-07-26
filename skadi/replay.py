import collections
import copy

from skadi.meta import string_table


def construct(demo, io):
  replay = Replay(demo, io)
  replay.tick = 0
  return replay


class Snapshot(object):
  def __init__(self, tick, user_messages, game_events, entities):
    self.tick = tick
    self.user_messages = user_messages
    self.game_events = game_events
    self.entities = entities


class Frame(object):
  def __init__(self, string_tables, snapshot=None):
    self.string_tables = string_tables
    self.snapshot = snapshot


class Replay(object):
  def __init__(self, demo, io):
    self.demo = demo
    self.io = io
    self.tick = 0
    self._cache = collections.OrderedDict()

  @property
  def snapshot(self):
    pass

  def _optimize(self, tick):
    string_tables = copy.deepcopy(self.demo.string_tables)

    for tick, offset in self.demo.full.items():
      string_tables = copy.deepcopy(string_tables)

      self.io.seek(offset)
      _, pb_full_packet = self.io.read()
      pb_string_tables = pb_full_packet.string_table

      for pb_string_table in pb_string_tables.tables:
        st = string_tables[pb_string_table.table_name]
        ii = []

        for pb_string in pb_string_table.items:
          string = string_table.String(pb_string.str, pb_string.data)
          ii.append(string)

        st.items = ii

      self._cache[tick] = Frame(string_tables)

  def rewind(self):
    self.tick = 0

  #demo_io.seek(dem.post_sync)
  # iter_d = iter(demo_io)

  # snapshot = {}

  # for pbmsg in iter_d:
  #   for _pbmsg in io_p.Packet.wrapping(data):
  #     if isinstance(_pbmsg, pb_n.CNETMsg_Tick):
  #       print 'tick {0}'.format(_pbmsg.tick)
  #     elif isinstance(_pbmsg, pb_n.CSVCMsg_UpdateStringTable):
  #       table_id = _pbmsg.table_id
  #       table_name = dem.string_tables.keys()[table_id]
  #       table = dem.string_tables[table_name]
  #       io_bs = io_b.Bitstream(_pbmsg.string_data)
  #       ii = d_string_table.decode(io_bs, table, _pbmsg.num_changed_entries)
  #       for name, data in ii:
  #         item = table[name]
  #         if item:
  #           item.data = data
  #         else:
  #           table.items.append(string_table.String(name, data))
  #       if table_name == 'instancebaseline':
  #         dem.generate_entity_templates()
  #     elif isinstance(_pbmsg, pb_n.CSVCMsg_PacketEntities):
  #       io = io_b.Bitstream(_pbmsg.entity_data)

  #       c, u, d = d_entity.read(
  #         io,
  #         _pbmsg.updated_entries, _pbmsg.is_delta,
  #         dem.class_bits, dem.class_info, dem.recv_tables,
  #         snapshot
  #       )

  #       templates = dem.templates      # entity templates (via baseline)

  #       # Creations
  #       for spec, delta in c.items():
  #         i, cls, serial = spec
  #         snapshot[i] = entity.Instance(i, templates[cls], delta=delta)
  #         print '  + {0} #{1}'.format(dem.class_info[cls].dt, str(i).ljust(4))
  #         print '    delta: {0}'.format(delta)

  #       # Updates
  #       for i, delta in u.items():
  #         dt = snapshot[i].template.recv_table.dt
  #         snapshot[i].apply(delta)
  #         print '  . {0} #{1}'.format(dt, str(i).ljust(4))
  #         print '    delta: {0}'.format(delta)

  #       # Deletions
  #       for i in d:
  #         dt = snapshot[i].template.recv_table.dt
  #         del snapshot[i]
  #         print '  - {0} #{1}'.format(dt, str(i).ljust(4))
