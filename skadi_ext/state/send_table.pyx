import itertools as it

from skadi.state.util import Prop, Flag, Type


cpdef mk(object pb):
    cdef object send_props = []
    cdef object array_prop

    for sp in pb.props:
        array_prop = send_props[-1] if sp.type is Type.Array else None

        send_prop = Prop(
            pb.net_table_name,
            sp.var_name, sp.type, sp.flags, sp.priority, sp.num_elements,
            sp.num_bits, sp.dt_name, sp.low_value, sp.high_value,
            array_prop
        )

        send_props.append(send_prop)

    return SendTable(pb.net_table_name, send_props, pb.needs_decoder)


def _aggregate_exclusions(object l, object st):
    relations = st.all_relations
    excl = map(lambda sp: _aggregate_exclusions(l, l[sp.dt]), relations)
    return list(st.all_exclusions) + list(it.chain(*excl))


cdef object _flatten(object l, object rp, object excl, object anc, object acc=None, object prx=None):
    cdef object _acc = acc or []
    cdef object n, s

    _flatten_collapsible(l, rp, excl, anc, _acc)

    for sp in _acc:
        if prx:
            n = '{}.{}'.format(sp[0], sp[1]).encode('utf-8')
            s = prx
        else:
            n = sp[0]
            s = sp[1]

        rp.append(Prop(s, n, *sp[2:]))


cdef object _flatten_collapsible(object l, object rp, object excl, object anc, object acc):
    cdef int excluded, ineligible

    for sp in anc.all_non_exclusions:
        excluded = (anc.name, sp.name) in excl
        ineligible = sp.flags & Flag.InsideArray

        if excluded or ineligible:
            continue

        if sp.type is Type.DataTable:
            if sp.flags & Flag.Collapsible:
                _flatten_collapsible(l, rp, excl, l[sp.dt], acc)
            else:
                _flatten(l, rp, excl, l[sp.dt], [], prx=sp.src)
        else:
            acc.append(sp)


cpdef object flatten(object lookup, object descendant):
    assert descendant.needs_flattening

    cdef object excl = _aggregate_exclusions(lookup, descendant)
    cdef object rp = [] # shared state within recursion

    _flatten(lookup, rp, excl, descendant) # recv_props is mutated

    return rp


cdef class SendTable(object):
    def __init__(self, name, send_props, needs_flattening):
        self.name = name
        self.send_props = send_props
        self.needs_flattening = needs_flattening

    property baseclass:
        def __get__(SendTable self):
            gen = (sp.dt for sp in self.send_props if sp.name is 'baseclass')
            return next(gen, None)

    property all_exclusions:
        def __get__(SendTable self):
            gen = (sp for sp in self.send_props if sp.flags & Flag.Exclude)
            return it.imap(lambda sp: (sp.dt, sp.name), gen)

    property all_non_exclusions:
        def __get__(SendTable self):
            return (sp for sp in self.send_props if sp.flags ^ Flag.Exclude)

    property all_relations:
        def __get__(SendTable self):
            non_exclusions = self.all_non_exclusions
            return (sp for sp in non_exclusions if sp.type is Type.DataTable)
