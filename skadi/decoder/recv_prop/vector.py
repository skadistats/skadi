import importlib as il
import math
import os
import snappy

__impl__ = 'skadi_ext' if os.environ.get('SKADI_EXT') else 'skadi'
dcdr_flt = il.import_module(__impl__ + '.decoder.recv_prop.float')

from skadi.state.util import Flag


def mk(*args):
    """
    Pass-through for ArrayDecoder instantiation.

    """
    return VectorDecoder(*args)


class VectorDecoder(object):
    """
    Decodes vectors (tuples) of x, y, z floats from a stream.

    """

    def __init__(self, prop):
        """
        Initialize instance to be used for vector property decoding.

        Arguments:
        prop -- array Prop (skadi.state.util) this instance represents

        """
        self.prop = prop
        self.normal = prop.flags & Flag.Normal
        self.decoder = dcdr_flt.mk(prop)

    def decode(self, stream):
        """
        Decodes three consecutive x, y, z float values by private decoder.

        Arguments:
        stream -- a Stream (skadi.io.stream) from which to read

        Returns tuple of x, y, z floats.

        """
        x = self.decoder.decode(stream)
        y = self.decoder.decode(stream)

        if self.normal:
            f = x * x + y * y
            z = 0 if (f <= 1) else math.sqrt(1 - f)

            sign = stream.read_numeric_bits(1)
            if sign:
                z *= -1
        else:
            z = self.decoder.decode(stream)

        return x, y, z
