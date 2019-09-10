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
//  /   /         Filename           : example_tb_phy.sv
// /___/   /\     Date Last Modified : $Date: 2014/09/03 $
// \   \  /  \    Date Created       : Thu Apr 18 2013
//  \___\/\___\
//
// Device           : UltraScale
// Design Name      : DDR4 SDRAM PHY EXAMPLE TB
// Purpose          : This is an  example test-bench that shows how to interface
//                    to the PHY. This example works for DDR4 PHY generated from 
//                    MIG. 
//                    This module waits for the calibration complete 
//                    (init_calib_complete) to pass the traffic to the PHY.
//
//                    This TB generates 10 write transactions
//                    followed by 10 read transactions to the PHY.
//                    Checks if the data that is read back from the 
//                    memory is correct. After 10 writes and reads, no other
//                    commands will be issued by this TG.
//
//                    All READ and WRITE transactions in this example TB are of 
//                    DDR4 BURST LENGTH (BL) 8. In a single clock cycle 1 BL8
//                    transaction will be generated.
//
//                    The fabric to DRAM clock ratio is 4:1. In each fabric 
//                    clock cycle 8 beats of data will be written during 
//                    WRITE transactions and 8 beats of data will be received 
//                    during READ transactions.
//
//                    In this example TB: All the commands are issued for 
//                    one slot only.
//
// Reference        :
// Revision History :
//*****************************************************************************

`timescale 1ps / 1ps

module example_tb_phy #
  (
  parameter SIMULATION       = "FALSE",   // This parameter must be
                                          // TRUE for simulations and 
                                          // FALSE for implementation.
                                          //
   parameter integer ADDR_WIDTH           = 17, // Address bus width
   parameter integer BANK_WIDTH           = 2,  // Bank width
   parameter integer BANK_GROUP_WIDTH     = 1,  // Bank group width
   parameter integer CS_WIDTH             = 1,  // Chip select width
   parameter integer ODT_WIDTH            = 1,  // ODT width
   parameter integer DQ_WIDTH             = 32, // Data bus width
   parameter integer DM_WIDTH             = 4,  // Data Mask width
   parameter integer CWL                  = 10,  // CAS Write Latency
   parameter integer NUM_RANK             = 1,
   parameter integer NUM_SLOT             = 1,
   parameter integer DATA_BUF_ADDR_WIDTH  = 5,  // Data buffer address width

   parameter ODTWR                        = 16'h8421,
   parameter ODTWRDEL                     = 5'd9
            ,ODTWRDUR                     = 4'd6
            ,ODTWRODEL                    = 5'd9
            ,ODTWRODUR                    = 4'd6

            ,ODTRD                        = 16'h0000
            ,ODTRDDEL                     = 5'd9
            ,ODTRDDUR                     = 4'd6
            ,ODTRDODEL                    = 5'd9
            ,ODTRDODUR                    = 4'd6

            ,ODTBITS                      = 4
            ,ODTNOP                       = 4'b0000
   )
  (
   input clk,                 // fabric clock.
                              //
   input rst,                 // reset signal.
                              //
   input init_calib_complete, // calibration done signal coming from PHY.
                              //
   output     [DATA_BUF_ADDR_WIDTH-1:0]  dBufAdr,   // Reserved. Should be tied low.
                                                    //
   output reg          [DQ_WIDTH*8-1:0]  wrData,    // DRAM write data.
                                                    // There are 8 bits for each DQ lane on the DRAM bus.
                                                    //
   output reg          [DM_WIDTH*8-1:0]  wrDataMask,// DRAM write DM/DBI port.  
                                                    // There is one bit for each byte of the wrData port.
                                                    //
   input                                 wrDataEn,  // Write data Enable. 
                                                    // The Phy will assert this port for one cycle for each write CAS command.
                                                    //
   output reg                     [7:0]  mc_ACT_n,  // DRAM ACT_n command signal for four DRAM clock cycles.
                                                    //
   output reg        [ADDR_WIDTH*8-1:0]  mc_ADR,    // DRAM address.
                                                    // There are 8 bits in the fabric interface for each address bit on the DRAM bus.
                                                    //
   output reg        [BANK_WIDTH*8-1:0]  mc_BA,     // DRAM bank address. 
                                                    // 8 bits for each DRAM bank address.
                                                    //
   output reg  [BANK_GROUP_WIDTH*8-1:0]  mc_BG,     // DRAM bank group address.
                                                    // 8 bits for each DRAM pin.
                                                    //
   output reg          [CS_WIDTH*8-1:0]  mc_CS_n,   // DRAM CS_n
                                                    // 8 bits for each DRAM pin
                                                    //
   output wire         [ODT_WIDTH*8-1:0]  mc_ODT,    // DRAM ODT
                                                    // 8 bits for each DRAM pin.
                                                    //
   output reg                            mcRdCAS,   // Read CAS command issued.
                                                    //
   output reg                            mcWrCAS,   // Write CAS command issued.
                                                    // 
   output reg                     [1:0]  winRank,   // Target rank for CAS commands. 
                                                    // This value indicates which rank a CAS command is issued to. 
                                                    //
   output reg                     [4:0]  winBuf,    // Optional control signal.  
                                                    // When either mcRdCAS or mcWrCAS is asserted, 
                                                    // the Phy will store the value on the winBuf signal.  
                                                    //
   input            [DQ_WIDTH*8-1:0]     rdData,    // DRAM read data. 
                                                    // There are 8 bits for each DQ lane on the DRAM bus.
                                                    //
   input                                 rdDataEn,  // Read data valid. 
                                                    // This signal asserts for one fabric cycle for each completed read operation.
                                                    //
   input                                 rdDataEnd, // Unused.  Tied high.
                                                    //
   output                                compare_error, // Memory READ_DATA and example TB
                                                       // WRITE_DATA compare error.
                                                  
   output                                wr_rd_complete                                              


  );

//*****************************************************************************
// Fixed constant parameters. 
// DO NOT CHANGE these values. 
// As they are meant to be fixed to those values by design.
//*****************************************************************************
localparam BEGIN_ADDRESS  = 20'h01000; // This is the starting address from
                                     // which the transaction are addressed to
         localparam NUM_TRANSACT  = 64; // Total number of transactions
localparam NUM_WRITES = (NUM_TRANSACT/2) ;// Total Number of WRITE transactions
localparam NUM_READS  = (NUM_TRANSACT/2) ;// Total Number of READ transactions
localparam TCQ = 100; // To model the clock to out delay

localparam INT_DATA_WIDTH  = 16 ;// Internal data width for write and read data.  
                              // set to 16 bit. Data generation is always 2 bytes
                        // For higher data widths the 16-bit data is duplicated.

//************************
// Instruction encoding
//************************
// encoding for the different states in the WRITE/READ Transaction generation 
// state machine
localparam IDLE       = 4'b0000;
localparam ACTIVATE   = 4'b0001;
localparam ACT_WAIT   = 4'b0010;
localparam WRITE      = 4'b0011;
localparam WRITE_WAIT = 4'b0100;
localparam WR_RD_WAIT = 4'b0101;
localparam READ       = 4'b0110;
localparam READ_WAIT  = 4'b0111;
localparam DONE       = 4'b1000;

// Internal signals
reg              [19:0]         addr_gen;          // Internal address signal
reg  [ADDR_WIDTH*8-1:0]         cmd_addr;          // Command address
reg [9 :0]                      cmd_cnt ;          // Command count
reg [9 :0]                      wr_to_rd_dly_cnt ; // Write to read command delay count
reg                             cmd_en;            // Command enable
reg                             compare_error_int; // Compare error
reg                             compare_error_r1;  // Registered version of 
                                                   // compare_error
wire [DQ_WIDTH*8-1:0]           exp_rd_data;       // Expected read data
reg                     [31:0]  exp_rd_data_int;   // Internal Expected read data
reg                             init_calib_complete_r; // Registered version of 
                                                       // init_calib_complete
reg [DQ_WIDTH*8-1 : 0]          rdData_r1;         // Registered version of read data
reg                             rdDataEn_r1;       // Registered version of read data enable
reg [(DQ_WIDTH*8/8)-1:0]        error_byte;        // Data error per byte
reg                      [3:0]  state;             // Internal state signal
reg                     [11:0]  act_wait_cnt;      // Activate command wait counter signal
reg                     [31:0]  wdf_data;          // write data signal
reg                             wrDataEn_r;        // Registered version of wrDataEn

//*****************************************************************************
//Init calib complete has to be asserted before any command can be driven out.
//Registering init_calib_complete to meet timing
//*****************************************************************************
always @ (posedge clk)
  init_calib_complete_r <= #TCQ init_calib_complete;

//*****************************************************************************
//Registering wrDataEn to provide wrData at the Phy input ports 
//on the cycle after wrDataEn asserts.
//*****************************************************************************
always @ (posedge clk)
  wrDataEn_r <= #TCQ wrDataEn;

//*****************************************************************************
// Command Address generation to the PHY
//*****************************************************************************
// The cmd_addr signal is the command address issued to the PHY.
// In this example TB, LSB is the COLUMN ADDRESS bits.
// The LSB 3-bits will be reserved for BL8 COLUMN address increments.
// The cmd_addr is initialised to BEGIN_ADDRESS and 
// incremented by 8(`h8) when state is WRITE or READ
// to increment the COLUMN address.
// The cmd_addr is initialized with BEGIN_ADDRESS when write commands
// are completed.
//*****************************************************************************

always @(posedge clk )
begin
  if(rst)
    cmd_en <= #TCQ 1'b0;
  else if (state == WRITE || state == READ)
    cmd_en <= #TCQ 1'b1;
  else
    cmd_en <= #TCQ 1'b0;
end

  always @(posedge clk)
  begin
    if(rst)
      addr_gen <= #TCQ BEGIN_ADDRESS;
     else if (state == WRITE || state == READ)
      // The cmd_cnt value is 10 when it completes 10 write transactions.
      // The cmd_addr is initialized with BEGIN_ADDRESS when write commands
      // are completed (cmd_cnt = 9) to start the read commands.  
      if (cmd_cnt == NUM_WRITES-1)
        addr_gen <= #TCQ BEGIN_ADDRESS;
      else
        addr_gen <= #TCQ addr_gen + 20'h00008;
  end

  genvar i, j;
  generate
    for (i=0; i<ADDR_WIDTH; i = i + 1)
      for (j=0; j<8; j = j + 1)
        assign cmd_addr[(i*8)+j] = addr_gen[i];
  endgenerate

//*****************************************************************************
// Write data generation to the PHY
//*****************************************************************************
// The wrData bus is the write data issued to the PHY.
// For 4:1 clock ratio in BL8 Mode, the data has to be provided for the entire
// BL8 burst in one clock cycle (PHY interface clock cycle).
//
// The data has to be provided in the following format:
// FALL3->RISE3->FALL2->RISE2->FALL1->RISE1->FALL0->RISE0
// 
// For a 16 bit interface, 16 * 8 = 128 bits of data will be provided in the
// each clock cycle. LSB 16-bits corresponds to RISE0 and MSB 16-bits 
// corresponds to FALL3.
//
// The wrData is initialised to zero and
// increments by 8(`h8) when wrDataEn_r is '1' to generate the write data.
// 
//*****************************************************************************
//Data duplication
assign wrData   = {((DQ_WIDTH*8)/INT_DATA_WIDTH){wdf_data}};

  always @(posedge clk)
  begin
    if(rst)
      wdf_data <= #TCQ 32'h00000000;
    else if (wrDataEn_r)
      if (wdf_data < ((NUM_WRITES-1)*8))
        wdf_data <= #TCQ wdf_data + 8'b00001000;
      else if (cmd_cnt == (NUM_WRITES-1))
        wdf_data <= #TCQ 32'h00000000;
  end

//*****************************************************************************
//  WRITE/READ Transaction generation state machine:
//
//  This state machine generates the PHY interface signals for 
//  10 writes followed by 10 reads transactions.
//
//  This state machine logic controls the read-write operations after 
//  calibration is done.
//  
//  The state machine stay in IDLE state until calibration is complete.
//
//  The state machine enter into ACTIVATE state after IDLE state when
//  calibration is completed. (init_calib_complete_r signal is '1')
//
//  The state machine enter into ACT_WAIT state in the next clock cycle 
//  after ACTIVATE state.
//
//  The state machine enter into WRITE state after ACT_WAIT state
//  when act_wait_cnt counter reaches the value of 10 to make sure that 
//  ACTIVATE command is processed.
//
//  The state machine enter into WRITE_WAIT state in the next clock cycle 
//  after WRITE state to provide extra one clock cycle delay to meet 
//  tCCD_L timing parameter until all WRITE commands are completed.
//
//  The state machine enter into WRITE state in the next clock cycle 
//  after WRITE_WAIT state.
//  
//  The state machine enter into WR_RD_WAIT state after WRITE state
//  when all the WRITE commands are completed.
//
//  The state machine stays in WR_RD_WAIT state until wr_to_rd_dly_cnt
//  reaches 10 to delay between WRITE and READ commands.
//
//  The state machine enter into READ state after WR_RD_WAIT state
//  when wr_to_rd_dly_cnt counter reaches the value of 10.
//
//  The state machine enter into READ_WAIT state in the next clock cycle 
//  after READ state to provide extra one clock cycle delay to meet 
//  tCCD_L timing parameter until all READ commands are completed.
//
//  The state machine enter into DONE state after READ state
//  when all the READ commands are completed.
//
//  The state machine stays in DONE state.
//
//*****************************************************************************
reg mcRdCAS_temp;
reg mcWRCAS_temp;
wire [ODT_WIDTH*8-1:0] mc_ODT_temp;
reg  [1:0] winRank_temp;
wire tranSentC;
assign mcRdCAS = mcRdCAS_temp;
assign mcWrCAS = mcWRCAS_temp;
assign mc_ODT  = mc_ODT_temp;
assign winRank = winRank_temp;
assign tranSentC = mcRdCAS_temp | mcWRCAS_temp;
always @(posedge clk)
begin
  if(rst) begin
    mc_ACT_n  <= #TCQ 8'hFF;
    mc_ADR    <= #TCQ {ADDR_WIDTH*8{1'b1}};
    mc_BA     <= #TCQ {BANK_WIDTH*8{1'b1}};
    mc_BG     <= #TCQ {BANK_GROUP_WIDTH*8{1'b1}};
    mc_CS_n   <= #TCQ {CS_WIDTH*8{1'b1}};
  //  mc_ODT  <= #TCQ {ODT_WIDTH*8{1'b0}};
    wrDataMask      <= #TCQ 'b0;
    mcRdCAS_temp   <= #TCQ 1'b0;
    mcWRCAS_temp   <= #TCQ 1'b0;
    state     <= #TCQ IDLE;
  end else begin
    casez (state)
      
      // ----------------------------------------------------------------
      IDLE: begin
      // ----------------------------------------------------------------
        if (init_calib_complete_r) begin
          state <= #TCQ ACTIVATE;
        end
      end

      // ----------------------------------------------------------------
      ACTIVATE: begin
      // ----------------------------------------------------------------
        mc_ACT_n        <= #TCQ 8'hFC;
        mc_CS_n[7:0]    <= #TCQ 8'hFC;
        mc_BA           <= #TCQ {BANK_WIDTH{8'hFC}};
        mc_BG           <= #TCQ {BANK_GROUP_WIDTH{8'hFC}};
        mc_ADR[135:128] <= #TCQ 8'hFC;
        mc_ADR[127:120] <= #TCQ 8'hFF;
        mc_ADR[119:112] <= #TCQ 8'hFF;
        mc_ADR[111:0]   <= #TCQ {ADDR_WIDTH*8{1'b0}};
        state           <= #TCQ ACT_WAIT;
      end

      // ----------------------------------------------------------------
      ACT_WAIT: begin
      // ----------------------------------------------------------------
        if(act_wait_cnt == 10)
          state      <= #TCQ WRITE;
        else
          state      <= #TCQ ACT_WAIT;

        mc_ACT_n     <= #TCQ 8'hFF;
        mc_CS_n      <= #TCQ {CS_WIDTH*8{1'b1}};
        mc_BA        <= #TCQ {BANK_WIDTH*8{1'b1}};
        mc_BG        <= #TCQ {BANK_GROUP_WIDTH*8{1'b1}};
        mc_ADR       <= #TCQ {ADDR_WIDTH*8{1'b1}};
      end

      // ----------------------------------------------------------------
      WRITE: begin
      // ----------------------------------------------------------------
        state           <= #TCQ WRITE_WAIT;
        mc_CS_n[7:0]    <= #TCQ 8'hFC;
        mc_BA           <= #TCQ {BANK_WIDTH{8'hFC}};
        mc_BG           <= #TCQ {BANK_GROUP_WIDTH{8'hFC}};
        mcWRCAS_temp    <= #TCQ 1'b1;
        mc_ADR[135:128] <= #TCQ 8'hFF;
        mc_ADR[127:120] <= #TCQ 8'hFC;
        mc_ADR[119:112] <= #TCQ 8'hFC;
        mc_ADR[111:0]   <= #TCQ cmd_addr;
        wrDataMask      <= #TCQ 'b0;
     //   mc_ODT        <= #TCQ {ODT_WIDTH*8{1'b1}};
      end

      // ----------------------------------------------------------------
      WRITE_WAIT: begin
      // ----------------------------------------------------------------
        if (cmd_cnt < NUM_WRITES)
          state      <= #TCQ WRITE;
        else 
          state      <= #TCQ WR_RD_WAIT;
        mc_ACT_n       <= #TCQ 8'hFF;
        mc_CS_n        <= #TCQ {CS_WIDTH*8{1'b1}};
        mc_BA          <= #TCQ {BANK_WIDTH*8{1'b1}};
        mc_BG          <= #TCQ {BANK_GROUP_WIDTH*8{1'b1}};
        mc_ADR         <= #TCQ {ADDR_WIDTH*8{1'b1}};
        mcWRCAS_temp   <= #TCQ 1'b0;
     //   mc_ODT         <= #TCQ { ODT_WIDTH {{4 {1'b0}} ,{4 {1'b1}} } } ;
      end

      // ----------------------------------------------------------------
      WR_RD_WAIT: begin
      // ----------------------------------------------------------------
        if (wr_to_rd_dly_cnt == 60)
          state      <= #TCQ READ;
        else
          state      <= #TCQ WR_RD_WAIT;

        mc_ACT_n       <= #TCQ 8'hFF;
        mc_CS_n        <= #TCQ {CS_WIDTH*8{1'b1}};
        mc_BA          <= #TCQ {BANK_WIDTH*8{1'b1}};
        mc_BG          <= #TCQ {BANK_GROUP_WIDTH*8{1'b1}};
        mc_ADR         <= #TCQ {ADDR_WIDTH*8{1'b1}};
        mcWRCAS_temp   <= #TCQ 1'b0;
     //   mc_ODT         <= #TCQ {ODT_WIDTH*8{1'b0}};
      end

      // ----------------------------------------------------------------
      READ: begin
      // ----------------------------------------------------------------
        if (cmd_cnt < (NUM_TRANSACT-1))
          state      <= #TCQ READ_WAIT;
        else 
          state      <= #TCQ DONE;

        mc_CS_n[7:0]    <= #TCQ 8'hFC;
        mc_BA           <= #TCQ {BANK_WIDTH{8'hFC}};
        mc_BG           <= #TCQ {BANK_GROUP_WIDTH{8'hFC}};
        mcRdCAS_temp    <= #TCQ 1'b1;
        mc_ADR[135:128] <= #TCQ 8'hFF;
        mc_ADR[127:120] <= #TCQ 8'hFC;
        mc_ADR[119:112] <= #TCQ 8'hFF;
        mc_ADR[111:0]   <= #TCQ cmd_addr;
        //mc_ODT          <= #TCQ { {((ODT_WIDTH-1)*8) {1'b1}}, {8 {1'b0}} } ;
      end

      // ----------------------------------------------------------------
      READ_WAIT: begin
      // ----------------------------------------------------------------
        state          <= #TCQ READ;
        mc_ACT_n       <= #TCQ 8'hFF;
        mc_CS_n        <= #TCQ {CS_WIDTH*8{1'b1}};
        mc_BA          <= #TCQ {BANK_WIDTH*8{1'b1}};
        mc_BG          <= #TCQ {BANK_GROUP_WIDTH*8{1'b1}};
        mc_ADR         <= #TCQ {ADDR_WIDTH*8{1'b1}};
        mcRdCAS_temp   <= #TCQ 1'b0;
        //mc_ODT         <= #TCQ { {(ODT_WIDTH-1) {{4 {1'b0}} ,{4 {1'b1}} } } ,{8 {1'b0}} } ;
      end

      // ----------------------------------------------------------------
      DONE: begin
      // ----------------------------------------------------------------
        state      <= #TCQ DONE;

        mc_ACT_n       <= #TCQ 8'hFF;
        mc_CS_n        <= #TCQ {CS_WIDTH*8{1'b1}};
        mc_BA          <= #TCQ {BANK_WIDTH*8{1'b1}};
        mc_BG          <= #TCQ {BANK_GROUP_WIDTH*8{1'b1}};
        mc_ADR         <= #TCQ {ADDR_WIDTH*8{1'b1}};
        mcRdCAS_temp   <= #TCQ 1'b0;
        //mc_ODT         <= #TCQ {ODT_WIDTH*8{1'b0}};
      end

    endcase
  end
end

//****************************************************************************
// Write to read command transition delay Counter :
//*****************************************************************************
always @(posedge clk )
begin
  if(rst) begin
    wr_to_rd_dly_cnt  <= #TCQ 'b0;
  end else if (state == WR_RD_WAIT) begin
    wr_to_rd_dly_cnt  <= #TCQ wr_to_rd_dly_cnt + 1'b1;
  end else begin
    wr_to_rd_dly_cnt  <= #TCQ 'b0;
  end
end

//****************************************************************************
//  Activate command wait Counter :
//*****************************************************************************
always @(posedge clk )
begin
  if(rst)
    act_wait_cnt <= #TCQ 'b0;
  else if (state == ACT_WAIT)
    act_wait_cnt <= #TCQ act_wait_cnt + 1'b1;
  else
    act_wait_cnt <= #TCQ 'b0;
end

//*****************************************************************************
//  Command Counter :
//      This command counter counts the number of commands issued to the 
//      PHY. 
//*****************************************************************************
always @(posedge clk )
begin
  if(rst)
    cmd_cnt <= #TCQ 'b0;
   else if (state == WRITE || state == READ)
    cmd_cnt <= #TCQ cmd_cnt + 1'b1;
end

//*****************************************************************************
//  winRank and winBuf signal generation:
//*****************************************************************************
always @(posedge clk )
begin
  if(rst) begin
    winRank_temp <= #TCQ 2'b00;
    winBuf  <= #TCQ 'b0;
  end else if (state == WRITE || state == READ) begin
    winRank_temp <= #TCQ 2'b00;
    winBuf  <= #TCQ winBuf + 1;
  end else begin
    winRank_temp <= #TCQ 2'b00;
    winBuf  <= #TCQ winBuf;
  end
end

//*****************************************************************************
// The dBufAdr signal tied to 0 in this example.
//*****************************************************************************
assign dBufAdr   = 5'b0 ;

//*****************************************************************************
// Expected Read data generation:
// 
// The expected read data (exp_rd_data_int) is initialised to zero and
// increments by 8(`h8) when rdDataEn is '1' to generate the read data. 
//
// The read data from the PHY interface is valid when ever the
// rdDataEn signal is asserted to '1'.
//*****************************************************************************
assign exp_rd_data = {((DQ_WIDTH*8)/INT_DATA_WIDTH){exp_rd_data_int}};

  always @(posedge clk )
  begin
    if(rst) begin
      exp_rd_data_int <= #TCQ 32'h00000000;
    end else if (rdDataEn_r1) begin
      if (exp_rd_data_int < (NUM_READS-1)*8) begin
        exp_rd_data_int <= #TCQ exp_rd_data_int + 8'b00001000;
      end
    end
  end

//*****************************************************************************
// Registering data read from the PHY interface and data valid to meet timing
//*****************************************************************************
always @(posedge clk )
begin
  rdData_r1   <= #TCQ rdData;
  rdDataEn_r1 <= #TCQ rdDataEn;
end

//*****************************************************************************
// Read data comparison:
// The compare error (compare_error_int) signal is asserted when the 
// expected read data (exp_rd_data) is not matching with the data 
// read from the PHY interface.
//*****************************************************************************
assign compare_error  = compare_error_r1;

for (i = 0; i < ((DQ_WIDTH*8)/8); i = i + 1)
begin: gen_cmp_4
  always @ (posedge clk)
    if (rdDataEn_r1)
      //synthesis translate_off
      if (SIMULATION=="TRUE")
        error_byte[i]  <= #TCQ (rdData_r1[8*(i+1)-1:8*i] !== exp_rd_data[8*(i+1)-1:8*i]) ;
      else
      //synthesis translate_on
        error_byte[i]  <= #TCQ (rdData_r1[8*(i+1)-1:8*i] != exp_rd_data[8*(i+1)-1:8*i]) ;
    else
      error_byte[i]  <= #TCQ 1'b0;

end

// Compare error is OR of all byte errors
always @(posedge clk )
begin
  if(rst)
    compare_error_int <= #TCQ 1'b0;
  else
    compare_error_int <= #TCQ | error_byte ;

  //synthesis translate_off
  if (compare_error_int)
    $display ("ERROR: Expected data=%h, Received data=%h @ %t" ,exp_rd_data,
               rdData_r1, $time);
  //synthesis translate_on
end

//*****************************************************************************
// Registering compare_error_int to meet the timing.
//*****************************************************************************
always @(posedge clk )
begin
  if(rst)
    compare_error_r1 <= #TCQ 1'b0;
  else
    if (compare_error_int)
      compare_error_r1 <= #TCQ 1'b1;
end

//*******************************************************************************
//*******************************************************************************
//  Read Counter :
//      This Read counter counts the number of rdDataEn issued by the 
//      PHY Interface and generates a pulse (wr_rd_complete) when the number of
//      consequent rdDataEn becomes equal to the 10 .
//      This wr_rd_complete is used only for simulation to finish.
//*******************************************************************************
reg              wr_rd_complete_r;
reg  [6:0] rd_cnt ;
always @(posedge clk)
begin
  if(rst) begin
    rd_cnt         <= #TCQ 'b0;
    wr_rd_complete_r <= #TCQ 'b0;
  end else if(rdDataEn) begin
    rd_cnt <= #TCQ rd_cnt + 1'b1 ;
    if (rd_cnt == (NUM_READS-1)) begin
       wr_rd_complete_r <= #TCQ 1'b1 ;
    end
  end
end

assign wr_rd_complete = wr_rd_complete_r;



// SIMULATION ONLY
//synthesis translate_off
initial
begin : Logging
  fork
    begin : write_read_done
      wait (wr_rd_complete);
      $display("10 Writes and 10 Reads to the memory completed");
      #1000;
      if (!compare_error) begin
        $display("Test Completed Successfully");
        $display("TEST PASSED");
      end
      else begin
        $display("TEST FAILED: DATA ERROR");
      end
      disable write_read_not_done;
      $finish;
    end

    begin : write_read_not_done
      wait (init_calib_complete);
      #50us;
      if (!wr_rd_complete) begin
         $display("ERROR: Timeout occured during Write/Read transaction");
      end
      disable write_read_done;
      $finish;
    end
  join
end
//synthesis translate_on
//*******************************************************************************
ddr4_v2_2_5_ddr_cal_mc_odt # (
    .ODTWR     (ODTWR)
   ,.ODTWRDEL  (ODTWRDEL)
   ,.ODTWRDUR  (ODTWRDUR)
   ,.ODTWRODEL (ODTWRODEL)
   ,.ODTWRODUR (ODTWRODUR)

   ,.ODTRD     (ODTRD)
   ,.ODTRDDEL  (ODTRDDEL)
   ,.ODTRDDUR  (ODTRDDUR)
   ,.ODTRDODEL (ODTRDODEL)
   ,.ODTRDODUR (ODTRDODUR)

   ,.ODTNOP    (ODTNOP)
   ,.ODTBITS   (ODTBITS)
   ,.TCQ       (0.1)
)u_ddr_tb_odt(
    .clk       (clk)
   ,.rst       (rst)
   ,.mc_ODT    (mc_ODT_temp)
   ,.casSlot2  ({1{1'b0}})
   ,.rank      (winRank_temp)
   ,.winRead   (mcRdCAS_temp)
   ,.winWrite  (mcWRCAS_temp)
   ,.tranSentC (tranSentC)
);


endmodule


