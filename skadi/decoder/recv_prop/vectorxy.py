import math

from skadi.decoder.recv_prop import float as dcdr_flt


def mk(*args):
    """
    Pass-through for ArrayDecoder instantiation.

    """
    return VectorXYDecoder(*args)


class VectorXYDecoder(object):
    """
    Decodes vectors (tuples) of x, y floats from a stream.

    """

    def __init__(self, prop):
        """
        Initialize instance to be used for 2-element vector property decoding.

        Arguments:
        prop -- array Prop (skadi.state.util) this instance represents

        """
        self.prop = prop
        self.decoder = dcdr_flt.mk(prop)

    def decode(self, stream):
        """
        Decodes two consecutive x, y float values by private decoder.

        Arguments:
        stream -- a Stream (skadi.io.stream) from which to read

        Returns tuple of x, y floats.

        """
        x = self.decoder.decode(stream)
        y = self.decoder.decode(stream)

        return x, y
