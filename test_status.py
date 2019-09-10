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
