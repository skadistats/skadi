from skadi.decoder import recv_prop as dcdr_rcvprp
from skadi.state.util import Prop


def mk(*args):
    """
    Pass-through for DTDecoder instantiation.

    """
    return DTDecoder(*args)


class DTDecoder(object):
    """
    Decodes a type of data from the stream by private decoders.

    """

    @classmethod
    def mk_cached_decoder(cls, recv_prop):
        """
        Since there only really needs to be one one decoder per recv prop ever
        encountered, we can cache them for a few reasons. One: it's easy to
        gather statistics on how many recv props exist. Two: memory.

        Arguments:
        recv_prop -- a Prop (skadi.state.util)

        """
        try:
            cls.cache
        except AttributeError:
            cls.cache = dict()

        if recv_prop not in cls.cache:
            cls.cache[recv_prop] = dcdr_rcvprp.mk(recv_prop)

        return cls.cache[recv_prop]

    def __init__(self, recv_table):
        """
        Initialize instance to be used for DT decoding.

        Arguments:
        recv_table -- RecvTable (skadi.state.recv_table) the decoder decodes

        """
        self.recv_table = recv_table
        self.by_index = []
        self.by_recv_prop = dict()

        for recv_prop in recv_table:
            recv_prop_decoder = DTDecoder.mk_cached_decoder(recv_prop)
            self.by_index.append(recv_prop_decoder)
            self.by_recv_prop[recv_prop] = recv_prop_decoder

    def __iter__(self):
        """
        Yields (recv_prop, recv_prop_decoder) for each recv_prop in this DT.

        """
        for recv_prop, recv_prop_decoder in self.by_recv_prop.items():
            yield recv_prop, recv_prop_decoder

        raise StopIteration()

    def decode(self, stream, prop_list):
        """
        Uses prop_list to find corresponding (skadi.state.util) Prop entries,
        then collects the results of each calling each prop decoder.

        Arguments:
        stream -- a Stream (skadi.io.stream) from which to read
        prop_list -- an array of integer indexes into the recv table

        Returns a dict of (recv prop index, value) tuples from stream.

        """
        return dict([(i, self[i].decode(stream)) for i in prop_list])
