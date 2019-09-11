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
analyzer = LiteScopeAnalyzerDriver(wb.regs, "analyzer", debug=True)
#analyzer.configure_trigger(cond={
#	"usddr4migphy_mc_rd_cas" : 1,
#	"usddr4migphy_mc_wr_cas" : 0,
#})
analyzer.add_rising_edge_trigger("usddr4migphy_mc_rd_cas")
#analyzer.add_rising_edge_trigger("usddr4migphy_mc_wr_cas")
analyzer.run(offset=64, length=128)
analyzer.wait_done()
analyzer.upload()
analyzer.save("analyzer.vcd")

# # #

wb.close()
