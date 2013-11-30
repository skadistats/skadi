from __future__ import absolute_import

import io
import os
import unittest

from skadi import demo as dm
from skadi.io import demo as d_io
from protobuf.impl import demo_pb2 as pb_d


pwd = os.path.dirname(__file__)
DEMO_PATH = os.path.abspath(os.path.join(pwd, 'fixtures', 'test.dem'))


class TestScanner(unittest.TestCase):
    def test_scan_kind_returns_match(self):
        with io.open(DEMO_PATH, mode='rb') as infile:
            io_demo = d_io.mk(infile)
            io_demo.bootstrap()
            peek, message = dm.scan_kind(io_demo, pb_d.DEM_SyncTick)
            self.assertEqual(pb_d.DEM_SyncTick, peek.kind)

    def test_scan_tick_returns_match(self):
        with io.open(DEMO_PATH, mode='rb') as infile:
            io_demo = d_io.mk(infile)
            io_demo.bootstrap()
            peek, message = dm.scan_tick(io_demo, 300)
            self.assertGreaterEqual(300, peek.kind)

    def test_scan_since_returns_timely_entries(self):
        with io.open(DEMO_PATH, mode='rb') as infile:
            io_demo = d_io.mk(infile)
            io_demo.bootstrap()
            fn_complete = lambda ((p, _)): p.tick >= 120 # for speed
            m = dm.scan_since(io_demo, 100, fn_complete=fn_complete)
            self.assertEqual(11, len(m))

    def test_scan_since_returns_filtered_entries(self):
        with io.open(DEMO_PATH, mode='rb') as infile:
            io_demo = d_io.mk(infile)
            io_demo.bootstrap()

            c = lambda ((p, _)): p.tick >= 10000 # for speed
            e = lambda ((p, _)): p.kind == pb_d.DEM_FullPacket
            m = dm.scan_since(io_demo, 100, fn_eligible=e, fn_complete=c)
            self.assertEqual(5, len(m))

    def test_scan_until_returns_timely_entries(self):
        with io.open(DEMO_PATH, mode='rb') as infile:
            io_demo = d_io.mk(infile)
            io_demo.bootstrap()
            m = dm.scan_until(io_demo, 120)
            self.assertEqual(77, len(m))

    def test_scan_between_returns_timely_entries(self):
        with io.open(DEMO_PATH, mode='rb') as infile:
            io_demo = d_io.mk(infile)
            io_demo.bootstrap()
            m = dm.scan_between(io_demo, 0, 120)
            self.assertEqual(77, len(m))
        

if __name__ == '__main__':
    unittest.main()
