#!/usr/bin/env python3

# This file is Copyright (c) 2019 Florent Kermarrec <florent@enjoy-digital.fr>
# License: BSD

import sys

from migen import *
from migen.genlib.io import CRG

import kcu105_platform as kcu105

from litex.soc.cores.uart import UARTWishboneBridge

from litex.soc.integration.soc_sdram import SoCSDRAM
from litex.soc.integration.builder import *

from litescope import LiteScopeAnalyzer

from litedram.modules import EDY4016A
from litedram.frontend.bist import LiteDRAMBISTGenerator
from litedram.frontend.bist import LiteDRAMBISTChecker

from usddr4migphy import USDDR4MIGPHY

# DDR4TestSoC --------------------------------------------------------------------------------------

class DDR4TestSoC(SoCSDRAM):
    def __init__(self, with_analyzer=True):
        sys_clk_freq = int(200e6)
        platform = kcu105.Platform()
        SoCSDRAM.__init__(self, platform, clk_freq=sys_clk_freq,
            cpu_type=None, with_uart=False, l2_size=128,
            ident="DDR4TestSoC", ident_version=True,)

        # CRG --------------------------------------------------------------------------------------
        self.clock_domains.cd_sys = ClockDomain()

        # Serial Bridge ----------------------------------------------------------------------------
        self.submodules.serial_bridge = UARTWishboneBridge(platform.request("serial"), sys_clk_freq)
        self.add_wb_master(self.serial_bridge.wishbone)

        # DDR4 PHY ---------------------------------------------------------------------------------
        self.submodules.ddr4_phy = ddr4_phy = USDDR4MIGPHY(platform, platform.request("ddram"))
        self.add_csr("ddr4_phy")

        # DDR4 Core --------------------------------------------------------------------------------
        sdram_module = EDY4016A(sys_clk_freq, "1:4")
        self.register_sdram(self.ddr4_phy, sdram_module.geom_settings, sdram_module.timing_settings)

        # DDR4 BIST
        sdram_generator_port = self.sdram.crossbar.get_port()
        sdram_checker_port   = self.sdram.crossbar.get_port()
        self.submodules.sdram_generator = LiteDRAMBISTGenerator(sdram_generator_port)
        self.add_csr("sdram_generator")
        self.submodules.sdram_checker   = LiteDRAMBISTChecker(sdram_checker_port)
        self.add_csr("sdram_checker")

        # Leds -------------------------------------------------------------------------------------
        self.comb += platform.request("user_led", 0).eq(ddr4_phy.init_calib_complete)

        # Analyzer ---------------------------------------------------------------------------------
        if with_analyzer:
            analyzer_signals = [
                ddr4_phy.init_calib_complete,
                ddr4_phy.mc_rd_cas,
                ddr4_phy.mc_wr_cas,
                ddr4_phy.mc_cas_slot,
                ddr4_phy.wr_data,
                ddr4_phy.wr_data_en,
                ddr4_phy.rd_data,
                ddr4_phy.rd_data_en,
                ddr4_phy.core_rddata_en,
                ddr4_phy.core_wrdata_en,

                sdram_generator_port.cmd.valid,
                sdram_generator_port.cmd.ready,
                sdram_generator_port.wdata.valid,
                sdram_generator_port.wdata.ready,
                sdram_generator_port.rdata.valid,
                sdram_generator_port.rdata.ready,

                sdram_checker_port.cmd.valid,
                sdram_checker_port.cmd.ready,
                sdram_checker_port.wdata.valid,
                sdram_checker_port.wdata.ready,
                sdram_checker_port.rdata.valid,
                sdram_checker_port.rdata.ready,
            ]
            self.submodules.analyzer = LiteScopeAnalyzer(analyzer_signals, 512, csr_csv="analyzer.csv")
            self.add_csr("analyzer")

# Build --------------------------------------------------------------------------------------------

def main():
    if "load" in sys.argv[1:]:
        from litex.build.xilinx import VivadoProgrammer
        prog = VivadoProgrammer()
        prog.load_bitstream("build/gateware/top.bit")
    else:
        soc = DDR4TestSoC()
        builder = Builder(soc, output_dir="build", csr_csv="csr.csv", compile_gateware=True)
        vns = builder.build()

if __name__ == "__main__":
    main()
