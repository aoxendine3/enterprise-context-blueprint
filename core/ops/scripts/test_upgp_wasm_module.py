#!/usr/bin/env python3
import subprocess
import os
import sys

def test_wasm_binary():
    wasm_path = "/Users/ajoxendine68/Desktop/SSOT_Agentic_Brain/docs/assets/wasm/upgp_simulator.wasm"
    if not os.path.exists(wasm_path):
        print(f"❌ WASM Binary not found at {wasm_path}")
        sys.exit(1)
        
    print(f"[STEP 1] Validating Compiled WASM File Exists ({os.path.getsize(wasm_path)} bytes)...")
    
    # Run Node.js inline script to test WebAssembly instantiation and function exports
    node_test_script = f"""
    const fs = require('fs');
    const wasmBuffer = fs.readFileSync('{wasm_path}');
    
    WebAssembly.instantiate(wasmBuffer).then(wasmModule => {{
        const exports = wasmModule.instance.exports;
        console.log('  * Exports:', Object.keys(exports));
        
        const hexSize = exports.init_hexcell_topology(25);
        console.log('  * init_hexcell_topology(25) =', hexSize, '(Expected 3200)');
        if (hexSize !== 3200) process.exit(1);
        
        const ops = exports.simulate_mtpo_concurrency(100, 1000);
        console.log('  * simulate_mtpo_concurrency(100, 1000) =', ops);
        if (ops <= 0) process.exit(1);
        
        const rollback = exports.trigger_saga_rollback(42);
        console.log('  * trigger_saga_rollback(42) =', rollback, '(Expected 1)');
        if (rollback !== 1) process.exit(1);
        
        const secureState = exports.verify_state_signature(123456789n, 0xABCDEF, 0x76);
        console.log('  * verify_state_signature(pristine 0x76) =', secureState, '(Expected 1 SECURE)');
        if (secureState !== 1) process.exit(1);
        
        const corruptState = exports.verify_state_signature(123456789n, 0xABCDEF, 0x06);
        console.log('  * verify_state_signature(bit-flipped 0x06) =', corruptState, '(Expected 0 CORRUPTED)');
        if (corruptState !== 0) process.exit(1);
        
        console.log('✅ ALL WASM EXPORTED FUNCTIONS PASSED UN-MOCKED INTEGRITY CHECKS!');
    }}).catch(err => {{
        console.error('❌ WASM Instantiation Error:', err);
        process.exit(1);
    }});
    """
    
    result = subprocess.run(["node", "-e", node_test_script], capture_output=True, text=True)
    print(result.stdout)
    if result.returncode != 0:
        print(f"❌ WASM Test Failed:\n{result.stderr}")
        sys.exit(1)
        
    print("==========================================================================")
    print("  ✅ UN-MOCKED WEBASSEMBLY KERNEL VERIFICATION 100% PASSED")
    print("==========================================================================")

if __name__ == "__main__":
    test_wasm_binary()
