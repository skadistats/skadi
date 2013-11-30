import importlib as il
import os

__impl__ = 'skadi_ext' if os.environ.get('SKADI_EXT') else 'skadi'
ndx_gnrc = il.import_module(__impl__ + '.index.generic')

from protobuf.impl import netmessages_pb2 as pb_n


def mk(*args):
    """
    Pass-through for DemSendTableIndex instantiation.

    """
    return DemSendTableIndex(*args)


class DemSendTableIndex(ndx_gnrc.Index):
    """
    Facilitates constant-time, expressive fetching of 'svc' messages embedded
    in a CDemoSendTable (protobuf.impl.demo_pb2) 'data' field.

    """

    def __init__(self, entries):
        """
        Initialize instance of index.

        Argument:
        entries -- list of (peek, message) to index

        """
        super(DemSendTableIndex, self).__init__(entries)

    @property
    def all_svc_send_table(self):
        """
        Returns list of (peek, message) for 'send table.'

        """
        return self.find_all_kind(pb_n.svc_SendTable)
