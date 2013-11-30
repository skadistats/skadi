from skadi.io import util
from skadi.state.util import Flag


def mk(*args):
    """
    Pass-through for ArrayDecoder instantiation.

    """
    return IntDecoder(*args)


class IntDecoder(object):
    """
    Decodes integers from a stream.

    """

    def __init__(self, prop):
        """
        Initialize instance to be used for int property decoding.

        Arguments:
        prop -- array Prop (skadi.state.util) this instance represents

        """
        self.prop = prop

        self.eat = prop.flags & Flag.EncodedAgainstTickcount
        self.unsigned = prop.flags & Flag.Unsigned
        self.bits = prop.bits

    def decode(self, stream):
        """
        Apparently decodes a signed integer.

        Arguments:
        stream -- a Stream (skadi.io.stream) from which to read

        Returns an integer.

        """
        if self.eat:
            # this integer is encoded against tick count (?)...
            # in this case, we read a protobuf-style varint
            v = stream.read_varint()

            if self.unsigned:
                return v # as is -- why?

            # ostensibly, this is the "decoding" part in signed cases
            return (-(v & Flag.Unsigned)) ^ (v >> Flag.Unsigned)

        v = stream.read_numeric_bits(self.bits)
        s = (0x80000000 >> (32 - self.bits)) & (self.unsigned - Flag.Unsigned)

        return (v ^ s) - s
