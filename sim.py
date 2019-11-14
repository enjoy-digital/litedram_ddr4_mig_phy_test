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

from litedram.common import PhySettings
from litedram.modules import MT48LC16M16
from litedram.phy.model import SDRAMPHYModel


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
    def __init__(self, with_sdram=True, **kwargs):
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

        # SDRAM ------------------------------------------------------------------------------------
        if with_sdram:
            sdram_module =  MT48LC16M16(100e6, "1:1") # use 100MHz timings
            phy_settings = PhySettings(
                memtype       = "SDR",
                databits      = 32,
                dfi_databits  = 16,
                nphases       = 1,
                rdphase       = 0,
                wrphase       = 0,
                rdcmdphase    = 0,
                wrcmdphase    = 0,
                cl            = 2,
                read_latency  = 4,
                write_latency = 0
            )
            self.submodules.sdrphy = SDRAMPHYModel(sdram_module, phy_settings)
            self.register_sdram(
                self.sdrphy,
                sdram_module.geom_settings,
                sdram_module.timing_settings)
            # Reduce memtest size for simulation speedup
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
    parser.add_argument("--opt-level", default="O3",
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
