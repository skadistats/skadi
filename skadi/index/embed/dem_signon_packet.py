import importlib as il
import os

__impl__ = 'skadi_ext' if os.environ.get('SKADI_EXT') else 'skadi'
ndx_gnrc = il.import_module(__impl__ + '.index.generic')

from protobuf.impl import netmessages_pb2 as pb_n


def mk(*args):
    """
    Pass-through for DemSignonPacketIndex instantiation.

    """
    return DemSignonPacketIndex(*args)


class DemSignonPacketIndex(ndx_gnrc.Index):
    """
    Facilitates constant-time, expressive fetching of 'svc' messages embedded
    in a CDemoPacket (protobuf.impl.demo_pb2) 'data' field.

    Note: The only difference between a 'signon packet' and a regular 'packet'
    is that the 'kind' varint in the protobuf message header is of type
    pb_d.DEM_SignonPacket. These 'signon' packets contain different types of
    embedded 'svc' messages specific to signing onto the game server.

    """

    def __init__(self, entries):
        """
        Initialize instance of index.

        Argument:
        entries -- list of (peek, message) to index

        """
        super(DemSignonPacketIndex, self).__init__(entries)

    @property
    def svc_game_event_list(self):
        """
        Returns (peek, message) for 'game event list.'

        """
        return self.find_kind(pb_n.svc_GameEventList)

    @property
    def svc_server_info(self):
        """
        Returns (peek, message) for 'server info.'

        """
        return self.find_kind(pb_n.svc_ServerInfo)

    @property
    def svc_voice_init(self):
        """
        Returns (peek, message) for 'voice init.'

        """
        return self.find_kind(pb_n.svc_VoiceInit)

    @property
    def all_svc_create_string_table(self):
        """
        Returns list of (peek, message) for 'create string table.'

        """
        return self.find_all_kind(pb_n.svc_CreateStringTable)
