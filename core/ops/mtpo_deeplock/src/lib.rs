use pyo3::prelude::*;
use std::collections::HashMap;
use std::sync::Mutex;
use sha2::{Sha256, Digest};

#[derive(Clone, Debug)]
pub struct SagaEntry {
    pub phase: String,
    pub tx_hash: String,
    pub payload: Option<String>,
}

#[pyclass]
pub struct NativeMTPODeeplock {
    #[pyo3(get)]
    pub agent_id: String,
    #[pyo3(get)]
    pub rank: u32,
    saga_log: Mutex<Vec<SagaEntry>>,
    state_table: Mutex<HashMap<String, String>>,
}

#[pymethods]
impl NativeMTPODeeplock {
    #[new]
    pub fn new(agent_id: String, rank: u32) -> Self {
        NativeMTPODeeplock {
            agent_id,
            rank,
            saga_log: Mutex::new(Vec::new()),
            state_table: Mutex::new(HashMap::new()),
        }
    }

    pub fn prepare(&self, payload_str: String) -> PyResult<String> {
        let mut hasher = Sha256::new();
        hasher.update(payload_str.as_bytes());
        let tx_hash = format!("{:x}", hasher.finalize());

        let mut log = self.saga_log.lock().unwrap();
        log.push(SagaEntry {
            phase: "PREPARE".to_string(),
            tx_hash: tx_hash.clone(),
            payload: Some(payload_str),
        });

        Ok(tx_hash)
    }

    pub fn execute(&self, tx_hash: String) -> PyResult<bool> {
        let mut log = self.saga_log.lock().unwrap();
        log.push(SagaEntry {
            phase: "EXECUTE".to_string(),
            tx_hash: tx_hash.clone(),
            payload: None,
        });

        let mut state = self.state_table.lock().unwrap();
        state.insert(tx_hash, "COMMITTED_ZERO_ABORT".to_string());
        Ok(true)
    }

    pub fn reverse(&self, tx_hash: String) -> PyResult<bool> {
        let mut log = self.saga_log.lock().unwrap();
        log.push(SagaEntry {
            phase: "REVERSE".to_string(),
            tx_hash: tx_hash.clone(),
            payload: None,
        });

        let mut state = self.state_table.lock().unwrap();
        state.remove(&tx_hash);
        Ok(true)
    }

    pub fn get_saga_depth(&self) -> PyResult<usize> {
        let log = self.saga_log.lock().unwrap();
        Ok(log.len())
    }
}

#[pymodule]
fn mtpo_deeplock_core(_py: Python, m: &PyModule) -> PyResult<()> {
    m.add_class::<NativeMTPODeeplock>()?;
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_native_mtpo_lifecycle() {
        let lock = NativeMTPODeeplock::new("DAXX_CORE_TEST".to_string(), 9);
        let hash = lock.prepare("test_vector_sync".to_string()).unwrap();
        assert_eq!(hash.len(), 64);
        assert!(lock.execute(hash.clone()).unwrap());
        assert_eq!(lock.get_saga_depth().unwrap(), 2);
        assert!(lock.reverse(hash).unwrap());
        assert_eq!(lock.get_saga_depth().unwrap(), 3);
    }
}
