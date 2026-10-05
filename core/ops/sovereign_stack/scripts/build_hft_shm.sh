#!/bin/bash
# --- XORAS HFT SHM ENGINE: MULTI-STAGE SECURE BUILD PIPELINE ---
# File: Source/build_hft_shm.sh
# Classification: [PRODUCTION // COMPILE UTILITY]

echo "=========================================================="
# 1. Compile Strict Release Binary
echo "[XORAS BUILD] Compiling Strict Shared Memory Release Binary..."
clang++ -O3 -std=c++17 -march=native \
  -Wall -Wextra -Wpedantic -Wshadow -Wconversion -Werror \
  xoras_hft_shm_engine.cpp -o xoras_hft_shm_engine

if [ $? -ne 0 ]; then
    echo "[ERROR] SHM Release compilation failed under strict rules."
    exit 1
fi

# 2. Compile ASAN Shared Memory Binary
echo "[XORAS BUILD] Compiling SHM ASAN Validation Binary..."
clang++ -g -O1 -std=c++17 -fsanitize=address \
  -Wall -Wextra -Wpedantic -Wshadow -Wconversion \
  xoras_hft_shm_engine.cpp -o xoras_hft_shm_engine_asan

if [ $? -ne 0 ]; then
    echo "[ERROR] SHM ASAN compilation failed."
    exit 1
fi

# 3. Compile TSAN Shared Memory Binary
echo "[XORAS BUILD] Compiling SHM TSAN Validation Binary..."
clang++ -g -O1 -std=c++17 -fsanitize=thread \
  -Wall -Wextra -Wpedantic -Wshadow -Wconversion \
  xoras_hft_shm_engine.cpp -o xoras_hft_shm_engine_tsan

if [ $? -ne 0 ]; then
    echo "[ERROR] SHM TSAN compilation failed."
    exit 1
fi

echo "[XORAS BUILD] All SHM targets compiled successfully."
echo "=========================================================="
