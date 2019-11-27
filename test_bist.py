#!/usr/bin/env python3

import sys
import time

from litex import RemoteClient

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
kB = 1024
mB = 1024*kB
gB = 1024*mB

wb.regs.sdram_dfii_control.write(1) # hardware control

class Generator:
    def __init__(self, name):
        for r in ["reset", "base", "length", "start", "done", "ticks",
                  "random"]:
            setattr(self, r, getattr(wb.regs, name + "_" + r))

    def init(self, base, length, random=False):
        self.write_length = length
        self.reset.write(1)
        self.reset.write(0)
        self.base.write(base)
        self.length.write(length)
        self.random.write(int(random))
        self.start.write(1)

    def wait(self):
        while(not self.done.read()):
            pass
        ticks = self.ticks.read()
        speed = wb.constants.config_clock_frequency*self.write_length/ticks
        return speed


class Checker:
    def __init__(self, name):
        for r in ["reset", "base", "length", "start", "done", "errors", "ticks",
                  "random"]:
            setattr(self, r, getattr(wb.regs, name + "_" + r))

    def init(self, base, length, random=False):
        self.read_length = length
        self.reset.write(1)
        self.reset.write(0)
        self.base.write(base)
        self.length.write(length)
        self.random.write(int(random))
        self.start.write(1)

    def wait(self):
        while(not self.done.read()):
            pass
        ticks = self.ticks.read()
        speed = wb.constants.config_clock_frequency*self.read_length/ticks
        errors = self.errors.read()
        return speed, errors


class BIST:
    def __init__(self, generator, checker):
        self.generator = generator
        self.checker = checker

        self.write_base_error_check()
        self.write_length_error_check()
        self.read_base_error_check()
        self.read_length_error_check()

        self.write_length = 0
        self.read_length = 0

    def write_base_error_check(self):
        self.generator.init(128, 1024)
        write_speed = self.generator.wait()
        self.checker.init(0, 1024)
        read_speed, read_errors = self.checker.wait()
        assert read_errors != 0

    def write_length_error_check(self):
        self.generator.init(0, 1024 - 128)
        write_speed = self.generator.wait()
        self.checker.init(0, 1024)
        read_speed, read_errors = self.checker.wait()
        assert read_errors != 0

    def read_base_error_check(self):
        self.generator.init(0, 1024)
        write_speed = self.generator.wait()
        self.checker.init(128, 1024)
        read_speed, read_errors = self.checker.wait()
        assert read_errors != 0

    def read_length_error_check(self):
        self.generator.init(0, 1024)
        write_speed = self.generator.wait()
        self.checker.init(0, 1024 + 128)
        read_speed, read_errors = self.checker.wait()
        assert read_errors != 0

    def test(self, base, length, increment, random):
        print("\nTesting Writes/Reads...")
        print("-"*40)

        offset =  0
        tested_errors = 0
        tested_length = 0

        i = 0

        while True:
            # write
            self.generator.init(base, length, random)
            write_speed = self.generator.wait()

            # read
            #self.checker.init(base, length, random)
            #read_speed, read_errors = self.checker.wait()
            read_speed, read_errors = 0, 0

            # infos
            if i%10 == 0:
                print("W_SPEED(gBps) R_SPEED(gBps) TESTED(mB)      ERRORS")
            i += 1
            tested_errors = tested_errors + read_errors
            tested_length = tested_length + length
            print("{:13.2f} {:13.2f} {:10d} {:11d}".format(
                8*write_speed/gB,
                8*read_speed/gB,
                tested_length//mB,
                tested_errors))
            #exit()

            offset += increment

bist = BIST(Generator("sdram_generator"), Checker("sdram_checker"))
bist.test(0x00000000, 2048*mB, 0, False)

# # #

wb.close()
