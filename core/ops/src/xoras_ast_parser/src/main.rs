use std::net::{TcpListener, TcpStream, UdpSocket};
use std::thread;
use std::io::{Read, Write};
use ed25519_dalek::{Verifier, Signature, VerifyingKey};
use hex;

const TCP_PORT: u16 = 8787;
const UDP_PORT: u16 = 11434;

// Hardcoded public key for the handshake (derived from trusted head node)
// In production, this lives in the integrity registry.
const TRUSTED_PUBKEY_HEX: &str = "f16c6a5bedfe2f195a3fcce37ccfaadfde6815ef4e4ee0959e91780cdf0ea17a";

fn handle_tcp_client(mut stream: TcpStream) {
    let mut buffer = [0; 1024];
    if let Ok(size) = stream.read(&mut buffer) {
        if size == 0 { return; }
        let payload = String::from_utf8_lossy(&buffer[..size]);
        println!("[TCP 8787] Received {} bytes. Verifying Ed25519 signature...", size);
        
        // Expected format: <64-byte-hex-signature>|<message>
        let parts: Vec<&str> = payload.splitn(2, '|').collect();
        if parts.len() == 2 {
            let sig_hex = parts[0];
            let msg = parts[1];
            
            let pubkey_bytes = hex::decode(TRUSTED_PUBKEY_HEX).unwrap_or_default();
            if let Ok(public_key) = VerifyingKey::try_from(pubkey_bytes.as_slice()) {
                if let Ok(sig_bytes) = hex::decode(sig_hex) {
                    if sig_bytes.len() == 64 {
                        let signature = Signature::from_bytes(sig_bytes.as_slice().try_into().unwrap());
                        if public_key.verify(msg.as_bytes(), &signature).is_ok() {
                            println!("[TCP 8787] Cryptographic Gate: PASSED. Payload: {}", msg);
                            let _ = stream.write_all(b"HANDSHAKE_VERIFIED_ACK\n");
                            return;
                        }
                    }
                }
            }
        }
        println!("[TCP 8787] Cryptographic Gate: REJECTED. Dropping packet.");
        let _ = stream.write_all(b"GATE_REJECTED\n");
    }
}

fn main() {
    println!("[XORAS::OS] AST Parser Daemon booting on bare-metal M4...");
    
    // Spawn UDP listener (Tensor Stream)
    thread::spawn(|| {
        let udp = UdpSocket::bind(("0.0.0.0", UDP_PORT)).expect("Failed to bind UDP 11434");
        println!("[UDP {}] HexCell Tensor Stream interface active.", UDP_PORT);
        let mut buf = [0; 3200]; // 3,200 byte HexCell strides
        loop {
            if let Ok((size, src)) = udp.recv_from(&mut buf) {
                // Raw drop unverified / simulate SIMD routing
                println!("[UDP {}] Received {} bytes from {}", UDP_PORT, size, src);
            }
        }
    });

    // Main thread TCP listener (Control Signaling)
    let tcp = TcpListener::bind(("0.0.0.0", TCP_PORT)).expect("Failed to bind TCP 8787");
    println!("[TCP {}] Synchronous Control AST Signaling active.", TCP_PORT);
    
    for stream in tcp.incoming() {
        match stream {
            Ok(s) => {
                thread::spawn(move || handle_tcp_client(s));
            }
            Err(e) => println!("TCP connection failed: {}", e),
        }
    }
}
