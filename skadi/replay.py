  #demo_io.seek(dem.post_sync)
  # iter_d = iter(demo_io)

  # snapshot = {}

  # for pbmsg in iter_d:
  #   if isinstance(pbmsg, pb_d.CDemoFullPacket):
  #     data = pbmsg.packet.data
  #   elif isinstance(pbmsg, pb_d.CDemoPacket):
  #     data = pbmsg.data

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
