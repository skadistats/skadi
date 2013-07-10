import collections as c

def enum(**enums):
  _enum = type('Enum', (), enums)
  _enum._enums = enums
  return _enum
