"""Compile every public helper and inspect actual emitted instruction words."""
import hashlib
import json
import pathlib
import re
import subprocess
import unittest
import sys
import os

ROOT = pathlib.Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / 'verification' / 'scripts'
sys.path.insert(0, str(SCRIPTS))
import riscv_toolchain


class Helpers(unittest.TestCase):
    def test_resolver_prefers_explicit_prefix(self):
        found = {
            'C:/tool/bin/riscv-none-elf-gcc.exe': 'C:/tool/bin/riscv-none-elf-gcc.exe',
            'C:/tool/bin/riscv-none-elf-objdump.exe': 'C:/tool/bin/riscv-none-elf-objdump.exe',
        }
        toolchain = riscv_toolchain.resolve(
            env={'RISCV_GCC_PREFIX': 'C:/tool/bin/riscv-none-elf-'},
            which=found.get,
            platform='win32',
        )
        self.assertEqual(toolchain.gcc, found['C:/tool/bin/riscv-none-elf-gcc.exe'])
        self.assertEqual(toolchain.objdump, found['C:/tool/bin/riscv-none-elf-objdump.exe'])

    def test_resolver_uses_riscv64_path_toolchain(self):
        found = {
            'riscv64-unknown-elf-gcc': '/usr/bin/riscv64-unknown-elf-gcc',
            'riscv64-unknown-elf-objdump': '/usr/bin/riscv64-unknown-elf-objdump',
        }
        toolchain = riscv_toolchain.resolve(env={}, which=found.get, platform='linux')
        self.assertEqual(toolchain.prefix, 'riscv64-unknown-elf-')
        self.assertEqual(toolchain.gcc, found['riscv64-unknown-elf-gcc'])

    def test_resolver_requires_compiler_and_objdump(self):
        toolchain = riscv_toolchain.resolve(
            env={'RISCV_GCC_PREFIX': 'riscv-none-elf-'},
            which=lambda name: '/tool/' + name if name.endswith('gcc') else None,
            platform='linux',
        )
        self.assertIsNone(toolchain)

    def test_resolver_uses_legacy_windows_local_install_as_last_resort(self):
        fallback = 'D:/fyp-xpulpnn/tools/xpack-riscv-none-elf-gcc-15.2.0-1/bin/riscv-none-elf-'
        found = {
            fallback + 'gcc.exe': fallback + 'gcc.exe',
            fallback + 'objdump.exe': fallback + 'objdump.exe',
        }
        toolchain = riscv_toolchain.resolve(env={}, which=found.get, platform='win32')
        self.assertEqual(toolchain.prefix, fallback)

    def test_resolver_returns_none_without_a_cross_toolchain(self):
        self.assertIsNone(riscv_toolchain.resolve(env={}, which=lambda _: None, platform='linux'))

    def test_public_helpers_emit_all_72_forms_and_quant_memory_barriers(self):
        header = ROOT / 'verification/sw/common/xpulpnn.h'
        self.assertTrue(header.exists(), 'Public typed xpulpnn.h helpers are not implemented')
        forms = json.loads((ROOT / 'verification/manifests/xpulpnn_isa.json').read_text())['forms']
        out = ROOT / 'artifacts/verification/arithmetic/c_helpers'
        out.mkdir(parents=True, exist_ok=True)
        code = ['#include "xpulpnn.h"']
        for form in forms:
            name = form['name'].replace('.', '_')
            helper = 'xpulpnn_' + name
            op = form['op']
            args = 'a' if op == 'abs' else 'a, (const int32_t *)(uintptr_t)b' if op == 'qnt' else 'acc, a, b' if op.startswith('sdot') else 'a, b'
            # Match the public helper ABI rather than a universal three-input shim.
            params = 'uint32_t a' if op == 'abs' else 'uint32_t a, uint32_t b, uint32_t acc' if op.startswith('sdot') else 'uint32_t a, uint32_t b'
            code.append(f'__attribute__((noinline,used)) uint32_t probe_{name}({params}) {{return {helper}({args});}}')
        code += [
            '__attribute__((noinline,used)) uint32_t probe_qnt_memory(int32_t *tables,int32_t before,int32_t after) {',
            '  tables[0]=before;',
            '  uint32_t result=xpulpnn_qnt_n(0,tables);',
            '  tables[0]=after;',
            '  return result;',
            '}',
        ]
        source = out / 'helpers.c'
        source.write_text('\n'.join(code) + '\n')
        toolchain = riscv_toolchain.resolve()
        if toolchain is None:
            if os.environ.get('REQUIRE_RISCV_TOOLCHAIN') == '1':
                self.fail('CI requires RISC-V GCC and objdump; check RISCV_GCC_PREFIX')
            self.skipTest('RISC-V GCC and objdump are unavailable; set RISCV_GCC_PREFIX to enable this check')
        command = [toolchain.gcc, '-march=rv32im', '-mabi=ilp32', '-O2',
                   '-std=c11', '-ffreestanding', '-Wall', '-Wextra', '-Werror',
                   '-I', str(header.parent), '-c', str(source), '-o', str(out / 'helpers.o')]
        built = subprocess.run(command, capture_output=True, text=True)
        (out / 'gcc.log').write_text(built.stdout + built.stderr)
        self.assertEqual(built.returncode, 0, built.stdout + built.stderr)
        decoded = subprocess.run([toolchain.objdump, '-d', '-M', 'no-aliases',
                                  str(out / 'helpers.o')], capture_output=True, text=True)
        self.assertEqual(decoded.returncode, 0, decoded.stderr)
        (out / 'helpers.disasm').write_text(decoded.stdout)
        functions = {}
        current = None
        for line in decoded.stdout.splitlines():
            symbol = re.match(r'^([0-9a-f]+) <([^>]+)>:', line)
            if symbol:
                current = symbol.group(2)
                functions[current] = []
            word = re.match(r'^\s*[0-9a-f]+:\s+([0-9a-f]{8})\s', line)
            if word and current:
                functions[current].append(int(word.group(1), 16))
        checked = []
        for form in forms:
            name = form['name'].replace('.', '_')
            words = functions['probe_' + name]
            custom = [word for word in words if word & 0x7f == 0x7b]
            self.assertEqual(len(custom), 1, form['name'])
            self.assertEqual(custom[0] & form['mask'], form['value'], form['name'])
            checked.append({'name': form['name'], 'word': f'{custom[0]:08x}'})
        words = functions['probe_qnt_memory']
        stores = [i for i, word in enumerate(words) if word & 0x707f == 0x2023]
        quant = [i for i, word in enumerate(words) if word & 0xfe00707f == 0xf400007b]
        self.assertEqual(len(stores), 2, 'Both table stores must survive compiler optimization')
        self.assertEqual(len(quant), 1)
        self.assertLess(stores[0], quant[0], 'Threshold initialization must precede qnt')
        self.assertLess(quant[0], stores[1], 'Subsequent table store must follow qnt')
        result = {'status': 'PASS', 'forms': checked, 'quant_memory_order': 'store/qnt/store',
                  'header_sha256': hashlib.sha256(header.read_bytes()).hexdigest(),
                  'command': command}
        (out / 'result.json').write_text(json.dumps(result, indent=2) + '\n')


if __name__ == '__main__':
    unittest.main()
