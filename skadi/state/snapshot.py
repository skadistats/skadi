import collections


def construct(string_tables, templates, entities):
  return Snapshot(string_tables, templates, entities)


class Snapshot(object):
  def __init__(self, string_tables, templates, entities):
    self.string_tables = string_tables
    self.templates = templates
    self.entities = entities

  def unpack(self):
    return self.string_tables, self.templates, self.entities
