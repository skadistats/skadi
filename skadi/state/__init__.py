import collections
import copy

from skadi.decoder import entity as d_entity
from skadi.decoder import prop as d_prop
from skadi.io import bitstream as bitstream_io
from skadi.io.protobuf import packet as packet_io
from skadi.protoc import netmessages_pb2 as pb_n


test_packet_entities = lambda m: m.cls is pb_n.CSVCMsg_PacketEntities


def derive_string_tables(pb_string_tables, base):
  string_tables = collections.OrderedDict()

  def pb_string_tables_find(pb_stt, name):
    gen = (pb_st for pb_st in pb_stt if pb_st.table_name == name)
    return next(gen, None)

  for st_name, st in base.items():
    pb_st = pb_string_tables_find(pb_string_tables.tables, st_name)
    if pb_st:
      strings = [(pb_s.str, pb_s.data) for pb_s in pb_st.items]
      string_tables[st_name] = st.merge(strings)
    else:
      string_tables[st_name] = st

  return string_tables


def derive_templates(class_info, recv_tables, st_ib, base):
  templates = copy.copy(base)

  for cls, string in st_ib.items.items():
    b_stream = bitstream_io.wrap(string.data)
    dt = class_info[int(cls)].dt
    rt = recv_tables[dt]

    baseline = collections.OrderedDict()
    prop_list = d_entity.read_prop_list(b_stream)
    for index in prop_list:
      prop = rt.props[index]
      fq_prop = '{0}.{1}'.format(prop.origin_dt, prop.var_name)
      baseline[fq_prop] = d_prop.decode(b_stream, prop)

    templates[cls] = entity.Template(cls, rt, baseline)

  return templates


def derive_entities(demo, pb_pent, templates, entities):
  entities = copy.copy(entities)

  created, updated, deleted = d_entity.read(
    bitstream_io.wrap(pb_pent.entity_data),
    pb_pent.updated_entries, pb_pent.is_delta,
    demo.class_bits, demo.class_info, demo.recv_tables,
    entities
  )

  for spec, delta in created.items():
    i, cls, serial = spec
    entities[i] = entity.Instance(i, templates[str(cls)], delta=delta)

  for i, delta in updated.items():
    dt = entities[i].template.recv_table.dt
    entities[i].apply(delta)

  for i in deleted:
    dt = entities[i].template.recv_table.dt
    del entities[i]

  return entities
