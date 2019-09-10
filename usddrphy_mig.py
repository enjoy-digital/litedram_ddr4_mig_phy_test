# This file is Copyright (c) 2019 Florent Kermarrec <florent@enjoy-digital.fr>
# License: BSD

import os

from migen import *


class USDDRPHY(Module):
    def __init__(self, platform, pads):

        # # #

        self.clock_domains.cd_dbg = ClockDomain()

        sys_rst = platform.request("cpu_reset")
        sys_clk = platform.request("clk300")

        self.c0_ddr4_ui_clk = Signal()
        self.c0_ddr4_ui_clk_sync_rst = Signal()
        self.c0_init_calib_complete = Signal()

        self.dbg_clk = Signal()
        self.dbg_rd_data_cmp = Signal(64)
        self.dbg_expected_data = Signal(64)
        self.dbg_cal_seq = Signal(3)
        self.dbg_cal_seq_cnt = Signal(32)
        self.dbg_cal_seq_rd_cnt = Signal(8)
        self.dbg_rd_valid = Signal()
        self.dbg_cmp_byte = Signal(6)
        self.dbg_rd_data = Signal(64)
        self.dbg_cplx_config = Signal(16)
        self.dbg_cplx_status = Signal(2)
        self.dbg_io_address = Signal(28)
        self.dbg_pllGate = Signal()
        self.dbg_phy2clb_fixdly_rdy_low = Signal(20)
        self.dbg_phy2clb_fixdly_rdy_upp = Signal(20)
        self.dbg_phy2clb_phy_rdy_low = Signal(20)
        self.dbg_phy2clb_phy_rdy_upp = Signal(20)
        self.win_status = Signal(32)
        self.cal_r0_status = Signal(128)
        self.cal_post_status = Signal(9)
        self.tCWL = Signal(6)

        self.dBufAdr = Signal(5)
        self.wrData = Signal(512)
        self.wrDataMask = Signal(64)
        self.wrDataEn = Signal()
        self.mc_ACT_n = Signal(8)
        self.mc_ADR = Signal(136)
        self.mc_BA = Signal(16)
        self.mc_BG = Signal(8)
        self.mc_CS_n = Signal(8)
        self.mc_ODT = Signal(8)
        self.mcRdCAS = Signal()
        self.mcWrCAS = Signal()
        self.winRank = Signal(2)
        self.winBuf = Signal(5)
        self.rdData = Signal(512)
        self.rdDataEn = Signal()
        self.rdDataEnd = Signal()
        self.compare_error = Signal()
        self.wr_rd_complete = Signal()

        # # #

        self.specials += Instance("example_tb_phy",
            i_clk=self.c0_ddr4_ui_clk,
            i_rst=self.c0_ddr4_ui_clk_sync_rst,
            i_init_calib_complete=self.c0_init_calib_complete,
            o_dBufAdr=self.dBufAdr,
            o_wrData=self.wrData,
            o_wrDataMask=self.wrDataMask,
            i_wrDataEn=self.wrDataEn,
            o_mc_ACT_n=self.mc_ACT_n,
            o_mc_ADR=self.mc_ADR,
            o_mc_BA=self.mc_BA,
            o_mc_BG=self.mc_BG,
            o_mc_CS_n=self.mc_CS_n,
            o_mc_ODT=self.mc_ODT,
            o_mcRdCAS=self.mcRdCAS,
            o_mcWrCAS=self.mcWrCAS,
            o_winRank=self.winRank,
            o_winBuf=self.winBuf,
            i_rdData=self.rdData,
            i_rdDataEn=self.rdDataEn,
            i_rdDataEnd=self.rdDataEnd,
            o_compare_error=self.compare_error,
            o_wr_rd_complete=self.wr_rd_complete,
        )

        self.specials += Instance("ddr4_0",
            # Clk/Rst ------------------------------------------------------------------------------
            i_sys_rst=sys_rst,
            i_c0_sys_clk_p=sys_clk.p,
            i_c0_sys_clk_n=sys_clk.n,
            o_c0_ddr4_ui_clk=self.c0_ddr4_ui_clk,
            o_c0_ddr4_ui_clk_sync_rst=self.c0_ddr4_ui_clk_sync_rst,

            # DRAM pads ----------------------------------------------------------------------------
            o_c0_ddr4_act_n=pads.act_n,
            o_c0_ddr4_adr=Cat(pads.a, pads.we_n, pads.cas_n, pads.ras_n),
            o_c0_ddr4_ba=pads.ba,
            o_c0_ddr4_bg=pads.bg,
            o_c0_ddr4_cke=pads.cke,
            o_c0_ddr4_odt=pads.odt,
            o_c0_ddr4_cs_n=pads.cs_n,
            o_c0_ddr4_ck_t=pads.clk_p,
            o_c0_ddr4_ck_c=pads.clk_n,
            o_c0_ddr4_reset_n=pads.reset_n,
            io_c0_ddr4_dm_dbi_n=pads.dm,
            io_c0_ddr4_dq=pads.dq,
            io_c0_ddr4_dqs_c=pads.dqs_n,
            io_c0_ddr4_dqs_t=pads.dqs_p,


            # Calibration --------------------------------------------------------------------------
            o_c0_init_calib_complete=self.c0_init_calib_complete,

            # Debug --------------------------------------------------------------------------------
            o_dbg_clk=ClockSignal("dbg"),
            o_dbg_rd_data_cmp=self.dbg_rd_data_cmp,
            o_dbg_expected_data=self.dbg_expected_data,
            o_dbg_cal_seq=self.dbg_cal_seq,
            o_dbg_cal_seq_cnt=self.dbg_cal_seq_cnt,
            o_dbg_cal_seq_rd_cnt=self.dbg_cal_seq_rd_cnt,
            o_dbg_rd_valid=self.dbg_rd_valid,
            o_dbg_cmp_byte=self.dbg_cmp_byte,
            o_dbg_rd_data=self.dbg_rd_data,
            o_dbg_cplx_config=self.dbg_cplx_config,
            o_dbg_cplx_status=self.dbg_cplx_status,
            o_dbg_io_address=self.dbg_io_address,
            o_dbg_pllGate=self.dbg_pllGate,
            o_dbg_phy2clb_fixdly_rdy_low=self.dbg_phy2clb_fixdly_rdy_low,
            o_dbg_phy2clb_fixdly_rdy_upp=self.dbg_phy2clb_fixdly_rdy_upp,
            o_dbg_phy2clb_phy_rdy_low=self.dbg_phy2clb_phy_rdy_low,
            o_dbg_phy2clb_phy_rdy_upp=self.dbg_phy2clb_phy_rdy_upp,
            o_win_status=self.win_status,
            o_cal_r0_status=self.cal_r0_status,
            o_cal_post_status=self.cal_post_status,
            #o_dbg_bus=,
            o_tCWL=self.tCWL,

            # Memory Controller Interface ----------------------------------------------------------
            i_dBufAdr=self.dBufAdr,
            i_wrData=self.wrData,
            i_wrDataMask=self.wrDataMask,
            o_wrDataEn=self.wrDataEn,
            i_mc_ACT_n=self.mc_ACT_n,
            i_mc_ADR=self.mc_ADR,
            i_mc_BA=self.mc_BA,
            i_mc_BG=self.mc_BG,
            i_mc_CS_n=self.mc_CS_n,
            i_mc_ODT=self.mc_ODT,
            i_mcRdCAS=self.mcRdCAS,
            i_mcWrCAS=self.mcWrCAS,
            i_winRank=self.winRank,
            i_winBuf=self.winBuf,
            o_rdData=self.rdData,
            o_rdDataEn=self.rdDataEn,
            o_rdDataEnd=self.rdDataEnd,

            #o_rdDataAddr=,
            #o_per_rd_done=,
            #o_rmw_rd_done=,
            i_mc_CKE=0b11111111,
            i_mcCasSlot=0,
            i_winInjTxn=0,
            i_winRmw=0,
            i_gt_data_ready=0,
        )
        platform.add_source(os.path.join("ip", "ddrx_cal_mc_odt.sv"))
        platform.add_source(os.path.join("ip", "example_tb_phy.sv"))
        platform.add_source(os.path.join("ip", "ddr4_0", "ddr4_0.dcp"))
        #platform.add_ip(os.path.join("ip", "ddr4_0", "ddr4_0.xci"))
