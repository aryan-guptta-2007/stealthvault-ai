"""
StealthVault AI - Data Models
Pydantic schemas for network packets, threats, and alerts.
"""

from pydantic import BaseModel, Field, IPvAnyAddress, conint, constr
from typing import Optional
from datetime import datetime
from enum import Enum
import uuid


class SafeConfig:
    """🛡️ MISSION-CRITICAL: Prevent hidden payload injection."""
    extra = "forbid"
    validate_assignment = True
    str_strip_whitespace = True


class AttackType(str, Enum):
    """Known attack categories."""
    NORMAL = "Normal"
    DDOS = "DDoS"
    PORT_SCAN = "PortScan"
    BRUTE_FORCE = "BruteForce"
    MALWARE = "Malware"
    SQL_INJECTION = "SQLInjection"
    XSS = "XSS"
    UNKNOWN = "Unknown"


class Severity(str, Enum):
    """Threat severity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class Protocol(str, Enum):
    """Network protocols."""
    TCP = "TCP"
    UDP = "UDP"
    ICMP = "ICMP"
    HTTP = "HTTP"
    HTTPS = "HTTPS"
    DNS = "DNS"
    SSH = "SSH"
    FTP = "FTP"
    OTHER = "OTHER"


class NetworkPacket(BaseModel):
    """
    🛡️ Hardened Network Packet Schema
    Enforces strict IP and Port validation to prevent injection.
    """
    id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8], min_length=8, max_length=8)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    tenant_id: str = Field("default", min_length=1, max_length=50)
    src_ip: IPvAnyAddress = Field(..., description="The source IP address of the packet")
    dst_ip: IPvAnyAddress = Field(..., description="The destination IP address of the packet")
    src_port: int = Field(0, ge=0, le=65535)
    dst_port: int = Field(0, ge=0, le=65535)
    protocol: Protocol = Protocol.TCP
    packet_size: int = Field(0, ge=0)
    flags: str = Field("", max_length=20)
    payload_size: int = Field(0, ge=0)
    ttl: int = Field(64, ge=0, le=255)
    duration: float = Field(0.0, ge=0.0)

    class Config(SafeConfig):
        pass


class FeatureVector(BaseModel):
    """Extracted features from a packet for AI processing."""
    src_port: float
    dst_port: float
    packet_size: float
    payload_size: float
    ttl: float
    duration: float
    protocol_tcp: float = 0.0
    protocol_udp: float = 0.0
    protocol_icmp: float = 0.0
    protocol_http: float = 0.0
    flag_syn: float = 0.0
    flag_ack: float = 0.0
    flag_fin: float = 0.0
    flag_rst: float = 0.0
    flag_psh: float = 0.0

    class Config(SafeConfig):
        pass


class AnomalyResult(BaseModel):
    is_anomaly: bool
    anomaly_score: float = Field(ge=0.0, le=1.0)
    confidence: float = Field(ge=0.0, le=1.0)
    explanation: Optional[str] = Field(None, max_length=500)
    
    class Config(SafeConfig):
        pass


class ClassificationResult(BaseModel):
    attack_type: AttackType
    confidence: float = Field(ge=0.0, le=1.0)
    explanation: Optional[str] = Field(None, max_length=500)
    
    class Config(SafeConfig):
        pass


class RiskScore(BaseModel):
    score: float = Field(ge=0.0, le=1.0)
    severity: Severity

    class Config(SafeConfig):
        pass


class BrainAnalysis(BaseModel):
    attack_name: str = Field(..., max_length=100)
    description: str = Field(..., max_length=500)
    recommended_actions: list[str] = []

    class Config(SafeConfig):
        pass


class GeoLocation(BaseModel):
    """Geographic information for an IP address."""
    city: str = "Unknown"
    country: str = "Unknown"
    country_code: str = "XX"
    latitude: float = 0.0
    longitude: float = 0.0

    class Config(SafeConfig):
        pass


class ThreatAlert(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4())[:12])
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    attack_type: str = Field("Unknown", max_length=50)
    packet: NetworkPacket
    anomaly: AnomalyResult
    classification: ClassificationResult
    risk: RiskScore
    brain_analysis: Optional[BrainAnalysis] = None

    class Config(SafeConfig):
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class DashboardStats(BaseModel):
    """Aggregated statistics for the dashboard."""
    total_packets_analyzed: int = 0
    total_alerts: int = 0
    critical_alerts: int = 0
    high_alerts: int = 0
    medium_alerts: int = 0
    low_alerts: int = 0
    attack_distribution: dict[str, int] = {}
    avg_risk_score: float = 0.0
    top_attackers: list[dict] = []
    packets_per_minute: float = 0.0
    system_status: str = "ACTIVE"

    class Config(SafeConfig):
        pass


class SimulationInput(BaseModel):
    attack_type: str = Field("ddos", pattern="^(ddos|bruteforce|portscan|malware|sqlinjection|xss)$")
    intensity: str = Field("medium", pattern="^(low|medium|high)$")

    class Config(SafeConfig):
        pass


class RegisterInput(BaseModel):
    tenant_name: str = Field(..., min_length=3, max_length=50)
    username: str = Field(..., min_length=4, max_length=32)
    password: str = Field(..., min_length=8, max_length=128)
    email: Optional[str] = Field(None, max_length=100)
    plan: str = Field("FREE", pattern="^(FREE|PRO|ENTERPRISE)$")

    class Config(SafeConfig):
        pass
