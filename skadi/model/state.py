class GameEvent(object):
	def __init__(self, _id, name, keys):
		self.id = _id
		self.name = name
		self.keys = keys

	def __repr__(self):
		_id, n= self.id, self.name
		lenkeys = len(self.keys)
		return "<GameEvent {0} '{1}' ({2} keys)>".format(_id, n, lenkeys)

class Class(object):
	def __init__(self, _id, name, dt):
		self.id = _id
		self.dt = dt
		self.name = name

	def __repr__(self):
		_id = self.id
		dtn = self.dt
		name = self.name
		return "<Class {0} '{1}' ({2})>".format(_id, name, dtn)

class StringTable(object):
	def __init__(self, name, flags, items, items_clientside):
		self.name = name
		self.items = items
		self.items_clientside = items_clientside
		self.flags = flags

	def __repr__(self):
		n, f = self.name, hex(int(self.flags))
		lenitems = len(self.items)
		lenitemsc = len(self.items_clientside)
		_repr = "<StringTable '{0}' f:{1} ({2} items, {3} items clientside)"
		return _repr.format(n, f, lenitems, lenitemsc)

class String(object):
	def __init__(self, name, data):
		self.name = name
		self.data = data

	def __repr__(self):
		n, d = self.name, self.data
		return "<String '{0}' ({1} bytes)>".format(n, d)
