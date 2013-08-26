from __future__ import print_function

import collections
import itertools as it


def construct(*args):
  return Index(*args)


class Index(object):
  def __init__(self, iterable):
    self.entries = collections.OrderedDict(list(iterable))

  def __iter__(self):
    return self.entries.iteritems()

  def find(self, kind):
    return next(it.ifilter(lambda (p, _): p.kind == kind, self))

  def find_all(self, kind):
    return it.ifilter(lambda (p, _): p.kind == kind, self)

  def find_behind(self, tell):
    return it.ifilter(lambda (p, _): p.tell < tell, self)

  def find_at(self, tell):
    return it.ifilter(lambda (p, _): p.tell == tell, self)

  def find_ahead(self, tell):
    return it.ifilter(lambda (p, _): p.tell > tell, self)

  def find_between(self, start, stop):
    return it.ifilter(lambda (p, _): start < p.tell < stop, self)
