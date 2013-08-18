import math


def enum(**enums):
  _enum = type('Enum', (), enums)
  _enum.tuples = enums
  return _enum

def bitlength(count):
  return int(math.ceil(math.log(count, 2)))
