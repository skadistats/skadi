import collections as c

PropertyName = c.namedtuple('PropertyName', ['dt', 'name'])

def enum(**enums):
    _enum = type('Enum', (), enums)
    _enum._enums = enums
    return _enum
