
/******************************************************************************
// (c) Copyright 2013 - 2014 Xilinx, Inc. All rights reserved.
//
// This file contains confidential and proprietary information
// of Xilinx, Inc. and is protected under U.S. and
// international copyright and other intellectual property
// laws.
//
// DISCLAIMER
// This disclaimer is not a license and does not grant any
// rights to the materials distributed herewith. Except as
// otherwise provided in a valid license issued to you by
// Xilinx, and to the maximum extent permitted by applicable
// law: (1) THESE MATERIALS ARE MADE AVAILABLE "AS IS" AND
// WITH ALL FAULTS, AND XILINX HEREBY DISCLAIMS ALL WARRANTIES
// AND CONDITIONS, EXPRESS, IMPLIED, OR STATUTORY, INCLUDING
// BUT NOT LIMITED TO WARRANTIES OF MERCHANTABILITY, NON-
// INFRINGEMENT, OR FITNESS FOR ANY PARTICULAR PURPOSE; and
// (2) Xilinx shall not be liable (whether in contract or tort,
// including negligence, or under any other theory of
// liability) for any loss or damage of any kind or nature
// related to, arising under or in connection with these
// materials, including for any direct, or any indirect,
// special, incidental, or consequential loss or damage
// (including loss of data, profits, goodwill, or any type of
// loss or damage suffered as a result of any action brought
// by a third party) even if such damage or loss was
// reasonably foreseeable or Xilinx had been advised of the
// possibility of the same.
//
// CRITICAL APPLICATIONS
// Xilinx products are not designed or intended to be fail-
// safe, or for use in any application requiring fail-safe
// performance, such as life-support or safety devices or
// systems, Class III medical devices, nuclear facilities,
// applications related to the deployment of airbags, or any
// other applications that could lead to death, personal
// injury, or severe property or environmental damage
// (individually and collectively, "Critical
// Applications"). Customer assumes the sole risk and
// liability of any use of Xilinx products in Critical
// Applications, subject only to applicable laws and
// regulations governing limitations on product liability.
//
// THIS COPYRIGHT NOTICE AND DISCLAIMER MUST BE RETAINED AS
// PART OF THIS FILE AT ALL TIMES.
******************************************************************************/
//   ____  ____
//  /   /\/   /
// /___/  \  /    Vendor             : Xilinx
// \   \   \/     Version            : 1.0
//  \   \         Application        : DDR4_SDRAM_PHY
//  /   /         Filename           : ddr4_0.v
// /___/   /\     Date Last Modified : $Date: 2011/06/17 11:11:25 $
// \   \  /  \    Date Created       : Thu Apr 18 2013
//  \___\/\___\
//
// Device           : UltraScale
// Design Name      : DDR4_SDRAM
// Purpose          :
//   Wrapper module for the user design top level file. This module can be 
//   instantiated in the system and interconnect as shown in example design 
//   (example_top module).
// Reference        :
// Revision History :
//*****************************************************************************

`timescale 1ns/1ps

(* CORE_GENERATION_INFO = "DDR4_SDRAM_PHY, DDR4_SDRAM_PHY,{x_ipProduct=Vivado 2017.2.0,x_ipVendor=xilinx.com,x_ipLibrary=ip,x_ipName=DDR4_SDRAM,x_ipVersion=2.2, Controller_Type = DDR4_SDRAM, Time_Period = 833, Input_Clock_Period = 3332, Memory_Type = Components, Memory_Part = EDY4016AABG-DR-F, Cas_Latency = 16, Cas_Write_Latency = 12, DQ_Width = 64, Chip_Select = true, Data_Mask = DM_NO_DBI, Slot_cofiguration =  Single , Clamshell_cofiguration =  false ,IS_FASTER_SPEED_RAM = No, Is_custom_part = false,Memory_Voltage = 1.2V, Phy_Only = Phy_Only_Single, Debug_Port = Enable, Burst_Length = 8, System_Clock = Differential, AXI_Selection = false, AXI_Data_Width = 64,  AXI_ArbitrationScheme = RD_PRI_REG, AXI_Narrow_Burst = false, Simulation_Mode = BFM, Debug_Mode = Enable, Example_TG = SIMPLE_TG, Self_Refresh = false, Save_Restore = false, MicroBlaze_ECC = false,  Specify_MandD = false, CLKBOUT_MULT = 4, DIVCLK_DIVIDE = 1, CLKOUT0_DIVIDE = 4}" *)
(* X_CORE_INFO = "ddr4_v2_2_5,Vivado 2018.2" *)
module ddr4_0
   (
    input                             sys_rst,
    input                             c0_sys_clk_p,
    input                             c0_sys_clk_n,
    output                            c0_ddr4_ui_clk,
    output                            c0_ddr4_ui_clk_sync_rst,
    output                            dbg_clk,
   // debug ports
    output [63:0]                     dbg_rd_data_cmp,
    output [63:0]                     dbg_expected_data,
    output wire [2:0]                 dbg_cal_seq,
    output wire [31:0]                dbg_cal_seq_cnt,
    output wire [7:0]                 dbg_cal_seq_rd_cnt,
    output wire                       dbg_rd_valid,
    output wire [5:0]                 dbg_cmp_byte,
    output wire [63:0]                dbg_rd_data,
    output wire [15:0]                dbg_cplx_config,
    output wire [1:0]                 dbg_cplx_status,
    output wire [27:0]                dbg_io_address,
    output wire                       dbg_pllGate,
    output wire [19:0]                dbg_phy2clb_fixdly_rdy_low,
    output wire [19:0]                dbg_phy2clb_fixdly_rdy_upp,
    output wire [19:0]                dbg_phy2clb_phy_rdy_low,
    output wire [19:0]                dbg_phy2clb_phy_rdy_upp,
    output wire [31:0]                win_status,
    output wire [127:0]               cal_r0_status,
    output wire [8:0]                 cal_post_status,
   // iob<>DDR4 signals
    output                            c0_ddr4_act_n,

    output               [16:0]       c0_ddr4_adr,
    output      [1:0]      c0_ddr4_ba,
    output [0:0]     c0_ddr4_bg,
    output        [0:0]     c0_ddr4_cke,
    output        [0:0]     c0_ddr4_odt,
    output        [0:0]      c0_ddr4_cs_n,
    output        [0:0]    c0_ddr4_ck_t,
    output        [0:0]    c0_ddr4_ck_c,
    output                            c0_ddr4_reset_n,
    inout         [7:0]      c0_ddr4_dm_dbi_n,
    inout          [63:0]     c0_ddr4_dq,
    inout        [7:0]      c0_ddr4_dqs_c,
    inout        [7:0]      c0_ddr4_dqs_t,

    output                            c0_init_calib_complete,

   output                             addn_ui_clkout1,

   // native<emcCal signals
    input  [4:0]  dBufAdr,
    input           [511:0]  wrData,
    input           [63:0]  wrDataMask,
    
    output          [511:0]  rdData,
    output [4:0]                     rdDataAddr,
    output [0:0]                           rdDataEn,
    output [0:0]                           rdDataEnd,
    output [0:0]                           per_rd_done,
    output [0:0]                           rmw_rd_done,
    output [4:0]                         wrDataAddr,
    output [0:0]                           wrDataEn,

    input                      [7:0]  mc_ACT_n,
    input         [135:0]  mc_ADR,
    input         [15:0]  mc_BA,
    input                  [7:0]  mc_BG,
    input                  [7:0]  mc_CKE,
      input                  [7:0]  mc_CS_n,
    input                  [7:0]  mc_ODT,
    input  [1:0]                      mcCasSlot,
    input  [0:0]                           mcCasSlot2,
    input  [0:0]                           mcRdCAS,
    input  [0:0]                           mcWrCAS,
    input  [0:0]                           winInjTxn,
    input  [0:0]                           winRmw,
    input                             gt_data_ready,
    input  [4:0]                      winBuf,
    input  [1:0]                      winRank,

    output [5:0]                      tCWL,
    // Debug Port
    output wire [511:0]               dbg_bus

);

ddr4_0_ddr4 inst
    (
     .sys_rst                 (sys_rst),
     .c0_sys_clk_p            (c0_sys_clk_p),
     .c0_sys_clk_n            (c0_sys_clk_n),
     .c0_ddr4_ui_clk          (c0_ddr4_ui_clk),
     .c0_ddr4_ui_clk_sync_rst (c0_ddr4_ui_clk_sync_rst),
     .c0_init_calib_complete  (c0_init_calib_complete),

   .addn_ui_clkout1           (addn_ui_clkout1),
   .addn_ui_clkout2           (),
   .addn_ui_clkout3           (),
   .addn_ui_clkout4           (),
     .dbg_clk                 (dbg_clk),
     .dbg_rd_data_cmp             (dbg_rd_data_cmp),
     .dbg_expected_data           (dbg_expected_data),
     .dbg_cal_seq                 (dbg_cal_seq               ),
     .dbg_cal_seq_cnt             (dbg_cal_seq_cnt           ),
     .dbg_cal_seq_rd_cnt          (dbg_cal_seq_rd_cnt        ),
     .dbg_rd_valid                (dbg_rd_valid              ),
     .dbg_cmp_byte                (dbg_cmp_byte              ),
     .dbg_rd_data                 (dbg_rd_data               ),
     .dbg_cplx_config             (dbg_cplx_config           ),
     .dbg_cplx_status             (dbg_cplx_status           ),
     .dbg_io_address              (dbg_io_address            ),
     .dbg_pllGate                 (dbg_pllGate               ),
     .dbg_phy2clb_fixdly_rdy_low  (dbg_phy2clb_fixdly_rdy_low),
     .dbg_phy2clb_fixdly_rdy_upp  (dbg_phy2clb_fixdly_rdy_upp),
     .dbg_phy2clb_phy_rdy_low     (dbg_phy2clb_phy_rdy_low   ),
     .dbg_phy2clb_phy_rdy_upp     (dbg_phy2clb_phy_rdy_upp   ),
     .win_status                  (win_status                ),
     .cal_r0_status               (cal_r0_status),
     .cal_post_status             (cal_post_status),

     .c0_ddr4_act_n           (c0_ddr4_act_n),
     .c0_ddr4_adr             (c0_ddr4_adr),
     .c0_ddr4_ba              (c0_ddr4_ba),
     .c0_ddr4_bg              (c0_ddr4_bg),
     .c0_ddr4_cke             (c0_ddr4_cke),
     .c0_ddr4_odt             (c0_ddr4_odt),
     .c0_ddr4_cs_n            (c0_ddr4_cs_n),
     .c0_ddr4_ck_t            (c0_ddr4_ck_t),
     .c0_ddr4_ck_c            (c0_ddr4_ck_c),
     .c0_ddr4_reset_n         (c0_ddr4_reset_n),
     .c0_ddr4_dm_dbi_n        (c0_ddr4_dm_dbi_n),
     .c0_ddr4_dq              (c0_ddr4_dq),
     .c0_ddr4_dqs_c           (c0_ddr4_dqs_c),
     .c0_ddr4_dqs_t           (c0_ddr4_dqs_t),

     .dBufAdr                 (dBufAdr),
     .wrData                  (wrData),
     .wrDataMask              (wrDataMask),
     .rdData                  (rdData),
     .rdDataAddr              (rdDataAddr),
     .rdDataEn                (rdDataEn),
     .rdDataEnd               (rdDataEnd),
     .per_rd_done             (per_rd_done),
     .rmw_rd_done             (rmw_rd_done),
     .wrDataAddr              (wrDataAddr),
     .wrDataEn                (wrDataEn),

     .mc_ACT_n                (mc_ACT_n),
     .mc_ADR                  (mc_ADR),
     .mc_BA                   (mc_BA),
     .mc_BG                   (mc_BG),
     .mc_CKE                  (mc_CKE),
     .mc_CS_n                 (mc_CS_n),
     .mc_ODT                  (mc_ODT),
     .mcCasSlot               (mcCasSlot),
     .mcCasSlot2              (mcCasSlot2),
     .mcRdCAS                 (mcRdCAS),
     .mcWrCAS                 (mcWrCAS),
     .winInjTxn               (winInjTxn),
     .winRmw                  (winRmw),
     .gt_data_ready           (gt_data_ready),
     .winBuf                  (winBuf),
     .winRank                 (winRank),
     .tCWL                    (tCWL),
     .sl_iport0               (37'b0),
     .sl_oport0               (),
     .dbg_bus                 (dbg_bus) 

     );

endmodule
