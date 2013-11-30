import itertools as it

from skadi.state.util import Prop, Flag, Type


def mk(pb):
    """
    Extract Prop (skadi.state.util) tuples from a CSVCMsg_SendTable protobuf
    message and return a SendTable (below) containing them.

    """
    send_props = []

    for sp in pb.props:
        # for send props of type Type.Array, the previous property stored is
        # the "template" for each of the items in the array.
        array_prop = send_props[-1] if sp.type is Type.Array else None

        send_prop = Prop(
            pb.net_table_name,
            sp.var_name, sp.type, sp.flags, sp.priority, sp.num_elements,
            sp.num_bits, sp.dt_name, sp.low_value, sp.high_value,
            array_prop
        )

        send_props.append(send_prop)

    return SendTable(pb.net_table_name, send_props, pb.needs_decoder)


def flatten(lookup, descendant):
    """
    Recursively aggregate ancestral send props into a single list of "recv
    props." Descendant send tables can also *exclude* send props from anywhere
    in their lineage, ensuring they don't end up in the flattened list.

    Because send tables are relational--they often reference other send tables
    --this method requires a dictionary of known send tables. Returns a list
    of Prop (skadi.state.util) instances to sort and pass to a new RecvTable.

    FIXME: Figure out how to test this ridiculous function.

    Arguments:
    lookup -- a dict with DT names as keys, and SendTable instances as values
    descendant -- the SendTable instance to flatten

    """
    assert descendant.needs_flattening

    def _aggregate_exclusions(send_table):
        """Recurse all ancestors and their relations, gathering exclusions."""
        relations = send_table.all_relations
        excl = map(lambda sp: _aggregate_exclusions(lookup[sp.dt]), relations)
        return list(send_table.all_exclusions) + list(it.chain(*excl))

    exclusions = _aggregate_exclusions(descendant)
    recv_props = [] # shared state within recursion

    def _flatten(ancestor, accumulator=None, proxy=None):
        """
        Recursion path for non-collapsible send tables.

        ancestor -- send table for this recursion frame
        accumulator -- mutable list of send props for this recursion frame
        proxy -- affects final naming of recv props while nested

        """
        accumulator = accumulator or []

        _flatten_collapsible(ancestor, accumulator)

        for send_prop in accumulator:
            s, n, t, f, p, l, b, d, _l, h, ap = send_prop

            if proxy:
                n = '{}.{}'.format(s, n).encode('utf-8')
                s = proxy

            # note: recv_props accessible by closure
            recv_props.append(Prop(s, n, t, f, p, l, b, d, _l, h, ap))

    def _flatten_collapsible(ancestor, accumulator):
        """
        Recursion path for collapsible send tables.

        Arguments:
        ancestor -- send table for this recursion frame
        accumulator -- mutable list of send props for this recursion frame

        """
        for send_prop in ancestor.all_non_exclusions:
            excluded = (ancestor.name, send_prop.name) in exclusions
            ineligible = send_prop.flags & Flag.InsideArray

            if excluded or ineligible:
                continue

            if send_prop.type is Type.DataTable:
                if send_prop.flags & Flag.Collapsible:
                    _flatten_collapsible(lookup[send_prop.dt], accumulator)
                else:
                    _flatten(lookup[send_prop.dt], [], proxy=send_prop.src)
            else:
                accumulator.append(send_prop)

    _flatten(descendant) # recv_props is mutated by this process

    return recv_props


class SendTable(object):
    """
    Think of a send table as a node in a ancestral tree of entity
    specifications. A send table has a list of properties, aka "send props,"
    which describe one data type (aka "DT") in the ancestry.

    Send tables must be flattened into a a list of "recv props," which are
    collectively managed by a RecvTable (skadi.state.recv_table). Recv tables
    are ultimately used to decode streams of entity data.

    Ancestor send props are inherited, recursively, by the descendant during
    flattening unless specifically excluded by the descendant.

    For flattening implementation details, see flatten() (above).
    For details on recv tables, see skadi.state.recv_table.

    """

    def __init__(self, name, send_props, needs_flattening):
        self.name = name
        self.send_props = send_props
        self.needs_flattening = needs_flattening

    @property
    def baseclass(self):
        gen = (sp.dt for sp in self.send_props if sp.name is 'baseclass')
        return next(gen, None)

    @property
    def all_exclusions(self):
        exclusions = (sp for sp in self.send_props if sp.flags & Flag.Exclude)
        return it.imap(lambda sp: (sp.dt, sp.name), exclusions)

    @property
    def all_non_exclusions(self):
        return (sp for sp in self.send_props if sp.flags ^ Flag.Exclude)

    @property
    def all_relations(self):
        non_exclusions = self.all_non_exclusions
        return (sp for sp in non_exclusions if sp.type is Type.DataTable)
