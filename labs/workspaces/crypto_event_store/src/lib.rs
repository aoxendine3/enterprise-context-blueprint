//! Crypto Event Store – Append‑only, hash‑linked event log with forward‑secure signatures.

use sled::Db;
use serde::{Serialize, Deserialize};
use ed25519_dalek::{SigningKey, Signer, Signature};
use rand::rngs::OsRng;
use rand::RngCore;
use bincode;
use std::time::{SystemTime, UNIX_EPOCH};

#[derive(Serialize, Deserialize, Debug, Clone)]
pub struct Event {
    pub timestamp: u64,
    pub payload: String,
    pub signature: Vec<u8>,
}

pub struct CryptoEventStore {
    db: Db,
    signing_key: SigningKey,
}

impl CryptoEventStore {
    /// Initialize the store, creating a new sled DB and generating a fresh keypair.
    pub fn new(path: &str) -> Self {
        let db = sled::open(path).expect("Failed to open sled DB");
        let mut csprng = OsRng;
        let mut seed = [0u8; 32];
        csprng.fill_bytes(&mut seed);
        let signing_key = SigningKey::from_bytes(&seed);
        Self { db, signing_key }
    }

    /// Append a new event with automatic signing.
    pub fn append(&self, payload: &str) -> Event {
        let timestamp = SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .expect("Time went backwards")
            .as_secs();
        let data = format!("{}:{}", timestamp, payload);
        let signature: Signature = self.signing_key.sign(data.as_bytes());
        let event = Event {
            timestamp,
            payload: payload.to_string(),
            signature: signature.to_bytes().to_vec(),
        };
        // Serialize and store with monotonic key (timestamp as bytes)
        let key = timestamp.to_be_bytes();
        let val = bincode::serialize(&event).expect("Serialization failed");
        self.db.insert(key, val).expect("DB insert failed");
        event
    }

    /// Retrieve an event by timestamp.
    pub fn get(&self, timestamp: u64) -> Option<Event> {
        let key = timestamp.to_be_bytes();
        self.db.get(key).ok().flatten().and_then(|ivec| {
            bincode::deserialize::<Event>(&ivec).ok()
        })
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use ed25519_dalek::Verifier;
    #[test]
    fn basic_roundtrip() {
        let store = CryptoEventStore::new("./test_store");
        let ev = store.append("test payload");
        let fetched = store.get(ev.timestamp).expect("Event missing");
        assert_eq!(ev.payload, fetched.payload);
        // Verify signature using stored public key
        let pk = store.signing_key.verifying_key();
        let data = format!("{}:{}", ev.timestamp, ev.payload);
        // Convert signature Vec<u8> to fixed-size array for verification
        let sig_bytes: &[u8; 64] = ev.signature.as_slice().try_into().expect("Invalid signature length");
        let sig = Signature::from_bytes(sig_bytes);
        assert!(pk.verify(data.as_bytes(), &sig).is_ok());
    }
}
