from skadi.state.util import Flag


def mk(*args):
    """
    Pass-through for ArrayDecoder instantiation.

    """
    return Int64Decoder(*args)


class Int64Decoder(object):
    """
    Decodes 64-bit integers from a stream.

    """

    def __init__(self, prop):
        """
        Initialize instance to be used for 64-bit integer property decoding.

        Arguments:
        prop -- array Prop (skadi.state.util) this instance represents

        """
        self.prop = prop

        assert prop.flags ^ Flag.EncodedAgainstTickcount

        self.unsigned = prop.flags & Flag.Unsigned
        self.bits = prop.bits

    def decode(self, stream):
        """
        Decodes a 64-bit signed integer from stream. Lowest-precision zeroed
        bits are truncated and filled by bitwise OR.

        Arguments:
        stream -- a Stream (skadi.io.stream) from which to read

        Returns an integer.

        """
        negate = False
        remainder = self.bits - 32

        if not self.unsigned:
            remainder -= 1
            if stream.read_numeric_bits(1):
                negate = True

        l = stream.read_numeric_bits(32)
        r = stream.read_numeric_bits(remainder)
        v = (l << 32) | r

        if negate:
            v *= -1

        return v
