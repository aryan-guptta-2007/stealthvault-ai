"""
StealthVault AI - Demo Data Generator
Generates realistic simulated network traffic with known attack patterns.
Used for training AI models and demonstrating the system without real network capture.
"""

import numpy as np
import os
import sys
import json
from datetime import datetime, timedelta


def safe_randint(low, high):
    """np.random.randint that handles low == high."""
    if low >= high:
        return low
    return np.random.randint(low, high)

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.models.alert import NetworkPacket, Protocol, AttackType
from app.collector.extractor import extractor
from app.ai_engine.anomaly import anomaly_detector
from app.ai_engine.classifier import attack_classifier


# ─── Traffic Generation Profiles ───────────────────────────────────────────────

NORMAL_PROFILES = [
    # Web browsing
    {"dst_port_range": (80, 80), "protocol": Protocol.HTTP, "size_range": (200, 1500), "flags": "SA"},
    {"dst_port_range": (443, 443), "protocol": Protocol.HTTPS, "size_range": (200, 1500), "flags": "SA"},
    # DNS
    {"dst_port_range": (53, 53), "protocol": Protocol.DNS, "size_range": (40, 512), "flags": ""},
    # SSH
    {"dst_port_range": (22, 22), "protocol": Protocol.SSH, "size_range": (100, 800), "flags": "SA"},
    # General TCP
    {"dst_port_range": (1024, 8080), "protocol": Protocol.TCP, "size_range": (64, 2000), "flags": "SA"},
]

ATTACK_PROFILES = {
    AttackType.DDOS: {
        "dst_port_range": (80, 443),
        "protocol": Protocol.TCP,
        "size_range": (40, 100),  # Small packets, high volume
        "flags": "S",  # SYN flood
        "ttl_range": (20, 60),
        "src_ips": ["10.0.{}.{}".format(np.random.randint(1, 254), np.random.randint(1, 254)) for _ in range(50)],
    },
    AttackType.PORT_SCAN: {
        "dst_port_range": (1, 65535),  # Scanning all ports
        "protocol": Protocol.TCP,
        "size_range": (40, 60),
        "flags": "S",
        "ttl_range": (50, 64),
        "src_ips": ["192.168.1.100"],
    },
    AttackType.BRUTE_FORCE: {
        "dst_port_range": (22, 22),  # SSH brute force
        "protocol": Protocol.SSH,
        "size_range": (100, 300),
        "flags": "SA",
        "ttl_range": (55, 64),
        "src_ips": ["172.16.0.{}".format(np.random.randint(1, 10)) for _ in range(5)],
    },
    AttackType.MALWARE: {
        "dst_port_range": (4444, 9999),  # C2 ports
        "protocol": Protocol.TCP,
        "size_range": (50, 200),
        "flags": "PA",  # PSH+ACK (data push)
        "ttl_range": (100, 128),
        "src_ips": ["10.0.0.50"],
    },
    AttackType.SQL_INJECTION: {
        "dst_port_range": (80, 80),
        "protocol": Protocol.HTTP,
        "size_range": (500, 3000),  # Large payloads
        "flags": "PA",
        "ttl_range": (60, 64),
        "src_ips": ["203.0.113.{}".format(np.random.randint(1, 50)) for _ in range(10)],
    },
    AttackType.XSS: {
        "dst_port_range": (80, 443),
        "protocol": Protocol.HTTP,
        "size_range": (300, 2000),
        "flags": "PA",
        "ttl_range": (60, 64),
        "src_ips": ["198.51.100.{}".format(np.random.randint(1, 30)) for _ in range(8)],
    },
}


def generate_normal_packet(timestamp: datetime) -> NetworkPacket:
    """Generate a single normal traffic packet with noise and jitter."""
    profile = NORMAL_PROFILES[np.random.randint(0, len(NORMAL_PROFILES))]

    # Add background noise/jitter
    size_noise = np.random.randint(-20, 20)
    jitter = round(np.random.normal(0, 0.05), 3)
    
    return NetworkPacket(
        timestamp=timestamp,
        src_ip=f"192.168.1.{np.random.randint(1, 254)}",
        dst_ip=f"10.0.0.{np.random.randint(1, 50)}",
        src_port=np.random.randint(1024, 65535),
        dst_port=safe_randint(*profile["dst_port_range"]),
        protocol=profile["protocol"],
        packet_size=max(40, np.random.randint(*profile["size_range"]) + size_noise),
        flags=profile["flags"],
        payload_size=max(0, np.random.randint(0, profile["size_range"][1] // 2) + size_noise),
        ttl=np.random.randint(55, 128),
        duration=max(0.001, round(np.random.exponential(0.5) + jitter, 3)),
    )


def generate_attack_packet(attack_type: AttackType, timestamp: datetime) -> NetworkPacket:
    """Generate a single attack packet with unpredictable patterns."""
    profile = ATTACK_PROFILES.get(attack_type)
    
    if not profile: # Handle Unknown / Zero-Day
        return NetworkPacket(
            timestamp=timestamp,
            src_ip=f"45.{np.random.randint(1, 255)}.{np.random.randint(1, 255)}.{np.random.randint(1, 255)}",
            dst_ip="10.0.0.1",
            src_port=np.random.randint(1024, 65535),
            dst_port=np.random.choice([23, 445, 3389, 5900]), # Interesting ports
            protocol=Protocol.TCP,
            packet_size=np.random.randint(100, 500),
            flags="PA",
            payload_size=np.random.randint(50, 400),
            ttl=np.random.randint(30, 60),
            duration=round(np.random.random(), 3),
        )

    src_ip = np.random.choice(profile["src_ips"])
    dst_port_range = profile["dst_port_range"]

    if attack_type == AttackType.PORT_SCAN:
        # Randomized sequential port scanning (stealthier)
        dst_port = np.random.randint(1, 1024) if np.random.random() > 0.1 else np.random.randint(1024, 65535)
    else:
        dst_port = safe_randint(*dst_port_range)

    return NetworkPacket(
        timestamp=timestamp,
        src_ip=src_ip,
        dst_ip="10.0.0.1",
        src_port=np.random.randint(1024, 65535),
        dst_port=dst_port,
        protocol=profile["protocol"],
        packet_size=np.random.randint(*profile["size_range"]),
        flags=profile["flags"],
        payload_size=np.random.randint(0, profile["size_range"][1]),
        ttl=np.random.randint(*profile["ttl_range"]),
        duration=max(0.001, round(np.random.exponential(0.1), 3)),
    )


def generate_training_data(
    n_normal: int = 5000,
    n_attacks_per_type: int = 500,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Generate complete training dataset.
    
    Returns:
        normal_data: Feature vectors of normal traffic (for anomaly detector)
        X_all: All feature vectors (for classifier)
        y_all: Labels for all features
    """
    print("🔧 Generating training data...")
    base_time = datetime.utcnow() - timedelta(hours=1)

    # Generate normal traffic
    normal_features = []
    for i in range(n_normal):
        timestamp = base_time + timedelta(seconds=i * 0.1)
        packet = generate_normal_packet(timestamp)
        features = extractor.extract(packet)
        normal_features.append(extractor.to_numpy(features).flatten())

    normal_data = np.array(normal_features)
    print(f"  ✅ Generated {n_normal} normal traffic samples")

    # Generate attack traffic
    all_features = list(normal_features)
    all_labels = [AttackType.NORMAL.value] * n_normal

    attack_types = [
        AttackType.DDOS,
        AttackType.PORT_SCAN,
        AttackType.BRUTE_FORCE,
        AttackType.MALWARE,
        AttackType.SQL_INJECTION,
        AttackType.XSS,
    ]

    for attack_type in attack_types:
        for i in range(n_attacks_per_type):
            timestamp = base_time + timedelta(seconds=(n_normal + i) * 0.1)
            packet = generate_attack_packet(attack_type, timestamp)
            features = extractor.extract(packet)
            all_features.append(extractor.to_numpy(features).flatten())
            all_labels.append(attack_type.value)
        print(f"  ✅ Generated {n_attacks_per_type} {attack_type.value} attack samples")

    X_all = np.array(all_features)
    y_all = np.array(all_labels)

    # Shuffle
    indices = np.random.permutation(len(X_all))
    X_all = X_all[indices]
    y_all = y_all[indices]

    return normal_data, X_all, y_all


def main():
    """Generate data and train all models."""
    print("=" * 60)
    print("  StealthVault AI — Training Pipeline")
    print("=" * 60)
    print()

    # Step 1: Generate data
    normal_data, X_all, y_all = generate_training_data()
    print()

    # Step 2: Train anomaly detector
    print("🧠 Training Anomaly Detection Model (Isolation Forest)...")
    anomaly_metrics = anomaly_detector.train(normal_data)
    print(f"  ✅ Trained on {anomaly_metrics['samples_trained']} samples")
    print(f"  📊 Anomaly rate in training: {anomaly_metrics['anomaly_rate']:.2%}")
    print()

    # Step 3: Train attack classifier
    print("🧠 Training Attack Classifier (Random Forest)...")
    classifier_metrics = attack_classifier.train(X_all, y_all)
    print(f"  ✅ Trained on {classifier_metrics['samples_trained']} samples")
    print(f"  📊 Training accuracy: {classifier_metrics['accuracy']:.2%}")
    print(f"  📊 Classes: {classifier_metrics['classes']}")
    print()

    print("=" * 60)
    print("  ✅ ALL MODELS TRAINED SUCCESSFULLY!")
    print(f"  📁 Models saved to: data/models/")
    print("=" * 60)
    print()

    # Step 4: Quick test
    print("🔬 Running quick test...")
    from app.models.alert import NetworkPacket, Protocol

    # Test normal packet
    normal_pkt = NetworkPacket(
        src_ip="192.168.1.10",
        dst_ip="10.0.0.5",
        src_port=54321,
        dst_port=443,
        protocol=Protocol.HTTPS,
        packet_size=1200,
        flags="SA",
        payload_size=800,
        ttl=64,
        duration=0.5,
    )
    features = extractor.extract(normal_pkt)
    feat_np = extractor.to_numpy(features)
    anomaly_result = anomaly_detector.predict(feat_np)
    class_result = attack_classifier.predict(feat_np)
    print(f"  Normal packet → Anomaly: {anomaly_result.is_anomaly} (score: {anomaly_result.anomaly_score})")
    print(f"  Normal packet → Class: {class_result.attack_type.value} (confidence: {class_result.confidence})")

    # Test attack packet
    attack_pkt = NetworkPacket(
        src_ip="10.0.5.100",
        dst_ip="10.0.0.1",
        src_port=12345,
        dst_port=80,
        protocol=Protocol.TCP,
        packet_size=50,
        flags="S",
        payload_size=0,
        ttl=30,
        duration=0.01,
    )
    features = extractor.extract(attack_pkt)
    feat_np = extractor.to_numpy(features)
    anomaly_result = anomaly_detector.predict(feat_np)
    class_result = attack_classifier.predict(feat_np)
    print(f"  Attack packet → Anomaly: {anomaly_result.is_anomaly} (score: {anomaly_result.anomaly_score})")
    print(f"  Attack packet → Class: {class_result.attack_type.value} (confidence: {class_result.confidence})")
    print()
    print("🚀 System ready! Start the server with: python -m uvicorn app.main:app --reload")


if __name__ == "__main__":
    main()
