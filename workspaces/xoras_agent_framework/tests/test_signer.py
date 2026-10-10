"""
Unit tests for XORAS Cryptographic Signer.
"""

from xoras.signer import CryptographicSigner

def test_evidence_receipt_signing_and_verification():
    signer = CryptographicSigner()
    payload = {"path": "test.txt", "content": "hello world"}
    receipt = signer.sign_receipt("Engineer", "file_write", payload, "SUCCESS")
    
    assert receipt.version == "xoras.evidence.v1"
    assert receipt.organization == "XORAS Systems LLC"
    assert receipt.status == "SUCCESS"
    assert receipt.signature is not None
    
    # Verify signature mathematically
    assert signer.verify_receipt(receipt) is True

def test_evidence_receipt_tamper_rejection():
    signer = CryptographicSigner()
    payload = {"path": "test.txt", "content": "hello world"}
    receipt = signer.sign_receipt("Engineer", "file_write", payload, "SUCCESS")
    
    # Tamper with status
    receipt.status = "FAILED"
    assert signer.verify_receipt(receipt) is False
