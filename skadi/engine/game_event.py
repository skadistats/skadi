import collections as c


def humanize(game_event, game_event_list):
  _type, data = game_event
  name, keys = game_event_list[_type]

  attrs = c.OrderedDict()

  for i, (k_type, k_name) in enumerate(keys):
    attrs[k_name] = data[i]

  return name, attrs


def parse(pbmsg, game_event_list):
  _, keys = game_event_list[pbmsg.eventid]

  attrs = []

  for i, (k_type, k_name) in enumerate(keys):
    key = pbmsg.keys[i]
    if k_type == 1:
      value = key.val_string
    elif k_type == 2:
      value = key.val_float
    elif k_type == 3:
      value = key.val_long
    elif k_type == 4:
      value = key.val_short
    elif k_type == 5:
      value = key.val_byte
    elif k_type == 6:
      value = key.val_bool
    elif k_type == 7:
      value = key.val_uint64

    attrs.append(value)

  return pbmsg.eventid, attrs
