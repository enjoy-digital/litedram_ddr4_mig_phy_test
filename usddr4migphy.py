# This file is Copyright (c) 2019 Florent Kermarrec <florent@enjoy-digital.fr>
# License: BSD

import os
import math

from migen import *
from migen.genlib.misc import BitSlip, WaitTimer

from litex.soc.interconnect.csr import *

from litedram.common import *
from litedram.phy.dfi import *


class USDDR4MIGPHY(Module):
    def __init__(self, platform, pads):
        addressbits = len(pads.a) + 3
        bankbits    = len(pads.ba) + len(pads.bg)
        nranks      = 1 if not hasattr(pads, "cs_n") else len(pads.cs_n)
        databits    = len(pads.dq)
        nphases     = 4

        self.init_calib_complete = Signal()

        self.dbg_rd_data_cmp            = Signal(64)
        self.dbg_expected_data          = Signal(64)
        self.dbg_cal_seq                = Signal(3)
        self.dbg_cal_seq_cnt            = Signal(32)
        self.dbg_cal_seq_rd_cnt         = Signal(8)
        self.dbg_rd_valid               = Signal()
        self.dbg_cmp_byte               = Signal(6)
        self.dbg_rd_data                = Signal(64)
        self.dbg_cplx_config            = Signal(16)
        self.dbg_cplx_status            = Signal(2)
        self.dbg_io_address             = Signal(28)
        self.dbg_pllGate                = Signal()
        self.dbg_phy2clb_fixdly_rdy_low = Signal(20)
        self.dbg_phy2clb_fixdly_rdy_upp = Signal(20)
        self.dbg_phy2clb_phy_rdy_low    = Signal(20)
        self.dbg_phy2clb_phy_rdy_upp    = Signal(20)
        self.win_status                 = Signal(32)
        self.cal_r0_status              = Signal(128)
        self.cal_post_status            = Signal(9)
        self.tCWL                       = Signal(6)

        # # #

        rst    = platform.request("cpu_reset")
        clk300 = platform.request("clk300")

        # PHY settings -----------------------------------------------------------------------------
        cl, cwl         = (11, 9)
        cl_sys_latency  = get_sys_latency(nphases, cl)
        cwl_sys_latency = get_sys_latency(nphases, cwl)

        rdcmdphase, rdphase = get_sys_phases(nphases, cl_sys_latency, cl)
        wrcmdphase, wrphase = get_sys_phases(nphases, cwl_sys_latency, cwl)
        self.settings = PhySettings(
            memtype       = "DDR4",
            databits      = databits,
            dfi_databits  = 2*databits,
            nranks        = nranks,
            nphases       = nphases,
            rdphase       = rdphase,
            wrphase       = wrphase,
            rdcmdphase    = rdcmdphase,
            wrcmdphase    = wrcmdphase,
            cl            = cl,
            cwl           = cwl,
            read_latency  = 2 + cl_sys_latency + 1 + 3,
            write_latency = cwl_sys_latency
        )

        # DFI Interface ----------------------------------------------------------------------------
        self.dfi = Interface(addressbits, bankbits, nranks, 2*databits, nphases)
        dfi = Interface(addressbits, bankbits, nranks, 2*databits, nphases)
        self.submodules += DDR4DFIMux(self.dfi, dfi)

        cas_slot = Signal(2)

        self.specials += Instance("ddr4_0",
            # Clk/Rst ------------------------------------------------------------------------------
            i_sys_rst                 = rst,
            i_c0_sys_clk_p            = clk300.p,
            i_c0_sys_clk_n            = clk300.n,
            o_c0_ddr4_ui_clk          = ClockSignal("sys"),
            o_c0_ddr4_ui_clk_sync_rst = ResetSignal("sys"),

            # DRAM pads ----------------------------------------------------------------------------
            o_c0_ddr4_act_n     = pads.act_n,
            o_c0_ddr4_adr       = Cat(pads.a, pads.we_n, pads.cas_n, pads.ras_n),
            o_c0_ddr4_ba        = pads.ba,
            o_c0_ddr4_bg        = pads.bg,
            o_c0_ddr4_cke       = pads.cke,
            o_c0_ddr4_odt       = pads.odt,
            o_c0_ddr4_cs_n      = pads.cs_n,
            o_c0_ddr4_ck_t      = pads.clk_p,
            o_c0_ddr4_ck_c      = pads.clk_n,
            o_c0_ddr4_reset_n   = pads.reset_n,
            io_c0_ddr4_dm_dbi_n = pads.dm,
            io_c0_ddr4_dq       = pads.dq,
            io_c0_ddr4_dqs_c    = pads.dqs_n,
            io_c0_ddr4_dqs_t    = pads.dqs_p,

            # Calibration --------------------------------------------------------------------------
            o_c0_init_calib_complete = self.init_calib_complete,

            # Debug --------------------------------------------------------------------------------
            #o_dbg_clk=,
            o_dbg_rd_data_cmp            = self.dbg_rd_data_cmp,
            o_dbg_expected_data          = self.dbg_expected_data,
            o_dbg_cal_seq                = self.dbg_cal_seq,
            o_dbg_cal_seq_cnt            = self.dbg_cal_seq_cnt,
            o_dbg_cal_seq_rd_cnt         = self.dbg_cal_seq_rd_cnt,
            o_dbg_rd_valid               = self.dbg_rd_valid,
            o_dbg_cmp_byte               = self.dbg_cmp_byte,
            o_dbg_rd_data                = self.dbg_rd_data,
            o_dbg_cplx_config            = self.dbg_cplx_config,
            o_dbg_cplx_status            = self.dbg_cplx_status,
            o_dbg_io_address             = self.dbg_io_address,
            o_dbg_pllGate                = self.dbg_pllGate,
            o_dbg_phy2clb_fixdly_rdy_low = self.dbg_phy2clb_fixdly_rdy_low,
            o_dbg_phy2clb_fixdly_rdy_upp = self.dbg_phy2clb_fixdly_rdy_upp,
            o_dbg_phy2clb_phy_rdy_low    = self.dbg_phy2clb_phy_rdy_low,
            o_dbg_phy2clb_phy_rdy_upp    = self.dbg_phy2clb_phy_rdy_upp,
            o_win_status                 = self.win_status,
            o_cal_r0_status              = self.cal_r0_status,
            o_cal_post_status            = self.cal_post_status,

            # PHY Statics / Optionals --------------------------------------------------------------
            i_dBufAdr       = 0,           # Reserved, should be tied low
            o_wrDataAddr    = Signal(5),   # Not used (optional)
            o_rdDataAddr    = Signal(5),   # Not used (optional)
            o_per_rd_done   = Signal(),    # Not used (optional)
            o_rmw_rd_done   = Signal(),    # Not used (optional)
            i_winInjTxn     = 0,           # Not used (optional)
            i_winRmw        = 0,           # Not used (optional)
            i_gt_data_ready = 0,           # Not used (optional)
            o_dbg_bus       = Signal(512), # Not used (optional)
            o_tCWL          = self.tCWL,   # tCWL, FIXME: add check with internal tCWL
            i_winRank       = 0,           # Tied to 0 for single-rank systems, FIXME for dual-rank
            i_winBuf        = 0,           # Not used (optional)

            # PHY Commands -------------------------------------------------------------------------
            i_mc_ACT_n  = Cat(
                getattr(dfi.phases[0], "act_n"), getattr(dfi.phases[0], "act_n"),
                getattr(dfi.phases[1], "act_n"), getattr(dfi.phases[1], "act_n"),
                getattr(dfi.phases[2], "act_n"), getattr(dfi.phases[2], "act_n"),
                getattr(dfi.phases[3], "act_n"), getattr(dfi.phases[3], "act_n")),
            i_mc_ADR    = 0,
            i_mc_BA     = 0,
            i_mc_BG     = 0,
            i_mc_CS_n   = Cat(
                getattr(dfi.phases[0], "cs_n"), getattr(dfi.phases[0], "cs_n"),
                getattr(dfi.phases[1], "cs_n"), getattr(dfi.phases[1], "cs_n"),
                getattr(dfi.phases[2], "cs_n"), getattr(dfi.phases[2], "cs_n"),
                getattr(dfi.phases[3], "cs_n"), getattr(dfi.phases[3], "cs_n")),
            i_mc_ODT    = Cat(
                getattr(dfi.phases[0], "odt"), getattr(dfi.phases[0], "odt"),
                getattr(dfi.phases[1], "odt"), getattr(dfi.phases[1], "odt"),
                getattr(dfi.phases[2], "odt"), getattr(dfi.phases[2], "odt"),
                getattr(dfi.phases[3], "odt"), getattr(dfi.phases[3], "odt")),
            i_mc_CKE    = Cat(
                getattr(dfi.phases[0], "cke"), getattr(dfi.phases[0], "cke"),
                getattr(dfi.phases[1], "cke"), getattr(dfi.phases[1], "cke"),
                getattr(dfi.phases[2], "cke"), getattr(dfi.phases[2], "cke"),
                getattr(dfi.phases[3], "cke"), getattr(dfi.phases[3], "cke")),
            i_mcCasSlot  = cas_slot, # FIXME: generate cas_slot
            i_mcCasSlot2 = cas_slot[1],
            i_mcRdCAS    = 0,
            i_mcWrCAS    = 0,

            # PHY Writes ---------------------------------------------------------------------------
            i_wrData     = 0,
            i_wrDataMask = 0,
            #o_wrDataEn  =,

            # PHY Reads ----------------------------------------------------------------------------
            #o_rdData   =,
            #o_rdDataEn =,
        )
        platform.add_source(os.path.join("ip", "ddr4_0", "ddr4_0.dcp"))
        #platform.add_ip(os.path.join("ip", "ddr4_0", "ddr4_0.xci"))
