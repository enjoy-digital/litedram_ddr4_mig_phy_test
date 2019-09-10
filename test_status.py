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

# Frequency checks ---------------------------------------------------------------------------------

print("DDR4 freq: {:3.2f} MHz".format(wb.regs.ddr4_clk_freq_value.read()/1e6))
print("DDR4 debug freq: {:3.2f} MHz".format(wb.regs.ddr4_debug_clk_freq_value.read()/1e6))

# Analyzer dump ------------------------------------------------------------------------------------
if hasattr(wb.regs, "analyzer"):
	print("true")
	analyzer = LiteScopeAnalyzerDriver(wb.regs, "analyzer", debug=True)
	analyzer.configure_group(0)
	analyzer.run(offset=32, length=128)

	analyzer.wait_done()
	analyzer.upload()
	analyzer.save("analyzer.vcd")

# # #

wb.close()
