# This file is Copyright (c) 2019 Florent Kermarrec <florent@enjoy-digital.fr>
# License: BSD

import math
from collections import OrderedDict

from migen import *
from migen.genlib.misc import BitSlip, WaitTimer

from litex.soc.interconnect.csr import *

from litedram.common import PhySettings
from litedram.phy.dfi import *


class USDDRPHY(Module, AutoCSR):
    def __init__(self, pads, memtype="DDR4", sys_clk_freq=100e6, iodelay_clk_freq=200e6, cmd_latency=0):
        tck = 2/(2*4*sys_clk_freq)
        addressbits = len(pads.a)
        if memtype == "DDR4":
            addressbits += 3 # cas_n/ras_n/we_n multiplexed with address
        bankbits = len(pads.ba) if memtype == "DDR3" else len(pads.ba) + len(pads.bg)
        nranks = 1 if not hasattr(pads, "cs_n") else len(pads.cs_n)
        databits = len(pads.dq)
        nphases = 4

        # compute phy settings
        cl, cwl = get_cl_cw(memtype, tck)
        cwl = cwl + cmd_latency
        cl_sys_latency = get_sys_latency(nphases, cl)
        cwl_sys_latency = get_sys_latency(nphases, cwl)

        rdcmdphase, rdphase = get_sys_phases(nphases, cl_sys_latency, cl)
        wrcmdphase, wrphase = get_sys_phases(nphases, cwl_sys_latency, cwl)
        self.settings = PhySettings(
            memtype=memtype,
            databits=databits,
            dfi_databits=2*databits,
            nranks=nranks,
            nphases=nphases,
            rdphase=rdphase,
            wrphase=wrphase,
            rdcmdphase=rdcmdphase,
            wrcmdphase=wrcmdphase,
            cl=cl,
            cwl=cwl - cmd_latency,
            read_latency=2 + cl_sys_latency + 1 + 3,
            write_latency=cwl_sys_latency
        )

#        self.dfi = Interface(addressbits, bankbits, nranks, 2*databits, nphases)
#        if memtype == "DDR3":
#            _dfi = self.dfi
#        else:
#            _dfi = Interface(addressbits, bankbits, nranks, 2*databits, nphases)
#            dfi_mux = DDR4DFIMux(self.dfi, _dfi)
#            self.submodules += dfi_mux

        # # #

        self.specials += Instance("ddr4_0",
            i_sys_rst=,
            i_c0_sys_clk_p=,
            i_c0_sys_clk_n=,
            o_c0_ddr4_ui_clk=,
            o_c0_ddr4_ui_clk_sync_rst=,
            o_c0_init_calib_complete=,

            o_dbg_clk=,
            o_dbg_rd_data_cmp=,
            o_dbg_expected_data=,
            o_dbg_cal_seq=,
            o_dbg_cal_seq_cnt=,
            o_dbg_cal_seq_rd_cnt=,
            o_dbg_rd_valid=,
            o_dbg_cmp_byte=,
            o_dbg_rd_data=,
            o_dbg_cplx_config=,
            o_dbg_cplx_status=,
            o_dbg_io_address=,
            o_dbg_pllGate=,
            o_dbg_phy2clb_fixdly_rdy_low=,
            o_dbg_phy2clb_fixdly_rdy_upp=,
            o_dbg_phy2clb_phy_rdy_low=,
            o_dbg_phy2clb_phy_rdy_upp=,
            o_win_status=,
            o_cal_r0_status=,
            o_cal_post_status=,

            o_addn_ui_clkout1=,

            o_c0_ddr4_act_n=,
            o_c0_ddr4_adr=,
            o_c0_ddr4_ba=,
            o_c0_ddr4_bg=,
            o_c0_ddr4_cke=,
            o_c0_ddr4_odt=,
            o_c0_ddr4_cs_n=,
            o_c0_ddr4_ck_t=,
            o_c0_ddr4_ck_c=,
            o_c0_ddr4_reset_n=,
            io_c0_ddr4_dm_dbi_n=,
            io_c0_ddr4_dq=,
            io_c0_ddr4_dqs_c=,
            io_c0_ddr4_dqs_t=,

            i_dBufAdr=,
            i_wrData=,
            i_wrDataMask=,
            o_rdData=,
            o_rdDataAddr=,
            o_rdDataEn=,
            o_rdDataEnd=,
            o_per_rd_done=,
            o_rmw_rd_done=,
            o_wrDataAddr=,
            o_wrDataEn=,

            i_mc_ACT_n=,
            i_mc_ADR=,
            i_mc_BA=,
            i_mc_BG=,
            i_mc_CKE=,
            i_mc_CS_n=,
            i_mc_ODT=,
            i_mcCasSlot=,
            i_mcCasSlot2=,
            i_mcRdCAS=,
            i_mcWrCAS=,
            i_winInjTxn=,
            i_winRmw=,
            i_gt_data_ready=,
            i_winBuf=,
            i_winRank=,
            o_tCWL=,
            o_dbg_bus=,
        )
