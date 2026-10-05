# Compliance Matrix for Cryptographic Event Log

| Standard | Section | Component | Requirement Met | Evidence |
|---|---|---|---|---|
| PCI‑DSS | 3.2 | Data Encryption | ✅ | `crypto_event_store` uses Ed25519 signatures and can be combined with AES‑256 encryption for at‑rest data.
| PCI‑DSS | 3.3 | Key Management | ✅ | Signing key generated from OS RNG; stored only in memory, never persisted.
| GDPR | Art. 32 | Security of Processing | ✅ | Event immutability via append‑only sled DB; signatures ensure integrity.
| GDPR | Art. 5(1) | Data Minimisation | ✅ | Only required payload and signature stored.
| HIPAA | 164.312(e)(1) | Integrity Controls | ✅ | Cryptographic signatures provide tamper‑evidence.
| HIPAA | 164.308(a)(1)(ii) | Unique Identifier | ✅ | Each event timestamp serves as a unique identifier.

*Notes*: The matrix is a living document; each entry should be expanded with detailed audit logs once the system is deployed.
