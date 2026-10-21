import pathlib
import sys
import unittest
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]))
from model.kernels import pack_row, unpack_row, datasets, reference


class Kernels(unittest.TestCase):
    def test_two_bit_tail_is_bounded_and_zero(self):
        values=[(n%4)-2 for n in range(72)]
        packed=pack_row(values,2)
        self.assertEqual(len(packed),5)
        self.assertEqual(packed[-1]>>16,0)
        self.assertEqual(unpack_row(packed,72,2),values)

    def test_shapes_and_full_output_count(self):
        data=datasets(1)
        self.assertEqual([(x['m'],x['k'],x['n']) for x in data],[(8,32,8),(36,72,8),(2,35,2),(8,32,8),(36,72,8),(2,35,2)])
        self.assertEqual(sum(len(reference(x)) for x in data),356)


if __name__=='__main__':unittest.main()
