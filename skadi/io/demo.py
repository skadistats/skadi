import importlib as il
import os
import snappy

__impl__ = 'skadi_ext' if os.environ.get('SKADI_EXT') else 'skadi'
io_util = il.import_module(__impl__ + '.io.util')

from skadi.io.util import Peek


COMPRESSED_MASK = 0b01110000
LEN_HEADER = 8
LEN_OFFSET = 4


def mk(*args):
    """
    Pass-through for DemoIO instantiation.

    """
    return DemoIO(*args)


class InvalidHeaderError(RuntimeError):
    pass


class DemoIO(object):
    """
    Demo files are structured simply at the top level. They all begin with a
    12-byte header:

        PBUFDEM\0
        [LE uint32: absolute byte position in file of game summary message]

    For the remainder of the file, the following pattern repeats terminally:

        1. kind (protobuf varint specifying kind of protobuf message)
        2. tick (protobuf varint specifying replay-time 'tick')
        3. size (protobuf varint specifying next serialized pb's size)
        4. [message: a binary string size #3 to be parsed with protobuf]

    All the protobuf messages at this level are in protobuf/demo.proto.

    This class wraps a python io, making the stream iterable until EOF. At
    each iteration, it yields (Peek (skadi.state.util), message), where
    message is the serialized (i.e. non-parsed) protobuf message.

    """

    def __init__(self, handle):
        """
        Initilize instance with regular python io.

        Note: This implementation makes no assumptions about the io. As a
        result, it does not 'seek,' nor does it expose such functionality.
        That is your responsibility, if you need it. Just be careful with
        shared io.

        Arguments:
        handle -- python io object

        """
        self.handle = handle

    def __iter__(self):
        """
        Iterate over (Peek (skadi.state.util), message) tuples in file.

        """
        while True:
            try:
                yield self.read()
            except EOFError:
                raise StopIteration()

    def bootstrap(self):
        """
        Read demo header and return absolute offset of 'game info' near EOF.

        Returns int value of game info offset in stream.

        """
        header = self.handle.read(LEN_HEADER)
        offset = self.handle.read(LEN_OFFSET)
        if header != 'PBUFDEM\0':
            raise InvalidHeaderError

        gio = bytearray(offset)

        return sum(gio[i] << (i * 8) for i in range(4))

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
            comp = bool(kind & COMPRESSED_MASK)
            kind = (kind & ~COMPRESSED_MASK) if comp else kind
            tick = io_util.read_varint(self.handle)
            size = io_util.read_varint(self.handle)
            message = self.handle.read(size)

            assert len(message) == size

            if comp:
                message = snappy.uncompress(message)
        except AssertionError:
            raise EOFError()

        return Peek(comp, kind, tick, size), message
