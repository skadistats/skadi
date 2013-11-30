import io
import os
import unittest

#from skadi.state import recv_table as state_rt
from skadi.state import send_table as state_st
from skadi.state.util import Prop, Type, Flag
from protobuf.impl import netmessages_pb2 as pb_n


pwd = os.path.dirname(__file__)
path_components = (pwd, '..', 'fixtures', 'CSVCMsg_SendTable')
FIXTURE_PATH = os.path.abspath(os.path.join(*path_components))


def load(fixture):
    path = os.path.join(FIXTURE_PATH, fixture)
    with io.open(path, 'rb') as infile:
        m = infile.read()
        pb = pb_n.CSVCMsg_SendTable()
        pb.ParseFromString(m)
        return pb


class TestSendTable(unittest.TestCase):
    def test_mk_and_flatten(self):
        # Test sucks, but if you look at flatten() you'll see it's untestable.

        lookup = {}
        for fixture in os.listdir(FIXTURE_PATH):
            if not os.path.isfile(os.path.join(FIXTURE_PATH, fixture)):
                continue

            send_table = state_st.mk(load(fixture))
            lookup[send_table.name] = send_table

        for send_table in lookup.values():
            if send_table.needs_flattening:
                flattened = state_st.flatten(lookup, send_table)
                # recv_props = state_rt._sorted(flattened)
                # print send_table.name
                # for recv_prop in recv_props:
                #     print '  {}'.format(recv_prop)

    def test_baseclass_returns_proper_name(self):
        _ = None
        send_prop = Prop(_, 'baseclass', _, _, _, _, _, 'DT_Foo', _, _, _)
        send_table = state_st.SendTable('DT_Bar', [send_prop], True)
        self.assertEqual('DT_Foo', send_table.baseclass)

    def test_all_exclusions_returns_matching_send_props(self):
        _ = None
        send_prop_1 = Prop(_, _, _, Flag.Exclude, _, _, _, _, _, _, _)
        send_prop_2 = Prop(_, _, _, Flag.Exclude, _, _, _, _, _, _, _)
        send_prop_3 = Prop(_, _, _, Flag.Exclude, _, _, _, _, _, _, _)
        send_prop_4 = Prop(_, _, _, 0, _, _, _, _, _, _, _)

        send_props = [send_prop_1, send_prop_2, send_prop_3, send_prop_4]
        send_table = state_st.SendTable('DT_Foo', send_props, True)

        self.assertEqual(3, len(list(send_table.all_exclusions)))

    def test_all_non_exclusions_returns_matching_send_props(self):
        _ = None
        send_prop_1 = Prop(_, _, _, 0, _, _, _, _, _, _, _)
        send_prop_2 = Prop(_, _, _, Flag.Exclude, _, _, _, _, _, _, _)
        send_prop_3 = Prop(_, _, _, Flag.Exclude, _, _, _, _, _, _, _)
        send_prop_4 = Prop(_, _, _, 0, _, _, _, _, _, _, _)

        send_props = [send_prop_1, send_prop_2, send_prop_3, send_prop_4]
        send_table = state_st.SendTable('DT_Foo', send_props, True)

        self.assertEqual(2, len(list(send_table.all_non_exclusions)))

    def test_all_relations_returns_matching_send_props(self):
        _ = None
        send_prop_1 = Prop(_, _, 0, 0, _, _, _, _, _, _, _)
        send_prop_2 = Prop(_, _, Type.DataTable, 0, _, _, _, _, _, _, _)
        send_prop_3 = Prop(_, _, 0, 0, _, _, _, _, _, _, _)
        send_prop_4 = Prop(_, _, Type.DataTable, 0, _, _, _, _, _, _, _)

        send_props = [send_prop_1, send_prop_2, send_prop_3, send_prop_4]
        send_table = state_st.SendTable('DT_Foo', send_props, True)

        self.assertEqual(2, len(list(send_table.all_relations)))


if __name__ == '__main__':
    unittest.main()
