import unittest

from skadi.state import recv_table as state_rt
from skadi.state.util import Prop


class TestRecvTable(unittest.TestCase):
    def test_recv_table_items_accessible_by_integer(self):
        _ = None
        recv_prop_1 = Prop('a', '1', _, _, _, _, _, _, _, _, _)
        recv_prop_2 = Prop('b', '2', _, _, _, _, _, _, _, _, _)
        recv_prop_3 = Prop('c', '3', _, _, _, _, _, _, _, _, _)
        recv_prop_4 = Prop('d', '4', _, _, _, _, _, _, _, _, _)

        recv_props = [recv_prop_1, recv_prop_2, recv_prop_3, recv_prop_4]
        recv_table = state_rt.RecvTable('DT_Foo', recv_props)

        self.assertEqual(recv_prop_1, recv_table[0])
        self.assertEqual(recv_prop_4, recv_table[-1])

    def test_recv_table_items_accessible_by_tuple(self):
        _ = None
        recv_prop_1 = Prop('a', '1', _, _, _, _, _, _, _, _, _)
        recv_prop_2 = Prop('b', '2', _, _, _, _, _, _, _, _, _)
        recv_prop_3 = Prop('c', '3', _, _, _, _, _, _, _, _, _)
        recv_prop_4 = Prop('d', '4', _, _, _, _, _, _, _, _, _)

        recv_props = [recv_prop_1, recv_prop_2, recv_prop_3, recv_prop_4]
        recv_table = state_rt.RecvTable('DT_Foo', recv_props)

        fn = lambda: recv_table[('e', '5', 'foo')] # bad tuple
        self.assertRaises(AssertionError, fn)
        self.assertEqual(recv_prop_1, recv_table[('a', '1')])
        self.assertIn(('a', '1'), recv_table._cache)
        self.assertNotIn(('a', '2'), recv_table._cache)
        self.assertEqual(None, recv_table[('e', '5')]) # not extant
