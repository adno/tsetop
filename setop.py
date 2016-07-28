from collections import OrderedDict, deque, Counter

def _orderedDictFromUniqueKeysAndValues(kvs):
    d = OrderedDict()
    for key, value in kvs:
        if key in d:
            raise ValueError('Value %r appears more than once in the set'%key)
        d[key] = value
    return d

class _OrderedDictSetMeta(type):
    def __call__(cls, items=None):
        if items == None:
            return type.__call__(cls)   # avoid infinite recursion via fromkeys()
        return cls.fromkeys(items)

class _OrderedDictSet(OrderedDict, metaclass=_OrderedDictSetMeta):
    # OrderedDict used as a set representation, pretends it's {key: key} instead of {key: Null}
    @classmethod
    def fromkeys(cls, iterable, value=None):
        d = cls()
        for key in iterable:
            if key in d:
                raise ValueError('Value %r appears more than once in the set'%key)
            d[key] = value
        return d

    def __getitem__(self, key):
        if key not in self:
            raise KeyError(key)
        return key
    def remove(self, key):
        del self[key]
    def values(self):
        return self.__iter__()

class _CounterListDict(Counter):
    # count*[key] instead of count
    def __getitem__(self, key):
        return super().__getitem__(key) * [key]

class _ListDict(dict):
    def __init__(self, key, items):
        for x in items:
            k = key(x)
            if k in self:
                self[k].append(x)
            else:
                self[k] = [x]

class _OrderedMultiset():
    # implements strictly what we need
    # items must not be integers or tuples
    
    # Basic special __methods__()
    
    def __init__(self, items):
        od  = OrderedDict()
        cur   = 1
        for x in items:
            if x not in od:
                od[x] = x
            else:
                xvalue      = od[x]
                od[cur]     = x
                if not type(xvalue) == tuple:
                    assert x == xvalue
                    od[x]   = (xvalue, deque((cur,)))
                else:
                    xvalue[1].append(cur)
                cur         +=1
        self.od     = od
        self.cur    = cur

    def __iter__(self):
        for xvalue in self.od.values():
            if not type(xvalue) == tuple:
                yield xvalue
            else:
                # xvalue ~ (x, deque[indices])
                x = xvalue[0]
                if x is None:   # just indices to multiple items of the same value, not the item itself, first such acts as a sentinel
                    break
                yield x

    def __contains__(self, key):
        return key in self.od

    # Mapping emulation

    def __getitem__(self, key):
        if key not in self.od:
            raise KeyError(key)
        return key
    def values(self):
        return self.__iter__()
    
    # Pop & Remove

    def pop(self, key):
        value = self.od[key]
        if not type(value) == tuple:
            del self.od[key]
            return value
        value0 = value[0]
        if value0 is not None:
            value1 = value[1]
            del self.od[key]
            self.od[key]    = (None, value1)    # create new entry at the end
            return value0
        # value ~ (None, deque(indices))
        indices = value[1]
        index = indices.popleft()
        if len(indices) == 0:
            del self.od[key]
        return self.od.pop(index)

    def remove(self, key):
        value = self.od[key]
        if not type(value) == tuple:
            del self.od[key]
            return
        if value[0] is not None:
            value1 = value[1]
            del self.od[key]
            self.od[key]    = (None, value1)    # create new entry at the end
            return
        # value ~ (None, deque(indices))
        indices = value[1]
        index = indices.popleft()
        if len(indices) == 0:
            del self.od[key]
        del self.od[index]
    

class SetOp():
    class _NullSetType():
        def add(self, __):
            pass
    class _UniqueSet(set):
        def add(self, x):
            if x in self:
                raise ValueError('Value %r appears more than once in the set'%x)
            super().add(x)
    _NullSet = _NullSetType()
    
    
    def __init__(self, a, b, multiset=False, key_a = None, key_b = None, value_ab = None, b_as_is = False):
        self.multiset   = multiset
        if not multiset:
            self.a_set  = SetOp._UniqueSet()
        else:
            if (key_a or key_b) and not isinstance(self, SetJoin):
                raise ValueError('Key functions provided for non-join operation on multisets')
            self.a_set  = SetOp._NullSet

        self.a          = a.__iter__()
        self.b          = (
            b                           if b_as_is  else
            _OrderedMultiset(b)         if multiset else
            _orderedDictFromUniqueKeysAndValues([(key_b(y), y) for y in b])     if key_b    else
            _OrderedDictSet(b)   # checks uniqueness
            )
                            
        self.key_a      = key_a         if key_a            else (lambda x: x)
        self.value_ab   = (value_ab      if value_ab        else
            (lambda x, y: (x, y))       if key_a or key_b   else
            (lambda x, y: x if x is not None else y)                        # TODO: regardless of key functions?
            )

class SetIntersection(SetOp):
    def __iter__(self):
        if self.a is None:
            raise LookupError('Cannot iterate more than once')
        if not self.multiset:
            for x in self.a:
                k = self.key_a(x)
                self.a_set.add(k)   # serves as safety check that a is actually a set (of unique values)
                if k in self.b:
                    yield self.value_ab(x, self.b[k])
        else:
            for x in self.a:
                k = self.key_a(x)
                if k in self.b:
                    y = self.b.pop(k)
                    yield self.value_ab(x, y)            
        self.a = None

class SetUnion(SetOp):
    def __iter__(self):
        if self.a is None:
            raise LookupError('Cannot iterate more than once')
        for x in self.a:
            k = self.key_a(x)
            self.a_set.add(k)   # serves as safety check that a is actually a set (of unique values)
            y = self.b.pop(k) if k in self.b else None
            yield self.value_ab(x,    y)
        for y in self.b.values():
            yield self.value_ab(None, y)
        self.a = None

class SetDifference(SetOp):
    def __iter__(self):
        if self.a is None:
            raise LookupError('Cannot iterate more than once')
        if not self.multiset:
            for x in self.a:
                k = self.key_a(x)
                self.a_set.add(k)   # serves as safety check that a is actually a set (of unique values)
                if k not in self.b:
                    yield self.value_ab(x, None)
        else:
            for x in self.a:
                k = self.key_a(x)
                if k in self.b:
                    self.b.remove(k)
                else:
                    yield self.value_ab(x, None)
        self.a = None


class SetSymmetricDifference(SetOp):
    def __iter__(self):
        if self.a is None:
            raise LookupError('Cannot iterate more than once')
        for x in self.a:
            k = self.key_a(x)
            self.a_set.add(k)   # serves as safety check that a is actually a set (of unique values)
            if k in self.b:
                self.b.remove(k)
            else:
                yield self.value_ab(x, None)
        for y in self.b.values():
            yield self.value_ab(None, y)
        self.a = None

# Two metaclassess to create a class cluster:
class SetJoinMeta(type):
    def __call__(cls, a, b, multiset=False, key_a = None, key_b = None, value_ab = (lambda x,y: (x,y)), left = False):
        assert cls == SetJoin, cls
        if not multiset:
            i = _USetJoin(a, b,                     False,   key_a, key_b, value_ab)
        elif not key_b:
            i = _MSetJoin(a, _CounterListDict(b),   True,    key_a, None,  value_ab)
        else:
            i = _MSetJoin(a, _ListDict(key_b, b),   True,    key_a, None,  value_ab)
        i.left = left
        return i

class ConcreteSetJoinMeta(SetJoinMeta):
    def __call__(cls, *args, **kwargs):
        return type.__call__(cls, *args, **kwargs)  # revert to the standard behavior (implemented by the default metaclass type)

class SetJoin(SetOp, metaclass = SetJoinMeta):
    pass

class _USetJoin(SetJoin, metaclass = ConcreteSetJoinMeta):
    def __init__(self, a, b, multiset, key_a, key_b, value_ab):
        super().__init__(a, b, multiset, key_a, key_b, value_ab)

    def __iter__(self):
        if self.a is None:
            raise LookupError('Cannot iterate more than once')
        for x in self.a:
            k = self.key_a(x)
            self.a_set.add(k)   # serves as safety check that a is actually a set (of unique values)
            if k in self.b:
                yield self.value_ab(x, self.b[k])
            elif self.left:
                yield self.value_ab(x, None)
        self.a = None

class _MSetJoin(SetJoin, metaclass = ConcreteSetJoinMeta):
    def __init__(self, a, b, multiset, key_a, key_b, value_ab):
        super().__init__(a, b, multiset, key_a, key_b, value_ab, b_as_is = True)

    def __iter__(self):
        if self.a is None:
            raise LookupError('Cannot iterate more than once')
        for x in self.a:
            k = self.key_a(x)
            if k in self.b:
                for y in self.b[k]:
                   yield self.value_ab(x, y)
            elif self.left:
                yield self.value_ab(x, None)
        self.a = None
