# SIA Core: Swarm Tactical Defense & Intrusion Sentry
import socket, time

class TacticalDefenseEngine:
    def probe_loopback_boundaries(self):
        ports_to_monitor = [8080, 11434, 5173]
        status = {}
        for port in ports_to_monitor:
            s = socket.socket()
            s.settimeout(0.1)
            res = s.connect_ex(('127.0.0.1', port))
            status[port] = "OPEN_AUTHORIZED" if res == 0 else "CLOSED_SECURE"
            s.close()
        return {"sentry_status": "ARMED", "ports": status}

if __name__ == "__main__":
    print(TacticalDefenseEngine().probe_loopback_boundaries())\n