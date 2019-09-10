#!/usr/bin/env python3

# This file is Copyright (c) 2018-2019 Florent Kermarrec <florent@enjoy-digital.fr>
# License: BSD

import sys

from migen import *
from migen.genlib.io import CRG

import kcu105_platform as kcu105

from litex.soc.cores.uart import UARTWishboneBridge

from litex.soc.integration.soc_core import SoCMini
from litex.soc.integration.builder import *

from litescope import LiteScopeAnalyzer

from usddrphy_mig import USDDRPHY

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

        # DDR4 PHY ---------------------------------------------------------------------------------
        self.submodules.ddr4_phy = ddr4_phy = USDDRPHY(platform, platform.request("ddram"))

        # Analyzer ---------------------------------------------------------------------------------
        analyzer_signals = [
            ddr4_phy.c0_ddr4_ui_clk,
            ddr4_phy.c0_ddr4_ui_clk_sync_rst,
            ddr4_phy.c0_init_calib_complete,

            ddr4_phy.dbg_clk,
            ddr4_phy.dbg_rd_data_cmp,
            ddr4_phy.dbg_expected_data,
            ddr4_phy.dbg_cal_seq,
            ddr4_phy.dbg_cal_seq_cnt,
            ddr4_phy.dbg_cal_seq_rd_cnt,
            ddr4_phy.dbg_rd_valid,
            ddr4_phy.dbg_cmp_byte,
            ddr4_phy.dbg_rd_data,
            ddr4_phy.dbg_cplx_config,
            ddr4_phy.dbg_cplx_status,
            ddr4_phy.dbg_io_address,
            ddr4_phy.dbg_pllGate,
            ddr4_phy.dbg_phy2clb_fixdly_rdy_low,
            ddr4_phy.dbg_phy2clb_fixdly_rdy_upp,
            ddr4_phy.dbg_phy2clb_phy_rdy_low,
            ddr4_phy.dbg_phy2clb_phy_rdy_upp,
            ddr4_phy.win_status,
            ddr4_phy.cal_r0_status,
            ddr4_phy.cal_post_status,
            ddr4_phy.tCWL,
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
        builder = Builder(soc, output_dir="build", csr_csv="csr.csv", compile_gateware=True)
        vns = builder.build()

if __name__ == "__main__":
    main()
