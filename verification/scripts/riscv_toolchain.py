"""Resolve a matching GCC/objdump pair without assuming the host platform."""
import os
import shutil
import sys
from typing import NamedTuple


class Toolchain(NamedTuple):
    prefix: str
    gcc: str
    objdump: str


def resolve(env=None, which=None, platform=None):
    env = os.environ if env is None else env
    which = shutil.which if which is None else which
    platform = sys.platform if platform is None else platform
    explicit = env.get('RISCV_GCC_PREFIX')
    prefixes = [explicit] if explicit else ['riscv-none-elf-', 'riscv64-unknown-elf-', 'riscv32-unknown-elf-']
    if not explicit and platform == 'win32':
        prefixes.append('D:/fyp-xpulpnn/tools/xpack-riscv-none-elf-gcc-15.2.0-1/bin/riscv-none-elf-')
    suffix = '.exe' if platform == 'win32' else ''
    for prefix in prefixes:
        gcc, objdump = which(prefix+'gcc'+suffix), which(prefix+'objdump'+suffix)
        if gcc and objdump: return Toolchain(prefix,gcc,objdump)
    return None
