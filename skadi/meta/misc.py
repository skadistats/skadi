import sys


def parse(pbmsg, cls):
  impl = getattr(sys.modules[__name__], cls)
  return impl({v:getattr(pbmsg,v) for v in impl.DELEGATED})


class GenericStateContainer(object):
  def __init__(self, attributes):
    self._attributes = attributes

  def __getitem__(self, key):
    if key in self._attributes:
      return self._attributes[key]

    raise KeyError('unknown attribute {0}'.format(key))


class FileHeader(GenericStateContainer):
  DELEGATED = (
    'demo_file_stamp', 'network_protocol', 'server_name', 'client_name',
    'map_name', 'game_directory', 'fullpackets_version'
  )

  def __init__(self, attributes):
    super(FileHeader, self).__init__(attributes)


class SetView(GenericStateContainer):
  DELEGATED = ('entity_index',)

  def __init__(self, attributes):
    super(SetView, self).__init__(attributes)


class ServerInfo(GenericStateContainer):
  DELEGATED = (
    'protocol', 'server_count', 'is_dedicated', 'is_hltv',
    'c_os', 'map_crc', 'client_crc', 'string_table_crc',
    'max_clients', 'max_classes', 'player_slot',
    'tick_interval', 'game_dir', 'map_name', 'sky_name',
    'host_name'
  )

  def __init__(self, attributes):
    super(ServerInfo, self).__init__(attributes)


class VoiceInit(GenericStateContainer):
  DELEGATED = ('quality', 'codec')

  def __init__(self, attributes):
    super(VoiceInit, self).__init__(attributes)
