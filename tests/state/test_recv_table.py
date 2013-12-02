import importlib as il
import os
import unittest

__impl__ = 'skadi_ext' if os.environ.get('SKADI_EXT') else 'skadi'
stt_rcvtbl = il.import_module(__impl__ + '.state.recv_table')

from skadi.state.util import Prop


class TestRecvTable(unittest.TestCase):
    def test_recv_table_items_accessible_by_index(self):
        _ = None
        prop_1 = Prop('a', '1', _, _, _, _, _, _, _, _, _)
        prop_2 = Prop('b', '2', _, _, _, _, _, _, _, _, _)
        prop_3 = Prop('c', '3', _, _, _, _, _, _, _, _, _)
        prop_4 = Prop('d', '4', _, _, _, _, _, _, _, _, _)

        props = [prop_1, prop_2, prop_3, prop_4]
        recv_table = stt_rcvtbl.RecvTable('DT_Foo', props)

        self.assertEqual(prop_1, recv_table.by_index[0])
        self.assertEqual(prop_4, recv_table.by_index[-1])

    def test_recv_table_items_accessible_by_src(self):
        _ = None
        prop_1 = Prop('a', '1', _, _, _, _, _, _, _, _, _)
        prop_2 = Prop('b', '2', _, _, _, _, _, _, _, _, _)
        prop_3 = Prop('c', '3', _, _, _, _, _, _, _, _, _)
        prop_4 = Prop('d', '4', _, _, _, _, _, _, _, _, _)

        props = [prop_1, prop_2, prop_3, prop_4]
        recv_table = stt_rcvtbl.RecvTable('DT_Foo', props)

        self.assertEqual(list(recv_table.by_src['a']), (0, prop_1))
        self.assertEqual(list(recv_table.by_src['b']), (1, prop_2))
        self.assertEqual(list(recv_table.by_src['c']), (2, prop_3))
        self.assertEqual(list(recv_table.by_src['d']), (3, prop_4))

    def test_recv_table_items_accessible_by_src(self):
        _ = None
        prop_1 = Prop('a', '1', _, _, _, _, _, _, _, _, _)
        prop_2 = Prop('b', '1', _, _, _, _, _, _, _, _, _)
        prop_3 = Prop('c', '2', _, _, _, _, _, _, _, _, _)
        prop_4 = Prop('d', '2', _, _, _, _, _, _, _, _, _)

        props = [prop_1, prop_2, prop_3, prop_4]
        recv_table = stt_rcvtbl.RecvTable('DT_Foo', props)

        print list(recv_table.by_src['a'])
        self.assertEqual(list(recv_table.by_name['1']), \
            [(0, prop_1), (1, prop_2)])
        self.assertEqual(list(recv_table.by_name['2']), \
            [(2, prop_3), (3, prop_4)])

    def test_recv_table_items_accessible_by_tuple(self):
        _ = None
        prop_1 = Prop('a', '1', _, _, _, _, _, _, _, _, _)
        prop_2 = Prop('b', '2', _, _, _, _, _, _, _, _, _)
        prop_3 = Prop('c', '3', _, _, _, _, _, _, _, _, _)
        prop_4 = Prop('d', '4', _, _, _, _, _, _, _, _, _)

        props = [prop_1, prop_2, prop_3, prop_4]
        recv_table = stt_rcvtbl.RecvTable('DT_Foo', props)

        self.assertEqual((0, prop_1), recv_table.by_tuple[('a', '1')])


if __name__ == '__main__':
    unittest.main()
