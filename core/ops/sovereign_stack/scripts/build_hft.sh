#!/bin/bash
# --- XORAS HFT ENGINE: MULTI-STAGE SECURE BUILD PIPELINE ---
# File: Source/build_hft.sh
# Classification: [PRODUCTION // COMPILE UTILITY]

echo "=========================================================="
# 1. Compile Strict Release Binary (Pedantic, Speed Optimized)
echo "[XORAS BUILD] Compiling Strict Release Binary..."
clang++ -O3 -std=c++17 -march=native \
  -Wall -Wextra -Wpedantic -Wshadow -Wconversion -Werror \
  -o xoras_hft_engine xoras_hft_core.cpp

if [ $? -ne 0 ]; then
    echo "[ERROR] Release compilation failed under strict compiler rules."
    exit 1
fi

# 2. Compile Address Sanitizer Binary (ASAN - Memory Safety Verification)
echo "[XORAS BUILD] Compiling ASAN Validation Binary..."
clang++ -g -O1 -std=c++17 -fsanitize=address \
  -Wall -Wextra -Wpedantic -Wshadow -Wconversion \
  -o xoras_hft_engine_asan xoras_hft_core.cpp

if [ $? -ne 0 ]; then
    echo "[ERROR] ASAN binary compilation failed."
    exit 1
fi

# 3. Compile Thread Sanitizer Binary (TSAN - Concurrency/Race Verification)
echo "[XORAS BUILD] Compiling TSAN Validation Binary..."
clang++ -g -O1 -std=c++17 -fsanitize=thread \
  -Wall -Wextra -Wpedantic -Wshadow -Wconversion \
  -o xoras_hft_engine_tsan xoras_hft_core.cpp

if [ $? -ne 0 ]; then
    echo "[ERROR] TSAN binary compilation failed."
    exit 1
fi

echo "[XORAS BUILD] All targets compiled successfully."
echo "=========================================================="
