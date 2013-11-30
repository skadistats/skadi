

def mk(*args):
    """
    Pass-through for ArrayDecoder instantiation.

    """
    return StringDecoder(*args)


class StringDecoder(object):
    """
    Decodes strings from a stream.

    """

    def __init__(self, prop):
        """
        Initialize instance to be used for string property decoding.

        Arguments:
        prop -- array Prop (skadi.state.util) this instance represents

        """
        self.prop = prop

    def decode(self, stream):
        """
        Decodes string, the first 9 bits indicating byte length.

        Arguments:
        stream -- a Stream (skadi.io.stream) from which to read

        Returns a string.

        """
        bytelength = stream.read_numeric_bits(9)
        return stream.read_string(bytelength)
