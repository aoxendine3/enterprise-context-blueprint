# Milestone M0: Toolchain and Baseline Boot

**Owner:** DAXX (Worker Lead)
**Status:** PENDING

## Objectives
1. Verify system disk space (ensure at least 1.5 GiB free before proceeding). Log `df -h /`.
2. Install the cross-compilation toolchain and emulation environment on macOS (Apple Silicon):
   `brew install x86_64-elf-gcc x86_64-elf-binutils qemu nasm xorriso`
3. Clear Homebrew cache after installation to save disk space: `brew cleanup`.
4. Create an empty Limine bootable ISO image.
5. Boot the empty image using `qemu-system-x86_64` (TCG mode, no HVF) and verify it reaches the Limine bootloader screen.
6. Take a screenshot or serial log of the boot.

## Exit Evidence
- Toolchain installed (log versions).
- Disk space verified.
- `screendump -f png` from QEMU or a serial log showing Limine booting.
- Artifacts and command logged with their SHA-256 hash in the receipt.
- A receipt saved to `memory/catch_log/gauntlet_audit.log` and the DAG updated.

## Instructions for DAXX
Follow the steps, implement self-healing if a command fails, and record all evidence according to the Invariants in `AGENTS.md`. Hand off to Vance/NoBoo for validation once done.
