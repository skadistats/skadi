import unittest

from skadi.state.util import humanize_type, humanize_flags, Flag, Type


class TestUtil(unittest.TestCase):
    def test_humanize_type_returns_string_repr_of_type(self):
        self.assertEqual(humanize_type(Type.Int), 'int')
        self.assertEqual(humanize_type(Type.Float), 'float')
        self.assertEqual(humanize_type(Type.Vector), 'vector')
        self.assertEqual(humanize_type(Type.VectorXY), 'vectorxy')
        self.assertEqual(humanize_type(Type.String), 'string')
        self.assertEqual(humanize_type(Type.Array), 'array')
        self.assertEqual(humanize_type(Type.DataTable), 'datatable')

    def test_humanize_flags_returns_array_of_flag_string_reprs(self):
        all_flags = \
            Flag.Unsigned | Flag.Coord | Flag.NoScale | Flag.RoundDown | \
            Flag.RoundUp | Flag.Normal | Flag.Exclude | Flag.XYZE | \
            Flag.InsideArray | Flag.ProxyAlways | Flag.VectorElem | \
            Flag.Collapsible | Flag.CoordMP | Flag.CoordMPLowPrecision | \
            Flag.CoordMPIntegral | Flag.CellCoord | \
            Flag.CellCoordLowPrecision | Flag.CellCoordIntegral | \
            Flag.ChangesOften | Flag.EncodedAgainstTickcount

        humanized = humanize_flags(all_flags)

        self.assertIn('unsigned', humanized)
        self.assertIn('coord', humanized)
        self.assertIn('noscale', humanized)
        self.assertIn('rounddown', humanized)
        self.assertIn('roundup', humanized)
        self.assertIn('normal', humanized)
        self.assertIn('exclude', humanized)
        self.assertIn('xyze', humanized)
        self.assertIn('insidearray', humanized)
        self.assertIn('proxyalways', humanized)
        self.assertIn('vectorelem', humanized)
        self.assertIn('collapsible', humanized)
        self.assertIn('coordmp', humanized)
        self.assertIn('coordmplowprecision', humanized)
        self.assertIn('coordmpintegral', humanized)
        self.assertIn('cellcoord', humanized)
        self.assertIn('cellcoordlowprecision', humanized)
        self.assertIn('cellcoordintegral', humanized)
        self.assertIn('changesoften', humanized)
        self.assertIn('encodedagainsttickcount', humanized)


if __name__ == '__main__':
    unittest.main()
