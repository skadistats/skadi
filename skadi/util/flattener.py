import itertools

from skadi.model import dt

test_collapsible = lambda prop: prop.flags & dt.Flag.COLLAPSIBLE

class Flattener(object):
    def __init__(self, world):
        self.world = world

    def flatten(self, st):
        props = self._build(st, [], self._aggregate_exclusions(st))
        return dt.RecvTable.construct(st.dt, props)

    def _build(self, st, onto, excl):
        non_dt_props = self._compile(st, onto, excl)

        for prop in non_dt_props:
            onto.append(prop)

        return onto

    def _compile(self, st, onto, excl, collapsed=None):
        collapsed = collapsed or []

        def test_excluded(prop):
            return (st.dt, prop.var_name) not in excl

        for prop in st.dt_props:
            if dt.test_data_table(prop) and test_excluded(prop):
                _st = self.world.send_tables[prop.dt_name]
                if test_collapsible(prop):
                    collapsed += self._compile(_st, onto, excl, collapsed)
                else:
                    self._build(_st, onto, excl)

        return collapsed + filter(test_excluded, st.non_dt_props)

    def _aggregate_exclusions(self, st):
        def recurse(_dt_prop):
            st = self.world.send_tables[_dt_prop.dt_name]
            return self._aggregate_exclusions(st)

        inherited = map(recurse, st.dt_props)

        return st.exclusions + list(itertools.chain(*inherited))
