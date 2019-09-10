

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
//  \   \         Application        : MIG
//  /   /         Filename           : example_top.sv
// /___/   /\     Date Last Modified : $Date: 2011/06/17 11:11:25 $
// \   \  /  \    Date Created       : Thu Apr 18 2013
//  \___\/\___\
//
// Device           : UltraScale
// Design Name      : DDR4_SDRAM
// Purpose          :
//                   example_top module
// Reference        :
// Revision History :
//*****************************************************************************
`ifdef MODEL_TECH
    `ifndef CALIB_SIM
       `define SIMULATION
     `endif
`elsif INCA
    `ifndef CALIB_SIM
       `define SIMULATION
     `endif
`elsif VCS
    `ifndef CALIB_SIM
       `define SIMULATION
     `endif
`elsif XILINX_SIMULATOR 
    `ifndef CALIB_SIM
       `define SIMULATION
     `endif
`endif

`timescale 1ps/1ps
module example_top #
  (
    parameter SIMULATION            = "FALSE"
  )
  (

    input                             sys_rst,
    input                             c0_sys_clk_p,
    input                             c0_sys_clk_n,

   // iob<>DDR4 signals
    output                            c0_ddr4_act_n,
    output               [16:0]       c0_ddr4_adr,
    output      [1:0]      c0_ddr4_ba,
    output [0:0]     c0_ddr4_bg,
    output        [0:0]     c0_ddr4_cke,
    output        [0:0]     c0_ddr4_odt,
    output        [0:0]      c0_ddr4_cs_n,
    output        [0:0]      c0_ddr4_ck_t,
    output        [0:0]      c0_ddr4_ck_c,
    output                            c0_ddr4_reset_n,
    inout         [7:0]      c0_ddr4_dm_dbi_n,
    inout          [63:0]     c0_ddr4_dq,
    inout        [7:0]      c0_ddr4_dqs_c,
    inout        [7:0]      c0_ddr4_dqs_t,

    output                            c0_init_calib_complete,
    output                            c0_data_compare_error
);

  wire [4:0]  dBufAdr;
  wire [511:0]  wrData;
  wire [63:0]  wrDataMask;
  wire [511:0]  rdData;
  wire [4:0]  rdDataAddr;
  wire [0:0]                           rdDataEn;
  wire [0:0]                           rdDataEnd;
  wire [0:0]                           per_rd_done;
  wire [0:0]                           rmw_rd_done;
  wire [4:0]  wrDataAddr;
  wire [0:0]                           wrDataEn;
  wire [7:0]                       mc_ACT_n;
  wire [135:0]  mc_ADR;
  wire [15:0]  mc_BA;
  wire [7:0]  mc_BG;
  wire [7:0]  mc_CKE;
  wire [7:0]  mc_CS_n;
  wire [7:0]  mc_ODT;
  wire [0:0]                            mcRdCAS;
  wire [0:0]                            mcWrCAS;
  wire [0:0]                            winInjTxn;
  wire [0:0]                            winRmw;
  wire [4:0]                       winBuf;
  wire [1:0]                       winRank;
  wire [5:0]                       tCWL;
  wire                             dbg_clk;
  wire c0_wr_rd_complete;



   // debug ports
  wire [63:0]                      dbg_rd_data_cmp;
  wire [63:0]                      dbg_expected_data;
  wire [2:0]                       dbg_cal_seq;
  wire [31:0]                      dbg_cal_seq_cnt;
  wire [7:0]                       dbg_cal_seq_rd_cnt;
  wire                             dbg_rd_valid;
  wire [5:0]                       dbg_cmp_byte;
  wire [63:0]                      dbg_rd_data;
  wire [15:0]                      dbg_cplx_config;
  wire [1:0]                       dbg_cplx_status;
  wire [27:0]                      dbg_io_address;
  wire                             dbg_pllGate;
  wire [19:0]                      dbg_phy2clb_fixdly_rdy_low;
  wire [19:0]                      dbg_phy2clb_fixdly_rdy_upp;
  wire [19:0]                      dbg_phy2clb_phy_rdy_low;
  wire [19:0]                      dbg_phy2clb_phy_rdy_upp;
  wire [127:0]                     cal_r0_status;
  wire [8:0]                       cal_post_status;
  wire                             c0_ddr4_clk;
  wire                             c0_ddr4_rst;
  // Debug Bus
  wire [511:0]                         dbg_bus;        

// debug port wire declarations
`ifdef SIMULATION
`else
 (*mark_debug  = "TRUE" *) wire dbg_init_calib_complete;
 (*mark_debug  = "TRUE" *) wire dbg_data_compare_error;
`endif
// end of  debug port wire declarations

wire c0_ddr4_reset_n_int;
  assign c0_ddr4_reset_n = c0_ddr4_reset_n_int;


ddr4_0 u_ddr4_0
    (
     .sys_rst              (sys_rst),
     .c0_sys_clk_p         (c0_sys_clk_p),
     .c0_sys_clk_n         (c0_sys_clk_n),

     .c0_ddr4_ui_clk       (c0_ddr4_clk),
     .c0_ddr4_ui_clk_sync_rst (c0_ddr4_rst),
     .c0_init_calib_complete (c0_init_calib_complete),
     .dbg_clk              (dbg_clk),
     .dbg_rd_data_cmp                            (dbg_rd_data_cmp),
     .dbg_expected_data                          (dbg_expected_data),
     .dbg_cal_seq                                (dbg_cal_seq               ),
     .dbg_cal_seq_cnt                            (dbg_cal_seq_cnt           ),
     .dbg_cal_seq_rd_cnt                         (dbg_cal_seq_rd_cnt        ),
     .dbg_rd_valid                               (dbg_rd_valid              ),
     .dbg_cmp_byte                               (dbg_cmp_byte              ),
     .dbg_rd_data                                (dbg_rd_data               ),
     .dbg_cplx_config                            (dbg_cplx_config           ),
     .dbg_cplx_status                            (dbg_cplx_status           ),
     .dbg_io_address                             (dbg_io_address            ),
     .dbg_pllGate                                (dbg_pllGate               ),
     .dbg_phy2clb_fixdly_rdy_low                 (dbg_phy2clb_fixdly_rdy_low),
     .dbg_phy2clb_fixdly_rdy_upp                 (dbg_phy2clb_fixdly_rdy_upp),
     .dbg_phy2clb_phy_rdy_low                    (dbg_phy2clb_phy_rdy_low   ),
     .dbg_phy2clb_phy_rdy_upp                    (dbg_phy2clb_phy_rdy_upp   ),
     .win_status                                 (),
     .cal_r0_status                              (cal_r0_status),
     .cal_post_status                            (cal_post_status),
     .c0_ddr4_act_n        (c0_ddr4_act_n),
     .c0_ddr4_adr          (c0_ddr4_adr),
     .c0_ddr4_ba           (c0_ddr4_ba),
     .c0_ddr4_bg           (c0_ddr4_bg),
     .c0_ddr4_cke          (c0_ddr4_cke),
     .c0_ddr4_odt          (c0_ddr4_odt),
     .c0_ddr4_cs_n         (c0_ddr4_cs_n),
     .c0_ddr4_ck_t         (c0_ddr4_ck_t),
     .c0_ddr4_ck_c         (c0_ddr4_ck_c),
     .c0_ddr4_reset_n      (c0_ddr4_reset_n_int),
     .c0_ddr4_dm_dbi_n     (c0_ddr4_dm_dbi_n),
     .c0_ddr4_dq           (c0_ddr4_dq),
     .c0_ddr4_dqs_c        (c0_ddr4_dqs_c),
     .c0_ddr4_dqs_t        (c0_ddr4_dqs_t),

     .dBufAdr              (dBufAdr),
     .wrData               (wrData),
     .wrDataMask           (wrDataMask),

     .rdData               (rdData),
     .rdDataAddr           (rdDataAddr),
     .rdDataEn             (rdDataEn),
     .rdDataEnd            (rdDataEnd),
     .per_rd_done          (per_rd_done),
     .rmw_rd_done          (rmw_rd_done),
     .wrDataAddr           (wrDataAddr),
     .wrDataEn             (wrDataEn),

     .mc_ACT_n             (mc_ACT_n),
     .mc_ADR               (mc_ADR),
     .mc_BA                (mc_BA),
     .mc_BG                (mc_BG),
     // DRAM CKE. 8 bits for each DRAM pin. The mc_CKE signal is always set to '1'.
     .mc_CKE               ({8{1'b1}}),
     .mc_CS_n              (mc_CS_n),
     .mc_ODT               (mc_ODT),
     // CAS command slot select. Slot0 is enabled for example design.
     .mcCasSlot            ({1{2'b00}}),
     // CAS slot 2 select.  mcCasSlot2 serves a similar purpose as the mcCasSlot[1:0] signal, but mcCasSlot2 is used in timing 
     // critical logic in the Phy. Slot0 is enabled for example design.
     .mcCasSlot2           ({1{1'b0}}),
     .mcRdCAS              (mcRdCAS),
     .mcWrCAS              (mcWrCAS),
     // Optional read command type indication. The winInjTxn signal is set to '0' for example design.
     .winInjTxn            ({1{1'b0}}),
     // Optional read command type indication. The winRmw signal is set to '0' for example design.
     .winRmw               ({1{1'b0}}),
     // Update VT Tracking. The gt_data_ready signal is set to '0' in this example design.
     // This signal must be asserted periodically to keep the DQS Gate aligned as voltage and temperature drift.
     // For more information, Refer to PG150 document.
     .gt_data_ready        (1'b0),
     .winBuf               (winBuf),
     .winRank              (winRank),
     .tCWL                 (tCWL),
     // Debug Port
     .dbg_bus         (dbg_bus)                                             
     
     );

   localparam  integer ADDR_WIDTH           = 17;
   localparam  integer BANK_WIDTH           = 2;
   localparam  integer BANK_GROUP_WIDTH     = 1;
   localparam  integer CS_WIDTH             = 1;
   localparam  integer ODT_WIDTH            = 1;
   localparam  integer DQ_WIDTH             = 64;
   localparam  integer DM_WIDTH             = 8;
   localparam  integer NUM_RANK             = 1;
   localparam  integer NUM_SLOT                     = 1;
   localparam  integer DATA_BUF_ADDR_WIDTH  = 5;
    
   localparam          ODTWRDEL                = 5'd12;
   localparam          ODTWRDUR                = 4'd6;
   localparam          ODTWRODEL               = 5'd9;
   localparam          ODTWRODUR               = 4'd6;
   localparam          ODTRDDEL                = 5'd17;
   localparam          ODTRDDUR                = 4'd6;
   localparam          ODTRDODEL               = 5'd9;
   localparam          ODTRDODUR               = 4'd6;
   localparam          ODTNOP                  = 16'h0000;

    localparam        ODTWR                     = 16'h0021;
    localparam        ODTRD                     = 16'h0000;

  example_tb_phy #
    (
     .SIMULATION     (SIMULATION),
     .ADDR_WIDTH     (ADDR_WIDTH),
     .BANK_WIDTH     (BANK_WIDTH),
     .BANK_GROUP_WIDTH     (BANK_GROUP_WIDTH),
     .ODTWR          (ODTWR),
     .ODTRD          (ODTRD),
     .ODTWRDEL       (ODTWRDEL ), 
     .ODTWRDUR       (ODTWRDUR ), 
     .ODTWRODEL      (ODTWRODEL), 
     .ODTWRODUR      (ODTWRODUR), 
     .ODTRDDEL       (ODTRDDEL ), 
     .ODTRDDUR       (ODTRDDUR ), 
     .ODTRDODEL      (ODTRDODEL), 
     .ODTRDODUR      (ODTRDODUR), 
     .ODTNOP         (ODTNOP   ), 
     .ODTBITS        (ODT_WIDTH),
     .CS_WIDTH       (CS_WIDTH),
     .ODT_WIDTH      (ODT_WIDTH),
     .DQ_WIDTH       (DQ_WIDTH),
     .DM_WIDTH       (DM_WIDTH),
     .CWL            (12),
     .DATA_BUF_ADDR_WIDTH   (DATA_BUF_ADDR_WIDTH)
     )
   u_example_tb_phy
      (
       .clk                                     (c0_ddr4_clk),
       .rst                                     (c0_ddr4_rst),
       .init_calib_complete                     (c0_init_calib_complete),
       .dBufAdr                                 (dBufAdr),
       .wrData 	                                (wrData),
       .wrDataMask                              (wrDataMask),
       .wrDataEn                                (wrDataEn),
       .mc_ACT_n 	                              (mc_ACT_n),
       .mc_ADR	                                (mc_ADR),
       .mc_BA	                                  (mc_BA),
       .mc_BG	                                  (mc_BG),
       .mc_CS_n	                                (mc_CS_n),
       .mc_ODT	                                (mc_ODT),
       .mcRdCAS 	                              (mcRdCAS),
       .mcWrCAS 	                              (mcWrCAS),
       .winBuf                                  (winBuf),
       .winRank                                 (winRank),
       .rdData	                                (rdData),
       .rdDataEn                                (rdDataEn),
       .rdDataEnd                               (rdDataEnd),
       .compare_error	                          (c0_data_compare_error),
       .wr_rd_complete                          (c0_wr_rd_complete)
       

       
  );

`ifdef SIMULATION
`else
 // Debug cores instantiation

   assign dbg_init_calib_complete = c0_init_calib_complete;
   assign dbg_data_compare_error  = c0_data_compare_error;


 ila_ddrx u_ila_ddrx (                                  // Refer to Answer Guide 60305 for Detailed Description of the usage of the Below probes                                                                                             
                                                                                                                                                                                                                               
    .clk (c0_ddr4_clk),                                            
    .probe0  (dbg_init_calib_complete),                 // Signifies the status of calibration
    .probe1  (dbg_data_compare_error),                  // Signifies the status of Traffic Error from The TG 
    .probe2  (dbg_expected_data),                       // Displays the expected data during calibration stages that use fabric-based data pattern comparison such as Read per-bit deskew or read DQS centering (complex).
    .probe3  (dbg_rd_data_cmp),                         // Comparison of dbg_rd_data and dbg_expected_data
    .probe4  (dbg_cal_seq),                             // Calibration sequence indicator, when RTL is issuing commands to the DRAM. 
    .probe5  (dbg_cal_seq_cnt),                         // Calibration command sequence count used when RTL is issuing commands to the DRAM.
    .probe6  (dbg_cal_seq_rd_cnt),                      // Calibration read data burst count
    .probe7  (dbg_rd_valid),                            // Read data valid
    .probe8  (dbg_cmp_byte),                            // Calibration byte selection 
    .probe9  (dbg_rd_data),                             // Read data from input FIFOs
    .probe10 (dbg_cplx_config),                         // Complex cal configuration
    .probe11 (dbg_cplx_status),                         // Complex cal status
    .probe12 (dbg_io_address),                          // MicroBlaze I/O address bus 
    .probe13 (dbg_pllGate),                             // PLL lock indicator
    .probe14 (dbg_phy2clb_fixdly_rdy_low),              // Xiphy fixed delay ready signal (lower nibble) 
    .probe15 (dbg_phy2clb_fixdly_rdy_upp),              // Xiphy fixed delay ready signal (upper nibble)
    .probe16 (dbg_phy2clb_phy_rdy_low),                 // Xiphy phy ready signal (lower nibble)
    .probe17 (dbg_phy2clb_phy_rdy_upp),                 // Xiphy phy ready signal (upper nibble)
    .probe18 (cal_r0_status),                            //Signifies the status of each stage of calibration.
    .probe19 (cal_post_status)                        // Signifies the status of calibration.                                                                                                                      
    );
`endif

 //End of Debug cores instantiation


endmodule
