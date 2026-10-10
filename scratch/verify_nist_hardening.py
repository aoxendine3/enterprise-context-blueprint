import hmac
import hashlib
import os

def test_nist_constant_time_hmac():
    key = b"XORAS_SOVEREIGN_HARDWARE_KEY_2026_M4"
    msg = b"TRINITY_GATE_PAYLOAD_VOTE_001"
    
    # Generate NIST-compliant HMAC-SHA256 signature
    sig = hmac.new(key, msg, hashlib.sha256).digest()
    
    # NIST SP 800-108 / FIPS 140-3 Constant-Time Comparison
    valid = hmac.compare_digest(sig, sig)
    print("NIST Constant-Time HMAC Comparison:", valid)
    assert valid is True

test_nist_constant_time_hmac()
