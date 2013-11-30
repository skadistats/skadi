import importlib as il
import os

__impl__ = 'skadi_ext' if os.environ.get('SKADI_EXT') else 'skadi'
c = 'c' if __impl__ == 'skadi_ext' else ''
d_ary = il.import_module(__impl__ + '.decoder.recv_prop.{}array'.format(c))
d_flt = il.import_module(__impl__ + '.decoder.recv_prop.{}float'.format(c))
d_nt = il.import_module(__impl__ + '.decoder.recv_prop.{}int'.format(c))
d_nt64 = il.import_module(__impl__ + '.decoder.recv_prop.{}int64'.format(c))
d_strng = il.import_module(__impl__ + '.decoder.recv_prop.{}string'.format(c))
d_vctr = il.import_module(__impl__ + '.decoder.recv_prop.{}vector'.format(c))
ivxy = '.decoder.recv_prop.{}vectorxy'.format(c) # name too long :(
d_vctrxy = il.import_module(__impl__ + ivxy)

from skadi.state.util import Prop, Type, Flag


MODULES_BY_TYPE = {
    Type.Array: d_ary,
    Type.Float: d_flt,
    Type.Int: d_nt,
    Type.Int64: d_nt64,
    Type.String: d_strng,
    Type.Vector: d_vctr,
    Type.VectorXY: d_vctrxy
}


def mk(prop):
    """
    Constructs a property decoder suitable for the provided prop.

    Arguments:
    prop -- a Prop (skadi.state.util)

    Returns a suitable decoder (skadi.decoder.recv_prop.*).

    """
    try:
        if prop.type is Type.Array:
            # array props have an embedded prop describing the in-array type
            array_prop = prop.array_prop
            apd = MODULES_BY_TYPE[array_prop.type].mk(array_prop)
            return d_ary.mk(prop, apd)
        return MODULES_BY_TYPE[prop.type].mk(prop)
    except KeyError:
        raise NotImplementedError()
