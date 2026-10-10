# Milestone M1: Kernel Entry, Serial Console, GDT, and IDT

**Owner:** DAXX (Worker Lead)
**Status:** PENDING

## Objectives
1. **Limine Boot Protocol Integration:** Write a minimal `kernel.c` and linker script (`linker.ld`) that implements the Limine boot protocol requests (64-bit entry).
2. **Serial Console:** Implement an early serial console using COM1 (I/O port `0x3F8`). Write a basic `print_serial(const char* str)` function.
3. **Kernel Entry Verification:** Have the kernel print `"[XORAS::OS] Kernel successfully booted via Limine."` to the serial port immediately upon entry.
4. **GDT & IDT:** Set up a bare-bones 64-bit Global Descriptor Table (GDT) and Interrupt Descriptor Table (IDT).
5. **Exception Handlers:** Implement basic ISR (Interrupt Service Routine) stubs that catch CPU exceptions (e.g., Page Fault, General Protection Fault). Have them print an error to the serial port and halt.
6. **Build & Boot:** 
   - Compile `kernel.elf` using the `x86_64-elf-gcc` toolchain installed in M0.
   - Update `limine.cfg` to point to `boot/kernel.elf`.
   - Build a new `freedoom.iso` using `xorriso`.
   - Run QEMU with `-serial file:serial.log` (or `-serial stdio` and redirect) to capture the output.

## Exit Evidence
- Source files (`kernel.c`, `limine_requests.c`/`.h`, `linker.ld`, `gdt.c`, `idt.c`) committed to the workspace.
- `serial.log` containing the exact `"[XORAS::OS] Kernel successfully booted via Limine."` string.
- SHA-256 of the new `freedoom.iso` and `serial.log` logged.
- Receipt written to `memory/catch_log/gauntlet_audit.log` and the DAG updated.

## Instructions for DAXX
If the compilation fails or QEMU panics, self-heal. Read the Limine protocol documentation if necessary. Ensure the serial output is flushed so QEMU writes it to the log file. Hand off to Orchestrator when done.
