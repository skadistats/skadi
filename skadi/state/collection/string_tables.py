from skadi.state.util import String


def mk(*args):
    return StringTablesCollection(*args)


def rebase(pb_string_tables, basis):
    """
    Apply new, protobuf-formatted string tables to a 'basis' instance of
    StringTablesCollection (below).

    Returns a StringTablesCollection instance of pb changes applied to basis.

    Arguments:
    pb -- a CDemoFullPacket (protobuf.impl.demo_pb2)
    basis -- a StringTablesCollection (below)

    """
    string_list_by_name = dict()

    for tbl in pb_string_tables.tables:
        string_list_by_name[tbl.table_name] = \
            [String(i, e.str, e.data) for i, e in enumerate(tbl.items)]

    return basis + StringTablesCollection(string_list_by_name)


class StringTablesCollection(object):
    def __init__(self, string_list_by_name):
        mapping = dict()
        by_index = dict()
        by_name = dict()

        for i, (name, string_list) in enumerate(string_list_by_name.items()):
            mapping[i] = name
            by_index[i] = string_list
            by_name[name] = string_list

        self._original = string_list_by_name
        self.mapping = mapping
        self.by_index = by_index
        self.by_name = by_name

    def __add__(self, other):
        old = self._original.copy()
        new = other._original
        old.update(new)
        return StringTablesCollection(old)
