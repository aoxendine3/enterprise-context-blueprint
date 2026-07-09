#!/bin/bash
echo "[FPGA-HLS] Simulating Vitis HLS compilation environment..."
g++ -O3 -Wall -Wno-unknown-pragmas xoras_fpga_core.cpp -o xoras_fpga_sim
echo "[FPGA-HLS] Compilation complete."
echo "------------------------------------------------"
./xoras_fpga_sim
