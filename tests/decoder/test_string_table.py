import importlib as il
import io
import math
import os
import unittest

__impl__ = 'skadi_ext' if os.environ.get('SKADI_EXT') else 'skadi'
dcdr_strngtbl = il.import_module(__impl__ + '.decoder.string_table')

from skadi.io.stream import generic as io_strm_generic
from protobuf.impl import netmessages_pb2 as pb_n


pwd = os.path.dirname(__file__)
path_components = (pwd, '..', 'fixtures', 'CSVCMsg_CreateStringTable')
FIXTURE_PATH = os.path.abspath(os.path.join(*path_components))


def load(fixture):
    path = os.path.join(FIXTURE_PATH, fixture)
    with io.open(path, 'rb') as infile:
        m = infile.read()
        pb = pb_n.CSVCMsg_CreateStringTable()
        pb.ParseFromString(m)
        return pb


class TestStringTableDecoder(unittest.TestCase):
    def test_fixtures_decode_without_error(self):
        for fixture in os.listdir(FIXTURE_PATH):
            if not os.path.isfile(os.path.join(FIXTURE_PATH, fixture)):
                continue

            pb = load(fixture)
            stream = io_strm_generic.mk(pb.string_data)

            decoder = dcdr_strngtbl.mk(pb)
            decoder.decode(stream, pb.num_entries)


if __name__ == '__main__':
    unittest.main()
