import collections as c

class World(object):
    def __init__(self):
        self.classes       = c.OrderedDict()
        self.properties    = c.OrderedDict()
        self.string_tables = c.OrderedDict()
        self.send_tables   = c.OrderedDict()
        self.recv_tables   = c.OrderedDict()

    def flatten_send_tables(self):
        pass