import importlib as il
import io
import os
import snappy

__impl__ = 'skadi_ext' if os.environ.get('SKADI_EXT') else 'skadi'
io_util = il.import_module(__impl__ + '.io.util')

from skadi.io.util import Peek


def mk(data, tick=0):
    """
    Given some data and an optional tick, return appropriate EmbedIO instance.

    Arguments:
    data -- binary string of data
    tick -- int indicating tick when this data originated

    """
    handle = io.BufferedReader(io.BytesIO(data))
    return EmbedIO(handle, tick=tick)


class EmbedIO(object):
    """
    Similar to DemoIO (skadi.io.demo), this class implements methods for easy
    iteration over *embedded* protobuf messages.

    Embedded protobuf messages are packed sequentially as binary data strings
    embedded in a 'data' (or similar) field in top-level protobuf messages.
    See demo.proto for an exhaustive list of these messages.

    Some examples of demo-level protobufs with embedded messages:

        CDemoSendTables: embeds CSVCMsg_CreateStringTable
        CDemoPacket: embeds CSVCMsg_PacketEntities, CSVCMsg_UpdateStringTable,
          CSVCMsg_UserMessage, CSVCMsg_GameEvent, and more...

    This list is not exhaustive, but many of the embedded 'svc' messages are
    defined in protobuf/netmessages.proto. More are elsewhere.

    """

    def __init__(self, handle, tick=0):
        """
        Initialize instance with python IO and descriptive tick.

        Since a set of embed messages comes from one top-level demo message,
        they effectively occur at the same tick. The tick argument provides
        context for which this embed occurred, and is used when Peek
        (skadi.state.util) instances are created by the instance.

        Arguments:
        handle -- python io object
        tick -- the int tick where this embed occurs

        """
        self.handle = handle
        self.tick = tick

    def __iter__(self):
        """
        Iterate over (Peek (skadi.state.util), message) tuples in embed io.

        """
        while True:
            try:
                yield self.read()
            except EOFError:
                raise StopIteration()

    def read(self):
        """
        Read next Peek and message from stream.

        If the message data was compressed with Google's snappy compression
        algorithm, the returned Peek will have a size value < len(message).
        (The returned message is decompressed for the caller.)

        Returns (Peek (skadi.state.util), message) tuple.

        """
        try:
            kind = io_util.read_varint(self.handle)
            size = io_util.read_varint(self.handle)
            message = self.handle.read(size)

            assert len(message) == size
        except AssertionError:
            raise EOFError()

        return Peek(False, kind, self.tick, size), message
