from __future__ import absolute_import

import io

from skadi.io import protobuf
from skadi.model import dt
from skadi.model import state as s

BY_CLASS = {
    'CDemoFileHeader': 'parse_file_header',
    'CDemoPacket': 'parse_packet',
    'CDemoSendTables': 'parse_send_tables',
    'CDemoClassInfo': 'parse_class_info',
    'CDemoStringTables': 'parse_string_tables'
}

def parse_file_header(world, m):
    print '  file header'
    to_extract = (
        'demo_file_stamp', 'network_protocol', 'server_name', 'client_name',
        'map_name', 'game_directory', 'fullpackets_version'
    )
    for attr in to_extract:
        world.meta[attr] = getattr(m, attr)

def parse_packet(world, m):
    print '  packet'

    relevant = (
        'CSVCMsg_ServerInfo', 'CSVCMsg_VoiceInit', 'CSVCMsg_GameEventList',
        'CSVCMsg_SetView'
    )

    extraneous = (
        'CSVCMsg_CreateStringTable', 'CNETMsg_Tick', 'CNETMsg_SetConVar',
        'CNETMsg_SignonState', 'CSVCMsg_ClassInfo'
    )

    packet_io = protobuf.PacketIO.wrapping(m.data)
    for _m in iter(packet_io):
        cls = _m.__class__.__name__
        if cls in relevant:
            print '    {0}'.format(cls)
            if cls == 'CSVCMsg_ServerInfo':
                to_extract = (
                    'protocol', 'server_count', 'is_dedicated', 'is_hltv',
                    'c_os', 'map_crc', 'client_crc', 'string_table_crc',
                    'max_clients', 'max_classes', 'player_slot',
                    'tick_interval', 'game_dir', 'map_name', 'sky_name',
                    'host_name'
                )
                for attr in to_extract:
                    world.server_info[attr] = getattr(_m, attr)
            elif cls == 'CSVCMsg_VoiceInit':
                to_extract = ('quality', 'codec')
                for attr in to_extract:
                    world.voice_init[attr] = getattr(_m, attr)
            elif cls == 'CSVCMsg_GameEventList':
                for desc in _m.descriptors:
                    _id, name = desc.eventid, desc.name
                    keys = [(k.type, k.name) for k in desc.keys]
                    world.game_events[_id] = s.GameEvent(_id, name, keys)
            elif cls == 'CSVCMsg_SetView':
                world.set_view['entity_index'] = _m.entity_index
        elif cls not in extraneous:
            print '! unanticipated message type {0}'.format(cls)

def parse_send_tables(world, m):
    print '  send tables'
    packet_io = protobuf.PacketIO.wrapping(m.data)
    for svc_message in iter(packet_io):
        st = dt.SendTable.construct(svc_message)
        world.send_tables[st.dt] = st

def parse_class_info(world, m):
    print '  class info'
    for c in m.classes:
        _id, dt, name = c.class_id, c.table_name, c.network_name
        world.classes[c.class_id] = s.Class(_id, name, dt)

def parse_string_tables(world, m):
    print '  string tables'
    for t in m.tables:
        _ii, _iic = [], []
        for i in t.items:
            _ii.append(s.String(i.str, i.data))
        for i in t.items_clientside:
            _iic.append(s.String(i.str, i.data))
        name, flags = t.table_name, t.table_flags
        world.string_tables[name] = s.StringTable(name, flags, _ii, _iic)
