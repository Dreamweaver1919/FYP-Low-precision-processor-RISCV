import importlib.util
import pathlib
import subprocess
import sys
import tempfile
import json
import unittest

SCRIPTS=pathlib.Path(__file__).resolve().parents[1]/'scripts'
sys.path.insert(0,str(SCRIPTS))
spec=importlib.util.spec_from_file_location('build_sw',SCRIPTS/'build_sw.py')
build=importlib.util.module_from_spec(spec);spec.loader.exec_module(build)
spec=importlib.util.spec_from_file_location('check_results',SCRIPTS/'check_results.py')
checker=importlib.util.module_from_spec(spec);spec.loader.exec_module(checker)
spec=importlib.util.spec_from_file_location('run_tests',SCRIPTS/'run_tests.py')
runner=importlib.util.module_from_spec(spec);spec.loader.exec_module(runner)


class ImageAndResults(unittest.TestCase):
    def test_byte_addresses_and_little_endian(self):
        i,d=build.convert_verilog_image('@00000200\n44 33 22 11\n@10000004\naa bb cc dd\n')
        self.assertEqual(i[0x200//4],0x11223344)
        self.assertEqual(d[1],0xddccbbaa)
        self.assertEqual(i[0],0)

    def test_unknown_or_overlapping_address_fails(self):
        for text in ('@20000000\n00','@0\n11223344','@0\n00\n@0\n01'):
            with self.assertRaises(ValueError): build.convert_verilog_image(text)

    def test_success_status_cannot_hide_mismatch(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=pathlib.Path(tmp)
            (p/'expected.json').write_text(json.dumps({'test':'test','seed':1,'signature':[7]}))
            (p/'simulation.json').write_text(json.dumps({'outcome':0,'status':1,'protocol_fail':0,'instruction_requests':1}))
            (p/'actual.hex').write_text('00000008\n')
            self.assertEqual(checker.check(p)['status'],'FAIL')

    def test_nonzero_xsim_exit_is_a_dut_failure(self):
        failure=subprocess.CalledProcessError(1,['xsim.bat','run_core'])
        self.assertEqual(runner.classify_failure('simulate',failure),'FAIL')

    def test_qnt_bad_base_has_immediate_load_to_qnt_and_alu_forward_cases(self):
        with tempfile.TemporaryDirectory() as tmp:
            source,expected=build.bad_base_source(pathlib.Path(tmp))
            self.assertEqual(expected,[7]+[0x12345678]*5+[2,0]*5)
            instructions=[line.strip() for line in source.read_text().splitlines()]
            load_at=instructions.index('lw t1,0(t3)')
            self.assertTrue(instructions[load_at+1].startswith('bad_0: .word'))
            self.assertIn('addi t1,t1,0',instructions)
            self.assertIn('addi t1,t1,4',instructions)

    def test_expected_negative_watchdog_is_not_reported_as_program_success(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=pathlib.Path(tmp)
            (p/'expected.json').write_text(json.dumps({'test':'nn_quant','seed':1,'signature':[],
                                                        'negative_environment_expected_watchdog':True}))
            (p/'simulation.json').write_text(json.dumps({'outcome':2,'status':0,'protocol_fail':0,'instruction_requests':1}))
            (p/'actual.hex').write_text('')
            result=checker.check(p)
            self.assertEqual(result['status'],'PASS')
            self.assertTrue(result['negative_environment_expected_watchdog'])


if __name__=='__main__': unittest.main()
