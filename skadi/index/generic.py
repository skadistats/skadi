import collections as c


def mk(*args):
    """
    Pass-through for EpilogueIndex instantiation.

    """
    return Index(*args)


class Index(object):
    def __init__(self, entries):
        self.entries_by_kind = c.defaultdict(list)

        for entry in entries:
            peek, _ = entry
            self.entries_by_kind[peek.kind].append(entry)

    def find_kind(self, kind):
        assert len(self.entries_by_kind[kind]) >= 1
        return self.entries_by_kind[kind][0]

    def find_all_kind(self, kind):
        return self.entries_by_kind[kind]
