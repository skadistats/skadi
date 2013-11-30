

def mk(*args):
    """
    Pass-through for ArrayDecoder instantiation.

    """
    return ArrayDecoder(*args)


class ArrayDecoder(object):
    """
    Decodes arrays of self.array_prop from a stream.

    """

    def __init__(self, prop, array_prop_decoder):
        """
        Initialize instance to be used for array property decoding.

        Arguments:
        prop -- array Prop (skadi.state.util) this instance represents
        array_prop_decoder -- decoder (skadi.decoder.recv_prop.*) for members

        """
        self.prop = prop

        shift, bits = prop.len, 0

        # there is probably a more concise way to do this
        while shift:
            shift >>= 1
            bits += 1

        self.bits = bits
        self.decoder = array_prop_decoder

    def decode(self, stream):
        """
        Reads a count of array elements from stream, then delegates to its
        private decoder for each element in that count.

        Arguments:
        stream -- a Stream (skadi.io.stream) from which to read

        """
        count = stream.read_numeric_bits(self.bits)
        return [self.decoder.decode(stream) for _ in range(count)]
