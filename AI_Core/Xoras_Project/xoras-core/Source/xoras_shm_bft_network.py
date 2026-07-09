import os
import sys
import time
import socket
import struct
import threading
from multiprocessing import shared_memory

# High-Availability BFT TCP Network Relay with Auto-Reconnection
# Connects Host (Node A) and Client (Node B) shared memory layers with fault tolerance.

PORT = 50051
SLOT_SIZE = 131
LOCAL_NODES = [0, 1, 2, 3]
REMOTE_NODES = [4, 5, 6, 7]

def host_loop(shm_name, client_ip):
    print(f"[*] Starting Fault-Tolerant Host Network Relay to {client_ip}:{PORT}...")
    try:
        shm = shared_memory.SharedMemory(name=shm_name)
    except Exception as e:
        print(f"[-] SHM error: {e}")
        return

    while True:
        # Check stop flag in SHM
        if shm.buf[2] == 1:
            break

        print(f"[*] Attempting connection to Client ({client_ip}:{PORT})...")
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
        
        connected = False
        while not connected:
            if shm.buf[2] == 1:
                s.close()
                return
            try:
                s.connect((client_ip, PORT))
                print("[+] Connected to Client Node B.")
                connected = True
            except Exception:
                time.sleep(1)

        # Reader thread to receive votes from Client
        def receive_votes(sock):
            while True:
                try:
                    header = sock.recv(4)
                    if not header:
                        break
                    node_id = struct.unpack("<I", header)[0]
                    slot_data = sock.recv(SLOT_SIZE)
                    if len(slot_data) < SLOT_SIZE:
                        break
                    
                    offset = 300 + (node_id * SLOT_SIZE)
                    shm.buf[offset:offset+SLOT_SIZE] = slot_data
                except Exception as e:
                    print(f"[-] Connection dropped during read: {e}")
                    break
            print("[-] Reader thread terminated.")

        t = threading.Thread(target=receive_votes, args=(s,), daemon=True)
        t.start()

        # Transmitter loop: watch local state and push changes
        last_round_state = -1
        last_round_number = -1
        
        while True:
            try:
                # Check socket status
                if not t.is_alive():
                    break

                round_state = shm.buf[0]
                round_number = shm.buf[3]
                proposal_value = shm.buf[1]
                stop_flag = shm.buf[2]

                if round_state != last_round_state or round_number != last_round_number:
                    packet = struct.pack("<BBBB", round_state, round_number, proposal_value, stop_flag)
                    s.sendall(packet)
                    print(f"[+] Broadcast state: round={round_number}, state={round_state}")
                    last_round_state = round_state
                    last_round_number = round_number

                if stop_flag == 1:
                    s.close()
                    shm.close()
                    return

                time.sleep(0.001)
            except Exception as e:
                print(f"[-] Connection dropped during write: {e}")
                break

        s.close()
        print("[-] Connection lost. Initiating host reconnect sequence...")
        time.sleep(2)

def client_loop(shm_name):
    print(f"[*] Starting Fault-Tolerant Client Network Relay on port {PORT}...")
    try:
        shm = shared_memory.SharedMemory(name=shm_name)
    except Exception as e:
        print(f"[-] SHM error: {e}")
        return

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind(("", PORT))
    s.listen(1)

    while True:
        if shm.buf[2] == 1:
            break

        print("[*] Listening for Host connection...")
        try:
            conn, addr = s.accept()
            print(f"[+] Host connected from {addr}")
        except Exception as e:
            print(f"[-] Accept error: {e}")
            break

        # Thread to send local votes back to Host
        def send_votes(connection):
            last_votes = {}
            while True:
                try:
                    for node_id in REMOTE_NODES:
                        offset = 300 + (node_id * SLOT_SIZE)
                        vote = shm.buf[offset]
                        if vote != 0 and last_votes.get(node_id) != vote:
                            slot_data = shm.buf[offset:offset+SLOT_SIZE]
                            packet = struct.pack("<I", node_id) + bytes(slot_data)
                            connection.sendall(packet)
                            last_votes[node_id] = vote
                    time.sleep(0.001)
                except Exception:
                    break
            print("[-] Sender thread terminated.")

        t = threading.Thread(target=send_votes, args=(conn,), daemon=True)
        t.start()

        # Reader loop: receive coordinator state from Host
        while True:
            try:
                data = conn.recv(4)
                if not data:
                    break
                round_state, round_number, proposal_value, stop_flag = struct.unpack("<BBBB", data)
                
                shm.buf[0] = round_state
                shm.buf[3] = round_number
                shm.buf[1] = proposal_value
                shm.buf[2] = stop_flag
                print(f"[+] Synced coordinator state: round={round_number}, state={round_state}")

                if stop_flag == 1:
                    conn.close()
                    s.close()
                    shm.close()
                    return
            except Exception as e:
                print(f"[-] Connection read error: {e}")
                break

        conn.close()
        print("[-] Host disconnected. Waiting for next connection...")
        time.sleep(2)

    s.close()

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python3 xoras_shm_bft_network.py --host <shm_name> <client_ip>")
        print("   or: python3 xoras_shm_bft_network.py --client <shm_name>")
        sys.exit(1)

    mode = sys.argv[1]
    name = sys.argv[2]

    if mode == "--host":
        ip = sys.argv[3]
        host_loop(name, ip)
    elif mode == "--client":
        client_loop(name)
    else:
        print("[-] Invalid mode.")
