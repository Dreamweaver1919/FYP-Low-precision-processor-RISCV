import pathlib
import sys
import unittest
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from model.packed import alu, dot
from model.quant import quantize_pair
from model.isa import forms, encode


class Models(unittest.TestCase):
    def test_abi_has_72_disjoint_forms(self):
        fs = forms()
        self.assertEqual(len(fs), 72)
        for i, a in enumerate(fs):
            self.assertEqual(encode(a['op'], a['width'], a['scalar'], 0, 0, 0), a['value'])
            for b in fs[i+1:]:
                self.assertNotEqual((a['value'] ^ b['value']) & (a['mask'] & b['mask']), 0)
        self.assertEqual(encode('add', 4, False, 7, 5, 6), 0x786283fb)

    def test_lane_wrap_and_average(self):
        self.assertEqual(alu('add', 4, 0xffffffff, 0x11111111), 0)
        self.assertEqual(alu('avg', 4, 0x77777777, 0x77777777), 0xffffffff)
        self.assertEqual(alu('avgu', 4, 0xffffffff, 0xffffffff), 0x77777777)
        self.assertEqual(alu('abs', 2, 0xaaaaaaaa, 0), 0xaaaaaaaa)

    def test_dot_accumulator_is_not_product_width(self):
        self.assertEqual(dot(4, 0, 0xffffffff, 0xffffffff), 1800)
        self.assertEqual(dot(2, 3, 0xaaaaaaaa, 0xaaaaaaaa), 64)
        self.assertEqual(dot(4, 1, 0xffffffff, 0xffffffff), (-120) & 0xffffffff)
        self.assertEqual(dot(4, 0, 0xffffffff, 0xffffffff, 0xfffffffe), 1798)

    def test_quant_examples_and_equality(self):
        self.assertEqual(quantize_pair(2, -5, 15, [-10,0,10], [-10,0,10]), 7)
        self.assertEqual(quantize_pair(4, -8, 8, list(range(-7,8)), list(range(-7,8))), 0x78)
        self.assertEqual(quantize_pair(2, 0, -1, [0,0,0], [0,0,0]), 9)


if __name__ == '__main__':
    unittest.main()
