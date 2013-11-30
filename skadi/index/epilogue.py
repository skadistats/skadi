import importlib as il
import os

__impl__ = 'skadi_ext' if os.environ.get('SKADI_EXT') else 'skadi'
ndx_gnrc = il.import_module(__impl__ + '.index.generic')

from protobuf.impl import demo_pb2 as pb_d


def mk(io_demo):
    """
    Process a specialized 'demo' IO wrapper into an EpilogueIndex.

    This index is terminal: it reads to end of file.

    Arguments:
    io_demo -- DemoIO (skadi.io.demo) wrapping a file stream

    """
    entries = []
    iter_io = iter(io_demo)

    return EpilogueIndex(list(iter_io))


class EpilogueIndex(ndx_gnrc.Index):
    """
    Facilitates constant-time, expressive fetching of 'dem' messages at end of
    match. These messages follow a single CDemoStop (protobuf.impl.demo_pb2)
    message toward the end of the replay.

    FIXME: Make this more functional, ex. 'match_id' property, etc.

    """

    def __init__(self, entries):
        """
        Initialize instance of index.

        Argument:
        entries -- list of (peek, message) to index

        """
        super(EpilogueIndex, self).__init__(entries)

    @property
    def dem_file_info(self):
        """
        Returns (peek, message) for 'file info.'

        """
        return self.find_kind(pb_d.DEM_FileInfo)
