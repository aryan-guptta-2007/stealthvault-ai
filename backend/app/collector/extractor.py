"""
StealthVault AI - Feature Extractor
Converts raw network packet data into numeric feature vectors for AI processing.
"""

import numpy as np
from app.models.alert import NetworkPacket, FeatureVector, Protocol


class FeatureExtractor:
    """Extracts ML-ready features from network packets."""

    # Normalization ranges for each feature
    NORM_RANGES = {
        "src_port": (0, 65535),
        "dst_port": (0, 65535),
        "packet_size": (0, 65535),
        "payload_size": (0, 65535),
        "ttl": (0, 255),
        "duration": (0, 300),
    }

    def extract(self, packet: NetworkPacket) -> FeatureVector:
        """Extract and normalize features from a network packet with extreme safety boundaries."""
        
        def safe_float(val, default=0.0):
            try:
                return float(val) if val is not None else default
            except (ValueError, TypeError):
                return default

        # Normalize numeric features to [0, 1] safely
        src_port = self._normalize(safe_float(packet.src_port), *self.NORM_RANGES["src_port"])
        dst_port = self._normalize(safe_float(packet.dst_port), *self.NORM_RANGES["dst_port"])
        packet_size = self._normalize(safe_float(packet.packet_size), *self.NORM_RANGES["packet_size"])
        payload_size = self._normalize(safe_float(packet.payload_size), *self.NORM_RANGES["payload_size"])
        ttl = self._normalize(safe_float(packet.ttl, 64.0), *self.NORM_RANGES["ttl"])
        duration = self._normalize(safe_float(packet.duration), *self.NORM_RANGES["duration"])

        # Safely extract protocol mapping
        protocol = getattr(packet, "protocol", Protocol.TCP)
        protocol_tcp = 1.0 if protocol in [Protocol.TCP, Protocol.HTTP, Protocol.HTTPS, Protocol.SSH, Protocol.FTP] else 0.0
        protocol_udp = 1.0 if protocol in [Protocol.UDP, Protocol.DNS] else 0.0
        protocol_icmp = 1.0 if protocol == Protocol.ICMP else 0.0
        protocol_http = 1.0 if protocol in [Protocol.HTTP, Protocol.HTTPS] else 0.0

        # Safely parse TCP flags
        flags = packet.flags.upper() if getattr(packet, "flags", None) else ""
        flag_syn = 1.0 if "S" in flags or "SYN" in flags else 0.0
        flag_ack = 1.0 if "A" in flags or "ACK" in flags else 0.0
        flag_fin = 1.0 if "F" in flags or "FIN" in flags else 0.0
        flag_rst = 1.0 if "R" in flags or "RST" in flags else 0.0
        flag_psh = 1.0 if "P" in flags or "PSH" in flags else 0.0

        return FeatureVector(
            src_port=src_port,
            dst_port=dst_port,
            packet_size=packet_size,
            payload_size=payload_size,
            ttl=ttl,
            duration=duration,
            protocol_tcp=protocol_tcp,
            protocol_udp=protocol_udp,
            protocol_icmp=protocol_icmp,
            protocol_http=protocol_http,
            flag_syn=flag_syn,
            flag_ack=flag_ack,
            flag_fin=flag_fin,
            flag_rst=flag_rst,
            flag_psh=flag_psh,
        )

    def to_numpy(self, features: FeatureVector) -> np.ndarray:
        """Convert FeatureVector to numpy array for model input."""
        return np.array([
            features.src_port,
            features.dst_port,
            features.packet_size,
            features.payload_size,
            features.ttl,
            features.duration,
            features.protocol_tcp,
            features.protocol_udp,
            features.protocol_icmp,
            features.protocol_http,
            features.flag_syn,
            features.flag_ack,
            features.flag_fin,
            features.flag_rst,
            features.flag_psh,
        ], dtype=np.float32).reshape(1, -1)

    @staticmethod
    def _normalize(value: float, min_val: float, max_val: float) -> float:
        """Normalize a value to [0, 1] range."""
        if max_val == min_val:
            return 0.0
        return max(0.0, min(1.0, (value - min_val) / (max_val - min_val)))


# Singleton instance
extractor = FeatureExtractor()
