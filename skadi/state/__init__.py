import collections
import copy

from skadi.decoder import entity as dec_entity
from skadi.decoder import prop as dec_prop
from skadi.io import bitstream as bitstream_io


test_packet_entities = lambda m: m.cls is pb_n.CSVCMsg_PacketEntities


def derive_templates(recv_tables, st_ib, base):
  templates = copy.copy(base)

  for index, (cls, data) in st_ib.items.items():
    b_stream = bitstream_io.wrap(data)
    rt = recv_tables[cls]

    baseline = collections.OrderedDict()
    prop_list = dec_entity.read_prop_list(b_stream)
    for index in prop_list:
      prop = rt.props[index]
      k = '{0}.{1}'.format(prop.origin_dt, prop.var_name)
      baseline[k] = dec_prop.decode(b_stream, prop)

    templates[cls] = entity.Template(cls, rt, baseline)

  return templates


def derive_entities(meta, pb_pent, templates, entities):
  entities = copy.copy(entities)

  created, updated, deleted = dec_entity.read(
    bitstream_io.wrap(pb_pent.entity_data),
    pb_pent.updated_entries, pb_pent.is_delta,
    meta.class_bits, meta.recv_tables,
    entities
  )

  for spec, delta in created.items():
    i, cls, serial = spec
    entities[i] = entity.Instance(templates[str(cls)], delta=delta)

  for i, delta in updated.items():
    entities[i].apply(delta)

  for i in deleted:
    del entities[i]

  return entities
