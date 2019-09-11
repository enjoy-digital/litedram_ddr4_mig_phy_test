# This file is Copyright (c) 2019 Florent Kermarrec <florent@enjoy-digital.fr>
# License: BSD

import os
import math

from migen import *
from migen.genlib.misc import BitSlip, WaitTimer

from litex.soc.interconnect.csr import *

from litedram.common import *
from litedram.phy.dfi import *

# Xilinx Ultrascale DDR4 MIG PHY -------------------------------------------------------------------

class USDDR4MIGPHY(Module, AutoCSR):
    def __init__(self, platform, pads):
        addressbits = len(pads.a) + 3
        bankbits    = len(pads.ba) + len(pads.bg)
        nranks      = 1 if not hasattr(pads, "cs_n") else len(pads.cs_n)
        databits    = len(pads.dq)
        nphases     = 4

        self.init_calib_complete        = Signal()
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

        self.calib_done = CSRStatus()
        self.comb += self.calib_done.status.eq(self.init_calib_complete)

        # # #

        rst    = platform.request("cpu_reset")
        clk300 = platform.request("clk300")

        # PHY settings -----------------------------------------------------------------------------
        cl, cwl         = (11, 9)
        cl_sys_latency  = get_sys_latency(nphases, cl)
        cwl_sys_latency = get_sys_latency(nphases, cwl)

        rdcmdphase, rdphase = get_sys_phases(nphases, cl_sys_latency, cl)
        wrcmdphase, wrphase = get_sys_phases(nphases, cwl_sys_latency, cwl)

        cwl_sys_latency = cwl_sys_latency - 2 # FUXME
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
            read_latency  = cl_sys_latency + 10, # FIXME
            write_latency = cwl_sys_latency
        )

        # DFI Interface ----------------------------------------------------------------------------
        self.dfi = Interface(addressbits, bankbits, nranks, 2*databits, nphases)
        dfi = Interface(addressbits, bankbits, nranks, 2*databits, nphases)
        self.submodules += DDR4DFIMux(self.dfi, dfi)

        mc_rd_cas   = Signal()
        mc_wr_cas   = Signal()
        mc_cas_slot = Signal(2)
        self.comb += [
            mc_rd_cas.eq(dfi.phases[self.settings.rdphase].rddata_en),
            mc_wr_cas.eq(dfi.phases[self.settings.wrphase].wrdata_en),
            If(mc_rd_cas,
                mc_cas_slot.eq(rdcmdphase), # FIXME; should only supporting CAS slots?
            ),
            If(mc_wr_cas,
                mc_cas_slot.eq(wrcmdphase), # FIXME: should only supporting CAS slots?
            ),
        ]

        # FIXME: drive
        wr_data      = Cat(Cat(
            dfi.phases[0].wrdata[i], dfi.phases[0].wrdata[databits+i],
            dfi.phases[1].wrdata[i], dfi.phases[1].wrdata[databits+i],
            dfi.phases[2].wrdata[i], dfi.phases[2].wrdata[databits+i],
            dfi.phases[3].wrdata[i], dfi.phases[3].wrdata[databits+i]) for i in range(databits))
        wr_data_mask = Signal(512//8)
        wr_data_en   = Signal()

        # FIXME: drive
        rd_data      = Cat(Cat(
            dfi.phases[0].rddata[i], dfi.phases[0].rddata[databits+i],
            dfi.phases[1].rddata[i], dfi.phases[1].rddata[databits+i],
            dfi.phases[2].rddata[i], dfi.phases[2].rddata[databits+i],
            dfi.phases[3].rddata[i], dfi.phases[3].rddata[databits+i]) for i in range(databits))
        rd_data_en   = Signal()

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
                dfi.phases[0].act_n, dfi.phases[0].act_n,
                dfi.phases[1].act_n, dfi.phases[1].act_n,
                dfi.phases[2].act_n, dfi.phases[2].act_n,
                dfi.phases[3].act_n, dfi.phases[3].act_n),
            i_mc_ADR    = Cat(Cat(
                dfi.phases[0].address[i], dfi.phases[0].address[i],
                dfi.phases[1].address[i], dfi.phases[1].address[i],
                dfi.phases[2].address[i], dfi.phases[2].address[i],
                dfi.phases[3].address[i], dfi.phases[3].address[i])
                for i in range(addressbits)),
            i_mc_BA     = Cat(Cat(
                dfi.phases[0].bank[i], dfi.phases[0].bank[i],
                dfi.phases[1].bank[i], dfi.phases[1].bank[i],
                dfi.phases[2].bank[i], dfi.phases[2].bank[i],
                dfi.phases[3].bank[i], dfi.phases[3].bank[i])
                for i in range(len(pads.ba))),
            i_mc_BG     = Cat(Cat(
                dfi.phases[0].bank[i], dfi.phases[0].bank[i],
                dfi.phases[1].bank[i], dfi.phases[1].bank[i],
                dfi.phases[2].bank[i], dfi.phases[2].bank[i],
                dfi.phases[3].bank[i], dfi.phases[3].bank[i])
                for i in range(len(pads.ba), len(pads.ba) + len(pads.bg))),
            i_mc_CS_n   = Cat(
                dfi.phases[0].cs_n, dfi.phases[0].cs_n,
                dfi.phases[1].cs_n, dfi.phases[1].cs_n,
                dfi.phases[2].cs_n, dfi.phases[2].cs_n,
                dfi.phases[3].cs_n, dfi.phases[3].cs_n),
            i_mc_ODT    = Cat(
                dfi.phases[0].odt, dfi.phases[0].odt,
                dfi.phases[1].odt, dfi.phases[1].odt,
                dfi.phases[2].odt, dfi.phases[2].odt,
                dfi.phases[3].odt, dfi.phases[3].odt),
            i_mc_CKE    = Cat(
                dfi.phases[0].cke, dfi.phases[0].cke,
                dfi.phases[1].cke, dfi.phases[1].cke,
                dfi.phases[2].cke, dfi.phases[2].cke,
                dfi.phases[3].cke, dfi.phases[3].cke),
            i_mcCasSlot  = mc_cas_slot, # FIXME: generate cas_slot
            i_mcCasSlot2 = mc_cas_slot[1],
            i_mcRdCAS    = mc_rd_cas,
            i_mcWrCAS    = mc_wr_cas,

            # PHY Writes ---------------------------------------------------------------------------
            i_wrData     = wr_data,
            i_wrDataMask = wr_data_mask,
            o_wrDataEn   = wr_data_en,

            # PHY Reads ----------------------------------------------------------------------------
            o_rdData   = rd_data,
            o_rdDataEn = rd_data_en,
        )
        platform.add_source(os.path.join("ip", "ddr4_0", "ddr4_0.dcp"))
        #platform.add_ip(os.path.join("ip", "ddr4_0", "ddr4_0.xci"))

        # Flow Control (for debug) -----------------------------------------------------------------
        rddata_en = dfi.phases[self.settings.rdphase].rddata_en
        for i in range(self.settings.read_latency-1):
            n_rddata_en = Signal()
            self.sync += n_rddata_en.eq(rddata_en)
            rddata_en = n_rddata_en

        wrdata_en = Signal()
        last_wrdata_en = Signal(cwl_sys_latency+2)
        wrphase = dfi.phases[self.settings.wrphase]
        self.sync += last_wrdata_en.eq(Cat(wrphase.wrdata_en, last_wrdata_en[:-1]))
        self.comb += wrdata_en.eq(last_wrdata_en[cwl_sys_latency])

        # Debug ------------------------------------------------------------------------------------
        _wr_data = Signal(8)
        _rd_data = Signal(8)
        self.comb += [
            _wr_data.eq(wr_data),
            _rd_data.eq(rd_data),
        ]

        self.mc_rd_cas  = mc_rd_cas
        self.mc_wr_cas  = mc_wr_cas
        self.wr_data    = _wr_data
        self.wr_data_en = wr_data_en
        self.rd_data    = _rd_data
        self.rd_data_en = rd_data_en

        self.core_rddata_en = rddata_en
        self.core_wrdata_en = wrdata_en
