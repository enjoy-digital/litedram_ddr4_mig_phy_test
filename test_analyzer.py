#!/usr/bin/env python3

import sys
import time

from litex import RemoteClient
from litescope import LiteScopeAnalyzerDriver

wb = RemoteClient(debug=False)
wb.open()

# # #

def help():
    print("Supported triggers:")
    print(" - read")
    print(" - write")
    print("")
    print(" - now")
    exit()

if len(sys.argv) < 2:
    help()

if len(sys.argv) < 3:
    length = 512
else:
    length = int(sys.argv[2])

# FPGA ID ------------------------------------------------------------------------------------------
fpga_id = ""
for i in range(256):
    c = chr(wb.read(wb.bases.identifier_mem + 4*i) & 0xff)
    fpga_id += c
    if c == "\0":
        break
print("FPGA: " + fpga_id)

# Analyzer dump ------------------------------------------------------------------------------------
analyzer = LiteScopeAnalyzerDriver(wb.regs, "analyzer", debug=True)
if sys.argv[1] == "read":
    analyzer.add_rising_edge_trigger("usddr4migphy_mc_rd_cas")
elif sys.argv[1] == "write":
    analyzer.add_rising_edge_trigger("usddr4migphy_mc_wr_cas")
elif sys.argv[1] == "now":
    analyzer.configure_trigger(cond={})
else:
    raise ValueError
analyzer.run(offset=32, length=length)
analyzer.wait_done()
analyzer.upload()
analyzer.save("analyzer.vcd")

# # #

wb.close()
