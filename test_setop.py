import unittest
import setop
from setop import *
from collections import Counter


abcdf_order0        = 'abbcccddddffff'
abcdf_order1        = 'dccffbdfadbcdf'
abcdf_other_counts  = 'aabbccddfffffffff'
alpha_nodups0       = 'abcdefghijklmnop'
alpha_nodups1       = 'zyxwvutsrqponmlk'
xyzuv               = 'xyzuvxyzzzzuvv'
abcdf_2orders   = (abcdf_order0, abcdf_order1)
all_strings     = (abcdf_order0, abcdf_order1, abcdf_other_counts, xyzuv, alpha_nodups0, alpha_nodups1, '')
all_strings_dup = (True, True, True, True, False, False, False)

class BasicClassesTestCase(unittest.TestCase):
    
    def test_ListDict(self):
        r = range(10)
        l = setop._ListDict(lambda x : x % 2, r)
        self.assertEqual(set(l.keys()),{0,1})
        for remainder in (0,1):
            self.assertEqual(l[remainder], [x for x in r if x % 2 == remainder])
            
    def test_CounterListDict(self):
        r = range(10)
        l = list(r) + list([x for x in r if x % 2 == 1])
        c = setop._CounterListDict(l)
        for x in r:
            self.assertEqual((x%2+1)*[x], c[x])

    def test_OrderedDictSet(self):
        r = range(10)
        o = setop._OrderedDictSet.fromkeys(r)
        self.assertEqual(list(o.keys()), list(o.values()))
        for x in r:
            self.assertEqual(x, o[x])
    
    def test_OrderedMultiset_iter(self):
        for s in abcdf_2orders:
            oms = setop._OrderedMultiset(s)
            self.assertEqual(len(s), len([x for x in oms]))
            for x,y in zip(s, oms):
                self.assertEqual(x, y)

    def test_OrderedMultiset_contains(self):
        abc = setop._OrderedMultiset(abcdf_order0)
        xyz = setop._OrderedMultiset(xyzuv)
        for a in abcdf_order0:
            self.assertIn(a, abc)
            self.assertNotIn(a, xyz)
        for x in xyzuv:
            self.assertNotIn(x, abc)
            self.assertIn(x, xyz)
            
    def test_OrderedMultiset_get(self):
        abc = setop._OrderedMultiset(abcdf_order0)
        xyz = setop._OrderedMultiset(xyzuv)
        for a in abcdf_order0:
            self.assertEqual(abc[a], a)
            self.assertRaises(KeyError, xyz.__getitem__, a)
        for x in xyzuv:
            self.assertRaises(KeyError, abc.__getitem__, x)
            self.assertEqual(xyz[x], x)
                
    def test_OrderedMultiset_pop(self):
        for a,b in (abcdf_2orders, list(reversed(abcdf_2orders))):
            oms = setop._OrderedMultiset(a)
            for x in b:
                self.assertIn(x, oms)
                self.assertEqual(x, oms.pop(x))
            self.assertEqual(len([x for x in oms]), 0)
            for x in b:
                self.assertNotIn(x, oms)
                self.assertRaises(KeyError, oms.pop, x)

    def test_OrderedMultiset_remove(self):
        for a,b in (abcdf_2orders, list(reversed(abcdf_2orders))):
            oms = setop._OrderedMultiset(a)
            for x in b:
                self.assertIn(x, oms)
                oms.remove(x)
            self.assertEqual(len([x for x in oms]), 0)
            for x in b:
                self.assertNotIn(x, oms)
                self.assertRaises(KeyError, oms.remove, x)
         
    def do_test_OrderedMultiset_remove_iter(self, remove_fun):
        for s in abcdf_2orders:
            counter = Counter(s)
            for x,n in counter.items():
                oms = setop._OrderedMultiset(s)
                for __ in range(n):
                    remove_fun(oms,x)
                for x,y in zip(s.replace(x,''), oms):
                    self.assertEqual(x, y)

    def test_OrderedMultiset_remove_iter(self):
        self.do_test_OrderedMultiset_remove_iter(lambda a,x: a.remove(x))

    def test_OrderedMultiset_pop_iter(self):
        self.do_test_OrderedMultiset_remove_iter(lambda a,x: a.pop(x))

class SetOpsTestCase(unittest.TestCase):
    def __init__(self,*args,**kwargs):
        super().__init__(*args, **kwargs)
        self.num_r = range(100)
        self.num_a = [x for x in self.num_r if x % 2 == 0]
        self.num_b = [x for x in self.num_r if x % 3 == 0]
    
    def is_ordered_subset(self, a,b):
        b = b.__iter__()
        for x in a:
            while True:
                try:
                    y = b.__next__()
                except StopIteration:
                    return False
                if x == y:
                    break
        return True        

    def test_SetOp_init(self):
        keys = (None, lambda x: 'foo', lambda x: 'bar'+x)
        keys_dup = (False, True, False)
        for a in all_strings:
            for (b,b_dup) in zip(all_strings,all_strings_dup):
                for multiset in (True, False):
                    for key_a in keys:
                        for key_b, key_b_dup in zip(keys, keys_dup):
                            for value_ab in (None, lambda a, b: a+b):
                                for b_as_is in (True, False):
                                    if (
                                        multiset and (key_a or key_b) or                    # keys not allowed for multiset
                                        not (multiset or b_as_is) and (b_dup or (key_b_dup and len(b)>=2))  # uniqueness check for b fails
                                        ):
                                        self.assertRaises(ValueError, SetOp,  a, b, multiset, key_a, key_b, value_ab, b_as_is)
                                    else:
                                        SetOp(a, b, multiset, key_a, key_b, value_ab, b_as_is)
    
    def test_SetIntersection(self):
        c = SetIntersection(self.num_a, self.num_b)
        d = [x for x in self.num_r if x % 6 == 0]
        for x,y in zip(c, d):
            self.assertEqual(x, y)
        with self.assertRaises(LookupError):
            [x for x in c]

    def test_SetUnion(self):
        c = SetUnion(self.num_a, self.num_b)
        d = self.num_a + [x for x in self.num_b if x not in self.num_a]
        for x,y in zip(c, d):
            self.assertEqual(x, y)
        with self.assertRaises(LookupError):
            [x for x in c]
                        
    def test_SetDifference(self):
        c = SetDifference(self.num_a, self.num_b)
        d = [x for x in self.num_a if x not in self.num_b]
        for x,y in zip(c, d):
            self.assertEqual(x, y)
        with self.assertRaises(LookupError):
            [x for x in c]                
    
    def test_SetSymmetricDifference(self):
        c = SetSymmetricDifference(self.num_a, self.num_b)
        d = [x for x in self.num_a if x not in self.num_b] + [x for x in self.num_b if x not in self.num_a]
        for x,y in zip(c, d):
            self.assertEqual(x, y)
        with self.assertRaises(LookupError):
            [x for x in c]
    
    def test_SetJoin(self):
        c = SetJoin(self.num_a, self.num_b, multiset = False, key_a = (lambda x: x//2), key_b = (lambda x: x//3))
        d = [(x//3*2,x) for x in self.num_b]
        for x,y in zip(c, d):
            self.assertEqual(x, y)
        with self.assertRaises(LookupError):
            [x for x in c]      # should not be able to iterate again

    def test_MSetJoin(self):
        c0  = SetJoin(self.num_r, self.num_r, multiset = True, key_a = None, key_b = (lambda x: x//2))
        c1  = SetJoin(self.num_r, self.num_r, multiset = True, key_a = (lambda x: -x), key_b = (lambda x: -(x//2)))
        neg = [-x for x in self.num_r]
        c2  = SetJoin(neg, self.num_r, multiset = True, key_a = (lambda x: -x), key_b = (lambda x: x//2), value_ab = (lambda x, y: (-x,y)))
        d   = [(x//2,x) for x in self.num_r]
        for c in (c0,c1,c2):
            for x,y in zip(c, d):
                self.assertEqual(x, y)
            with self.assertRaises(LookupError):
                [x for x in c]      # should not be able to iterate again
            
    def test_M_all_except_join(self):
        for a in all_strings:
            ac = Counter(a)
            for b in all_strings:
                bc = Counter(b)
                for (op,                        superset,   dc) in (
                    (SetIntersection,           a,          ac&bc),
                    (SetUnion,                  a+b,        ac|bc),
                    (SetDifference,             a,          ac-bc),
                    (SetSymmetricDifference,    a+b,        (ac-bc)|(bc-ac))
                    ):
                    c = list(op(a,b,True))
                    if op == SetUnion:
                        self.assertEqual(c[:len(a)],list(a))
                    self.assertTrue(self.is_ordered_subset(c, superset))
                    self.assertEqual(Counter(c), dc) 

    def test_all_crosstest(self):
        for (a,a_dup) in zip(all_strings,all_strings_dup):
            for (b,b_dup) in zip(all_strings,all_strings_dup):
                for m in (False, True):
                    if not m and (a_dup or b_dup):
                        with self.assertRaises(ValueError):
                            [x for x in SetSymmetricDifference(a,b,m)]
                        with self.assertRaises(ValueError):
                            [x for x in SetUnion(a,b,m)]
                    else:
                        sdl = list(SetSymmetricDifference(a,b,m))
                        self.assertEqual(
                            sdl,
                            list(SetUnion(SetDifference(a,b,m), SetDifference(b,a,m), m))
                            )
                        self.assertEqual(
                            Counter(sdl),
                            Counter(SetDifference(SetUnion(a,b,m), SetIntersection(a,b,m), m))
                            )
                    
    def test_MSetIntersection_extra(self):
        abcdf_counter = Counter(abcdf_order0)
        for b in [x+abcdf_order1 for x in all_strings]:
            c = SetIntersection(abcdf_order0, b, True)
            for x,y in zip(c, abcdf_order0):
                self.assertEqual(x, y)
            with self.assertRaises(LookupError):
                [x for x in c]

            c = list(SetIntersection(b, abcdf_order0, True))
            self.assertEqual(Counter(c), abcdf_counter)
            self.assertTrue(self.is_ordered_subset(c,b))

    def test_uniqueness_check(self):
        dup0 = list(self.num_r)+[0]
        # All operations (including join without keys)
        for setop in (SetIntersection, SetUnion, SetDifference, SetSymmetricDifference, SetJoin):
            c = setop(dup0, self.num_r)
            with self.assertRaises(ValueError):
                [x for x in c]      # duplicate value in the udnerlying set -> ValueError when iterating
            c = setop(dup0, self.num_r, True)
            [x for x in c]          # multiset, no error
        # Join, duplicate by key:
        c = SetJoin(self.num_r, self.num_r, key_a = lambda x: 0 if x==42 else x)
        with self.assertRaises(ValueError):
            [x for x in c]      # duplicate value in the udnerlying set -> ValueError when iterating
        with self.assertRaises(ValueError):
            c = SetJoin(self.num_r, self.num_r, key_b = lambda x: 0 if x==42 else x)
            [x for x in c]      # duplicate value in the udnerlying set -> ValueError when iterating
       

if __name__ == '__main__':
    unittest.main()
