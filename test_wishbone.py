#!/usr/bin/env python3

import sys
import time

from litex import RemoteClient
from litescope import LiteScopeAnalyzerDriver

wb = RemoteClient()
wb.open()

# # #

# FPGA ID ------------------------------------------------------------------------------------------
fpga_id = ""
for i in range(256):
    c = chr(wb.read(wb.bases.identifier_mem + 4*i) & 0xff)
    fpga_id += c
    if c == "\0":
        break
print("FPGA: " + fpga_id)

# Check DDR4 calibration ---------------------------------------------------------------------------
if wb.regs.ddr4_phy_calib_done.read() != 1:
    print("DDR4 calibration failed, exiting.")
    wb.close()
    exit(0)
else:
    print("DDR4 calibration successful, continue.")

# Test DDR4 ----------------------------------------------------------------------------------------

wb.regs.sdram_dfii_control.write(1) # hardware control

def seed_to_data(seed, random=True):
    if random:
        return (1664525*seed + 1013904223) & 0xffffffff
    else:
        return seed

def write_pattern(length):
    for i in range(length):
        wb.write(wb.mems.main_ram.base + 4*i, seed_to_data(i))
        time.sleep(0.1)

def check_pattern(length, debug=False):
    errors = 0
    for i in range(length):
        error = 0
        if wb.read(wb.mems.main_ram.base + 4*i) != seed_to_data(i):
            error = 1
            if debug:
                print("{}: 0x{:08x}, 0x{:08x} KO".format(i, wb.read(wb.mems.main_ram.base + 4*i), seed_to_data(i)))
        else:
            if debug:
                print("{}: 0x{:08x}, 0x{:08x} OK".format(i, wb.read(wb.mems.main_ram.base + 4*i), seed_to_data(i)))
        errors += error
    return errors

write_pattern(64)
errors = check_pattern(64, debug=True)
print("{} errors".format(errors))

# # #

wb.close()
