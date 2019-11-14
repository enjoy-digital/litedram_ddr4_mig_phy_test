#!/usr/bin/env python3

# This file is Copyright (c) 2019 Florent Kermarrec <florent@enjoy-digital.fr>
# License: BSD

import argparse

from migen import *
from migen.genlib.io import CRG

from litex.build.generic_platform import *
from litex.build.sim import SimPlatform
from litex.build.sim.config import SimConfig

from litex.soc.integration.soc_core import *
from litex.soc.integration.soc_sdram import *
from litex.soc.integration.builder import *
from litex.soc.cores import uart

from litedram.modules import EDY4016A

from usddr4migphy import USDDR4MIGPHY

# IOs ----------------------------------------------------------------------------------------------

class SimPins(Pins):
    def __init__(self, n=1):
        Pins.__init__(self, "s "*n)

_io = [
    ("sys_clk", 0, SimPins(1)),
    ("sys_rst", 0, SimPins(1)),
    ("serial", 0,
        Subsignal("source_valid", SimPins()),
        Subsignal("source_ready", SimPins()),
        Subsignal("source_data",  SimPins(8)),

        Subsignal("sink_valid",   SimPins()),
        Subsignal("sink_ready",   SimPins()),
        Subsignal("sink_data",    SimPins(8)),
    ),

    ("ddram", 0,
        Subsignal("a",       SimPins(14)),
        Subsignal("ba",      SimPins(2)),
        Subsignal("bg",      SimPins(1)),
        Subsignal("ras_n",   SimPins(1)),
        Subsignal("cas_n",   SimPins(1)),
        Subsignal("we_n",    SimPins(1)),
        Subsignal("cs_n",    SimPins(1)),
        Subsignal("act_n",   SimPins(1)),
        Subsignal("ten",     SimPins(1)),
        Subsignal("alert_n", SimPins(1)),
        Subsignal("par",     SimPins(1)),
        Subsignal("dm",      SimPins(8)),
        Subsignal("dq",      SimPins(64)),
        Subsignal("dqs_p",   SimPins(8)),
        Subsignal("dqs_n",   SimPins(8)),
        Subsignal("clk_p",   SimPins(1)),
        Subsignal("clk_n",   SimPins(1)),
        Subsignal("cke",     SimPins(1)),
        Subsignal("odt",     SimPins(1)),
        Subsignal("reset_n", SimPins(1)),
        Misc("SLEW=FAST"),
    ),
]

# Platform -----------------------------------------------------------------------------------------

class Platform(SimPlatform):
    default_clk_name = "sys_clk"
    default_clk_period = 1000 # ~ 1MHz

    def __init__(self):
        SimPlatform.__init__(self, "SIM", _io)

    def do_finalize(self, fragment):
        pass

# Simulation SoC -----------------------------------------------------------------------------------

class SimSoC(SoCSDRAM):
    def __init__(self, **kwargs):
        platform     = Platform()
        sys_clk_freq = int(1e6)

        # SoCSDRAM ---------------------------------------------------------------------------------
        SoCSDRAM.__init__(self, platform, clk_freq=sys_clk_freq,
            integrated_rom_size = 0x8000,
            ident               = "LiteX Simulation", ident_version=True,
            with_uart           = False,
            **kwargs)
        # CRG --------------------------------------------------------------------------------------
        self.submodules.crg = CRG(platform.request("sys_clk"))

        # Serial -----------------------------------------------------------------------------------
        self.submodules.uart_phy = uart.RS232PHYModel(platform.request("serial"))
        self.submodules.uart = uart.UART(self.uart_phy)
        self.add_csr("uart")
        self.add_interrupt("uart")

        # DDR4 PHY ---------------------------------------------------------------------------------
        self.submodules.ddr4_phy = ddr4_phy = USDDR4MIGPHY(platform, platform.request("ddram"))
        self.add_csr("ddr4_phy")

        # SDRAM ------------------------------------------------------------------------------------
        sdram_module = EDY4016A(sys_clk_freq, "1:4")
        self.register_sdram(ddr4_phy,
                            sdram_module.geom_settings,
                            sdram_module.timing_settings,
                            main_ram_size_limit=0x40000000)
        self.add_constant("MEMTEST_DATA_SIZE", 8*1024)
        self.add_constant("MEMTEST_ADDR_SIZE", 8*1024)

# Build --------------------------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Generic LiteX SoC Simulation")
    builder_args(parser)
    soc_sdram_args(parser)
    parser.add_argument("--threads", default=1,
                        help="set number of threads (default=1)")
    parser.add_argument("--trace", action="store_true",
                        help="enable VCD tracing")
    parser.add_argument("--trace-start", default=0,
                        help="cycle to start VCD tracing")
    parser.add_argument("--trace-end", default=-1,
                        help="cycle to end VCD tracing")
    parser.add_argument("--opt-level", default="O0",
                        help="compilation optimization level")
    args = parser.parse_args()

    soc_kwargs = soc_sdram_argdict(args)
    builder_kwargs = builder_argdict(args)

    sim_config = SimConfig(default_clk="sys_clk")
    sim_config.add_module("serial2console", "serial")

    # Configuration --------------------------------------------------------------------------------

    cpu_endianness = "little"
    if "cpu_type" in soc_kwargs:
        if soc_kwargs["cpu_type"] in ["mor1kx", "lm32"]:
            cpu_endianness = "big"

    soc_kwargs["integrated_main_ram_size"] = 0x0

    # SoC ------------------------------------------------------------------------------------------

    soc = SimSoC(**soc_kwargs)

    # Build/Run ------------------------------------------------------------------------------------
    builder_kwargs["csr_csv"] = "csr.csv"
    builder = Builder(soc, **builder_kwargs)
    vns = builder.build(run=False, threads=args.threads, sim_config=sim_config,
        opt_level=args.opt_level,
        trace=args.trace, trace_start=int(args.trace_start), trace_end=int(args.trace_end))
    builder.build(build=False, threads=args.threads, sim_config=sim_config,
        opt_level=args.opt_level,
        trace=args.trace, trace_start=int(args.trace_start), trace_end=int(args.trace_end))


if __name__ == "__main__":
    main()
