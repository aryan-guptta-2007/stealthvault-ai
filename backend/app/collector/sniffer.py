"""
StealthVault AI - Real Network Packet Capture (Scapy)
Captures LIVE packets from the network interface and feeds them to the AI pipeline.

⚠️ Requires:
   - Npcap installed on Windows (https://npcap.com)
   - Run as Administrator for raw packet capture
"""

import asyncio
import time
from datetime import datetime
from typing import Callable, Optional
from collections import deque

try:
    from scapy.all import sniff, IP, TCP, UDP, ICMP, conf
    SCAPY_AVAILABLE = True
except ImportError:
    SCAPY_AVAILABLE = False
    print("⚠️  Scapy not installed. Install with: pip install scapy")

from app.models.alert import NetworkPacket, Protocol


# Suppress Scapy warnings
if SCAPY_AVAILABLE:
    conf.verb = 0


def _map_protocol(packet) -> Protocol:
    """Map Scapy packet layers to our Protocol enum."""
    if TCP in packet:
        sport = packet[TCP].sport
        dport = packet[TCP].dport
        if dport == 80 or sport == 80:
            return Protocol.HTTP
        elif dport == 443 or sport == 443:
            return Protocol.HTTPS
        elif dport == 22 or sport == 22:
            return Protocol.SSH
        elif dport == 21 or sport == 21:
            return Protocol.FTP
        return Protocol.TCP
    elif UDP in packet:
        sport = packet[UDP].sport if UDP in packet else 0
        dport = packet[UDP].dport if UDP in packet else 0
        if dport == 53 or sport == 53:
            return Protocol.DNS
        return Protocol.UDP
    elif ICMP in packet:
        return Protocol.ICMP
    return Protocol.OTHER


def _extract_flags(packet) -> str:
    """Extract TCP flags as a string."""
    if TCP not in packet:
        return ""
    flags = packet[TCP].flags
    flag_str = ""
    if flags & 0x02:
        flag_str += "S"  # SYN
    if flags & 0x10:
        flag_str += "A"  # ACK
    if flags & 0x01:
        flag_str += "F"  # FIN
    if flags & 0x04:
        flag_str += "R"  # RST
    if flags & 0x08:
        flag_str += "P"  # PSH
    if flags & 0x20:
        flag_str += "U"  # URG
    return flag_str


def scapy_to_network_packet(raw_packet) -> Optional[NetworkPacket]:
    """Convert a raw Scapy packet to our NetworkPacket model."""
    if IP not in raw_packet:
        return None

    ip_layer = raw_packet[IP]

    # Extract ports
    src_port = 0
    dst_port = 0
    if TCP in raw_packet:
        src_port = raw_packet[TCP].sport
        dst_port = raw_packet[TCP].dport
    elif UDP in raw_packet:
        src_port = raw_packet[UDP].sport
        dst_port = raw_packet[UDP].dport

    # Calculate payload size
    payload_size = len(raw_packet.payload) if raw_packet.payload else 0

    return NetworkPacket(
        timestamp=datetime.utcnow(),
        src_ip=ip_layer.src,
        dst_ip=ip_layer.dst,
        src_port=src_port,
        dst_port=dst_port,
        protocol=_map_protocol(raw_packet),
        packet_size=len(raw_packet),
        flags=_extract_flags(raw_packet),
        payload_size=payload_size,
        ttl=ip_layer.ttl,
        duration=0.0,
    )


class LiveSniffer:
    """
    Real-time network packet sniffer using Scapy.
    
    Captures live packets, converts them to NetworkPacket objects,
    and pushes them to a processing queue.
    """

    def __init__(self):
        self.is_running: bool = False
        self.packet_queue: asyncio.Queue = None
        self.packets_captured: int = 0
        self.packets_per_second: float = 0.0
        self._start_time: float = 0
        self._recent_counts: deque = deque(maxlen=60)  # Last 60 seconds
        self._callbacks: list[Callable] = []

    def add_callback(self, callback: Callable):
        """Add a callback function to be called for each captured packet."""
        self._callbacks.append(callback)

    def _packet_handler(self, raw_packet):
        """Called by Scapy for each captured packet."""
        packet = scapy_to_network_packet(raw_packet)
        if packet is None:
            return

        self.packets_captured += 1

        # Calculate packets/sec
        elapsed = time.time() - self._start_time
        if elapsed > 0:
            self.packets_per_second = self.packets_captured / elapsed

        # Push to async queue if available
        if self.packet_queue:
            try:
                self.packet_queue.put_nowait(packet)
            except asyncio.QueueFull:
                pass  # Drop packet if queue is full

        # Call registered callbacks
        for cb in self._callbacks:
            try:
                cb(packet)
            except Exception:
                pass

    def start_capture(
        self,
        interface: str = None,
        count: int = 0,
        timeout: int = None,
        bpf_filter: str = None,
        queue: asyncio.Queue = None,
    ):
        """
        Start capturing packets.
        
        Args:
            interface: Network interface name (None = default)
            count: Number of packets to capture (0 = infinite)
            timeout: Stop after N seconds (None = no timeout)
            bpf_filter: BPF filter string (e.g., "tcp port 80")
            queue: Async queue to push packets to
        """
        if not SCAPY_AVAILABLE:
            raise RuntimeError(
                "Scapy is not installed. Install with: pip install scapy\n"
                "Also install Npcap: https://npcap.com"
            )

        self.packet_queue = queue
        self.is_running = True
        self._start_time = time.time()
        self.packets_captured = 0

        retry_count = 0
        max_retries = 5
        backoff = 2

        print(f"🔍 Starting live capture...")
        print(f"   Interface: {interface or 'default'}")
        print(f"   Filter: {bpf_filter or 'none'}")
        print(f"   Count: {count or 'infinite'}")
        print()

        while self.is_running and (retry_count < max_retries or count != 0):
            try:
                sniff(
                    iface=interface,
                    prn=self._packet_handler,
                    count=count,
                    timeout=timeout,
                    filter=bpf_filter,
                    store=False,
                )
                # If sniff returns normally, it finished its requested count or timeout
                break
            except PermissionError:
                self.is_running = False
                print("❌ Permission denied. Run as Administrator for packet capture.")
                raise
            except Exception as e:
                retry_count += 1
                if not self.is_running:
                    break
                
                print(f"⚠️ Capture error: {e}. Attempting restart {retry_count}/{max_retries} in {backoff}s...")
                time.sleep(backoff)
                backoff *= 2
        
        self.is_running = False

    def stop(self):
        """Stop the capture."""
        self.is_running = False

    def get_stats(self) -> dict:
        """Get capture statistics."""
        elapsed = time.time() - self._start_time if self._start_time else 0
        return {
            "is_running": self.is_running,
            "packets_captured": self.packets_captured,
            "packets_per_second": round(self.packets_per_second, 2),
            "elapsed_seconds": round(elapsed, 1),
        }


# Singleton
live_sniffer = LiveSniffer()
