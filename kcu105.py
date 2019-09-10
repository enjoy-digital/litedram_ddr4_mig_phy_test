#!/usr/bin/env python3

# This file is Copyright (c) 2018-2019 Florent Kermarrec <florent@enjoy-digital.fr>
# License: BSD

import sys

from migen import *
from migen.genlib.io import CRG

from litex.boards.platforms import kcu105

from litex.soc.cores.uart import UARTWishboneBridge

from litex.soc.integration.soc_core import SoCMini
from litex.soc.integration.builder import *

from litescope import LiteScopeAnalyzer

# DDR4TestSoC --------------------------------------------------------------------------------------

class DDR4TestSoC(SoCMini):
    def __init__(self, sys_clk_freq=int(125e6), **kwargs):
        platform = kcu105.Platform()
        SoCMini.__init__(self, platform, clk_freq=sys_clk_freq, ident="DDR4TestSoC", ident_version=True)

        # CRG --------------------------------------------------------------------------------------
        self.submodules.crg = CRG(platform.request("clk125"))

        # Serial Bridge ----------------------------------------------------------------------------
        self.submodules.serial_bridge = UARTWishboneBridge(platform.request("serial"), sys_clk_freq)
        self.add_wb_master(self.serial_bridge.wishbone)

        # Analyzer ---------------------------------------------------------------------------------
        analyzer_signals = [
            Signal(2),
            Signal(2),
        ]
        self.submodules.analyzer = LiteScopeAnalyzer(analyzer_signals, 128, csr_csv="analyzer.csv")
        self.add_csr("analyzer")

# Build --------------------------------------------------------------------------------------------

def main():
    if "load" in sys.argv[1:]:
        from litex.build.xilinx import VivadoProgrammer
        prog = VivadoProgrammer()
        prog.load_bitstream("build/gateware/top.bit")
    else:
        soc = DDR4TestSoC()
        builder = Builder(soc, output_dir="build", csr_csv="csr.csv", compile_gateware=False)
        vns = builder.build()

if __name__ == "__main__":
    main()
