# RISC240-ML

This project extends the CMU RISC240 processor by adding a small vector instruction set for machine learning style operations. I added a vector register file, vector ALU, dot-product unit, and accumulator while keeping the original scalar processor working.

To make writing programs easier, I also made a Python assembler and instruction-level simulator based on the ideas behind the `as240` assembler and `sim240` simulator from CMU's 18-240 course. I used ChatGPT to help write parts of the Python code while checking everything against the ISA and test programs as I went. I also put together an automated verification flow using Synopsys VCS so I could quickly test new instructions before running them on the FPGA.

## Main changes

### Datapath

Most of the hardware work was done in `datapath.sv`. This is where I integrated the new vector hardware:

- Vector register file
- Vector ALU
- Dot-product unit
- Accumulator
- New datapaths needed for vector instructions

### Control logic

`controlpath.sv` was updated with the extra states and control signals needed for the new instructions, including vector arithmetic, vector loads/stores, and dot-product execution.

### New hardware modules

I added several new modules:

- `ML_alu.sv` - vector addition, multiplication, ReLU, and pass-through operations
- `vector_regfile.sv` - 8-entry, 64-bit vector register file
- `dot_product_unit.sv` - parallel dot-product hardware
- `accumulator.sv` - accumulator used by the dot-product instruction

### Assembler and simulator

I wrote a Python assembler (`MLASM.py`) that supports both the original RISC240 instructions and the new vector instructions. It generates memory files for both simulation and Vivado.

I also wrote a simple instruction-level simulator (`MLSIM.py`) so I could test assembly programs without running RTL every time.

### Verification

The verification flow automatically:

- Assembles the program
- Runs the RTL in Synopsys VCS
- Waits for the processor to halt
- Compares the final processor state against the expected results

Right now there are 18 assembly test programs covering both the original processor and the new vector instructions.

## Tools

- SystemVerilog
- Python
- Synopsys VCS
- Xilinx Vivado

## Repository Structure

```text
rtl/
    controlpath.sv
    datapath.sv
    alu.sv
    ML_alu.sv
    vector_regfile.sv
    dot_product_unit.sv
    accumulator.sv
    memory.sv
    RISC240.sv
    ...

assembler/
    MLASM.py
    MLSIM.py
    tests/

verification/
    risc240_tb.sv
    run_tests.py
    expected_results.json
```