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
            ddr4_phy.c0_init_calib_complete,        # Signifies the status of calibration

            ddr4_phy.dbg_clk,
            ddr4_phy.dbg_rd_data_cmp,                # Comparison of dbg_rd_data and dbg_expected_data
            ddr4_phy.dbg_expected_data,              # Displays the expected data during calibration stages that use fabric-based data pattern comparison such as Read per
            ddr4_phy.dbg_cal_seq,                    # Calibration sequence indicator, when RTL is issuing commands to the DRAM.
            ddr4_phy.dbg_cal_seq_cnt,                # Calibration command sequence count used when RTL is issuing commands to the DRAM.
            ddr4_phy.dbg_cal_seq_rd_cnt,             # Calibration read data burst count
            ddr4_phy.dbg_rd_valid,                   # Read data valid
            ddr4_phy.dbg_cmp_byte,                   # Calibration byte selection
            ddr4_phy.dbg_rd_data,                    # Read data from input FIFOs
            ddr4_phy.dbg_cplx_config,                # Complex cal configuration
            ddr4_phy.dbg_cplx_status,                # Complex cal status
            ddr4_phy.dbg_io_address,                 # MicroBlaze I/O address bus
            ddr4_phy.dbg_pllGate,                    # PLL lock indicator
            ddr4_phy.dbg_phy2clb_fixdly_rdy_low,     # Xiphy fixed delay ready signal (lower nibble)
            ddr4_phy.dbg_phy2clb_fixdly_rdy_upp,     # Xiphy fixed delay ready signal (upper nibble)
            ddr4_phy.dbg_phy2clb_phy_rdy_low,        # Xiphy phy ready signal (lower nibble)
            ddr4_phy.dbg_phy2clb_phy_rdy_upp,        # Xiphy phy ready signal (upper nibble)
            ddr4_phy.win_status,                     #
            ddr4_phy.cal_r0_status,                  # Signifies the status of each stage of calibration.
            ddr4_phy.cal_post_status,                # Signifies the status of calibration.
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
