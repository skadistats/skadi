from __future__ import absolute_import

import io

from skadi.io import protobuf
from skadi.model import dt

BY_CLASS = {
    'CDemoFileHeader': 'parse_file_header',
    'CDemoPacket': 'parse_packet',
    'CDemoSendTables': 'parse_send_tables',
    'CDemoClassInfo': 'parse_class_info',
    'CDemoStringTables': 'parse_string_tables'
}

def parse_file_header(world, m):
    print '  file header'

    world.meta['server_name'] = m.server_name
    world.meta['network_protocol'] = m.network_protocol
    world.meta['fullpackets_version'] = m.fullpackets_version

def parse_packet(world, m):
    print '  generic packet'

    relevant = (
        'CSVCMsg_ServerInfo', 'CSVCMsg_VoiceInit', 'CSVCMsg_GameEventList',
        'CSVCMsg_SetView'
    )

    extraneous = (
        'CSVCMsg_CreateStringTable', 'CNETMsg_Tick', 'CNETMsg_SetConVar',
        'CNETMsg_SignonState', 'CSVCMsg_ClassInfo', 'CSVCMsg_SetView'
    )

    packet_io = protobuf.PacketIO.wrapping(m.data)
    for _m in iter(packet_io):
        cls = _m.__class__.__name__
        if cls in relevant:
            print '     {0}'.format(cls)
            if cls == 'CSVCMsg_ServerInfo':
                pass
            elif cls == 'CSVCMsg_VoiceInit':
                pass
            elif cls == 'CSVCMsg_GameEventList':
                pass
            elif cls == 'CSVCMsg_SetView':
                pass
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

def parse_string_tables(world, m):
    print '  string tables'
