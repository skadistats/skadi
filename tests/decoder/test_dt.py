import importlib as il
import os
import unittest

__impl__ = 'skadi_ext' if os.environ.get('SKADI_EXT') else 'skadi'
dcdr_dt = il.import_module(__impl__ + '.decoder.dt')

from skadi.state import recv_table as state_rt
from skadi.state.util import Prop, Type


class TestDT(unittest.TestCase):
    def test_decoder_constructs_recv_prop_decoders(self):
        _ = None

        rp = [
            Prop('a', '1', Type.Float, 0, _, 0, 0, _, 0, 0, _),
            Prop('b', '2', Type.Float, 0, _, 0, 0, _, 0, 0, _),
            Prop('c', '3', Type.Float, 0, _, 0, 0, _, 0, 0, _),
            Prop('d', '4', Type.Float, 0, _, 0, 0, _, 0, 0, _)
        ]

        recv_table = state_rt.RecvTable('DT_Foo', rp)
        decoder = dcdr_dt.mk(recv_table)

        self.assertEqual(rp[0], decoder.by_index[0].prop)
        self.assertEqual(rp[1], decoder.by_index[1].prop)
        self.assertEqual(rp[2], decoder.by_index[2].prop)
        self.assertEqual(rp[3], decoder.by_index[3].prop)
        self.assertEqual(rp[0], decoder.by_recv_prop[rp[0]].prop)
        self.assertEqual(rp[1], decoder.by_recv_prop[rp[1]].prop)
        self.assertEqual(rp[2], decoder.by_recv_prop[rp[2]].prop)
        self.assertEqual(rp[3], decoder.by_recv_prop[rp[3]].prop)


if __name__ == '__main__':
    unittest.main()
