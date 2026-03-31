import numpy as np
import os
import sys

# Ensure backend directory is in path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.ai_engine.anomaly import anomaly_detector
from app.config import settings

def generate_normal_data(n_samples=5000):
    """
    Generates synthetic 'Normal' traffic features to train the baseline ML model.
    Feature order matches extractor.py:
    [src_port, dst_port, p_size, py_size, ttl, dur, tcp, udp, icmp, http, syn, ack, fin, rst, psh]
    """
    print(f"Generating {n_samples} normal traffic samples...")
    
    # 1. Source Port (mostly high ports)
    src_ports = np.random.uniform(0.1, 1.0, n_samples)
    
    # 2. Destination Port (mostly 80/443 -> small normalized values)
    # Port 80 = 80/65535 = 0.0012
    # Port 443 = 443/65535 = 0.0067
    dst_ports = np.random.choice([0.0012, 0.0067, 0.1, 0.5], n_samples, p=[0.4, 0.4, 0.1, 0.1])
    
    # 3. Packet Size (Normal: 60 - 1000 bytes)
    # Range is 0-65535. 1000/65535 = 0.015
    packet_sizes = np.random.uniform(0.001, 0.015, n_samples)
    
    # 4. Payload Size (Normal: < Packet Size)
    payload_sizes = packet_sizes * np.random.uniform(0.5, 0.9, n_samples)
    
    # 5. TTL (Normal: ~64 or ~128)
    # 64/255 = 0.25, 128/255 = 0.5
    ttls = np.random.choice([0.25, 0.5], n_samples, p=[0.7, 0.3])
    
    # 6. Duration (Normal: small 0-1s)
    # 1/300 = 0.0033
    durations = np.random.uniform(0.0, 0.0033, n_samples)
    
    # 7-10. Protocols (TCP=1.0, Others=0.0)
    protocol_tcp = np.ones(n_samples)
    protocol_udp = np.zeros(n_samples)
    protocol_icmp = np.zeros(n_samples)
    protocol_http = np.random.choice([1.0, 0.0], n_samples, p=[0.8, 0.2])
    
    # 11-15. TCP Flags (Mostly ACK=1, Others=0)
    flag_syn = np.random.choice([0.0, 1.0], n_samples, p=[0.98, 0.02])
    flag_ack = np.ones(n_samples)
    flag_fin = np.zeros(n_samples)
    flag_rst = np.zeros(n_samples)
    flag_psh = np.random.choice([0.0, 1.0], n_samples, p=[0.7, 0.3])
    
    data = np.column_stack([
        src_ports, dst_ports, packet_sizes, payload_sizes, ttls, durations,
        protocol_tcp, protocol_udp, protocol_icmp, protocol_http,
        flag_syn, flag_ack, flag_fin, flag_rst, flag_psh
    ])
    
    return data

def main():
    # Ensure models dir exists
    os.makedirs(settings.MODELS_DIR, exist_ok=True)
    
    # Generate data
    X = generate_normal_data(10000)
    
    # Train
    print("Training Isolation Forest ML model...")
    metrics = anomaly_detector.train(X)
    
    print("\n✅ Training Complete!")
    print(f"   Model Version: {metrics['samples_trained']} samples")
    print(f"   Anomalies detected in baseline: {metrics['anomalies_in_training']} ({metrics['anomaly_rate']:.2%})")
    print(f"   Average Anomaly Score: {metrics['avg_score']:.4f}")
    print(f"   Model Saved To: {settings.MODELS_DIR}")

if __name__ == "__main__":
    main()
