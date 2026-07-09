import asyncio
import socket
import os
import platform


class OffensiveSentinel:
    def __init__(self):
        self.honeypot_ports = [8888, 8889, 9999]
        self.blacklisted_ips = set()
        print("[OFFENSIVE-OPSEC] Sentinel Initialized. Weaponizing perimeter...")

    def _generate_blackhole_command(self, ip):
        """Generates OS-specific firewall commands to drop IP traffic."""
        os_type = platform.system()
        if os_type == "Linux":
            return f"sudo iptables -A INPUT -s {ip} -j DROP"
        elif os_type == "Darwin":  # macOS
            # Note: Requires creating a pf.conf anchor, simulating here for safety
            return f'echo "block drop in from {ip} to any" | sudo pfctl -a xoras_blackhole -f -'
        else:
            return f"REM OS not supported for automated blackholing of {ip}"

    async def _tarpit_connection(self, reader, writer, port):
        peername = writer.get_extra_info('peername')
        if not peername:
            writer.close()
            return

        ip = peername[0]

        # We will trap all IPs for the demonstration, even localhost.
        if ip not in self.blacklisted_ips:
            print(
                f"\n[OFFENSIVE-OPSEC] HOSTILE PROBE DETECTED: IP {ip} probed port {port}")
            print(f"[OFFENSIVE-OPSEC] Engaging Tarpit... trapping connection.")
            self.blacklisted_ips.add(ip)

            cmd = self._generate_blackhole_command(ip)
            print(
                f"[OFFENSIVE-OPSEC] Firewall Blackhole command generated:\n    -> {cmd}")

        try:
            # The Tarpit: Keep connection open, send 1 byte of garbage every 10 seconds
            while True:
                writer.write(b'\x00')
                await writer.drain()
                await asyncio.sleep(10)
        except Exception:
            pass  # Connection finally closed by attacker
        finally:
            writer.close()

    async def _start_honeypot(self, port):
        try:
            server = await asyncio.start_server(
                lambda r, w: self._tarpit_connection(r, w, port),
                '0.0.0.0', port
            )
            print(f"[HONEYPOT] Deceptive listener armed on port {port}")
            async with server:
                await server.serve_forever()
        except OSError:
            print(f"[HONEYPOT] Port {port} already in use or requires root. Skipping.")

    async def arm_perimeter(self):
        print("==========================================")
        print("    XORAS OFFENSIVE SENTINEL (ARMED)      ")
        print("==========================================")
        tasks = [self._start_honeypot(port) for port in self.honeypot_ports]
        await asyncio.gather(*tasks)


if __name__ == "__main__":
    sentinel = OffensiveSentinel()
    try:
        asyncio.run(sentinel.arm_perimeter())
    except KeyboardInterrupt:
        print("\n[OFFENSIVE-OPSEC] Sentinel disarmed.")
