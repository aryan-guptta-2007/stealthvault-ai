import uuid
from datetime import datetime
from sqlalchemy import Column, String, Float, DateTime, Boolean, JSON, Integer, ForeignKey, Index
from sqlalchemy.orm import relationship
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from app.database import Base

class DBTenant(Base):
    __tablename__ = "tenants"
    
    id = Column(String(36), primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(100), unique=True, index=True)
    api_key = Column(String(64), unique=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 💰 SaaS Business Layer
    plan = Column(String(20), default="FREE") # FREE, PRO, ENTERPRISE
    is_active = Column(Boolean, default=True)
    monthly_packet_limit = Column(Integer, default=100000)
    current_usage_count = Column(Integer, default=0)
    last_billing_reset = Column(DateTime, default=datetime.utcnow)
    
    users = relationship("DBUser", back_populates="tenant", cascade="all, delete-orphan")
    alerts = relationship("DBAlert", back_populates="tenant", cascade="all, delete-orphan")
    inspections = relationship("DBInspectionLog", back_populates="tenant", cascade="all, delete-orphan")
    system_events = relationship("DBSystemEvent", back_populates="tenant", cascade="all, delete-orphan")

class DBUser(Base):
    __tablename__ = "users"
    
    id = Column(String(36), primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(String(36), ForeignKey("tenants.id"), index=True)
    username = Column(String(50), unique=True, index=True)
    email = Column(String(100), unique=True, index=True, nullable=True) # Optional for now
    password_hash = Column(String(255))
    roles = Column(JSON) # e.g., ["admin", "soc_analyst"]
    is_verified = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    tenant = relationship("DBTenant", back_populates="users")

class DBAlert(Base):
    __tablename__ = "alerts"
    __table_args__ = (
        Index("idx_alerts_tenant_severity_ts", "tenant_id", "severity", "timestamp"),
        Index("idx_alerts_tenant_ts", "tenant_id", "timestamp"),
    )

    id = Column(String(36), primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(String(36), ForeignKey("tenants.id"), index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    src_ip = Column(String(50), index=True)
    dst_ip = Column(String(50))
    attack_type = Column(String(50), index=True)
    risk_score = Column(Float)
    severity = Column(String(20), index=True)
    
    packet_data = Column(JSON)
    anomaly_data = Column(JSON)
    classification_data = Column(JSON)
    risk_data = Column(JSON)
    brain_analysis = Column(JSON, nullable=True)
    
    # 📉 Monitoring & Feedback
    feedback_label = Column(String(50), nullable=True) # Actual label from analyst
    is_correct = Column(Boolean, nullable=True) # Was the model right?
    
    tenant = relationship("DBTenant", back_populates="alerts")

class DBAttackStory(Base):
    __tablename__ = "attack_stories"

    # Composite primary key: IP + Tenant
    attacker_ip = Column(String(50), primary_key=True, index=True)
    tenant_id = Column(String(36), ForeignKey("tenants.id"), index=True, primary_key=True)
    target_ip = Column(String(50), nullable=True) # Optional secondary target field
    
    start_time = Column(DateTime, default=datetime.utcnow)
    last_update = Column(DateTime, default=datetime.utcnow)
    status = Column(String(20), default="active") # active, closed
    
    current_phase = Column(String(100))
    predicted_next_phase = Column(String(100))
    confidence = Column(Float)
    
    events = Column(JSON) # List of alert IDs or simplified event dicts
    defense_actions = Column(JSON) # List of actions taken
    
    # Audit Trail Link
    audit_story_data = Column(JSON, nullable=True) # Full structured story snapshot

class DBInspectionLog(Base):
    """
    🔬 THE FULL AUDIT TRAIL
    Logs every packet analyzed by the system, threat or not.
    """
    __tablename__ = "inspection_logs"
    __table_args__ = (
        Index("idx_inspections_tenant_ts_ip", "tenant_id", "timestamp", "src_ip"),
        Index("idx_inspections_threat_only", "is_threat"), # Partial index would be better, but this helps
    )
    
    id = Column(String(36), primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(String(36), ForeignKey("tenants.id"), index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    
    # Network Layer
    src_ip = Column(String(50), index=True)
    dst_ip = Column(String(50))
    src_port = Column(Integer)
    dst_port = Column(Integer)
    protocol = Column(String(10))
    
    # Decision Layer
    risk_score = Column(Float, index=True)
    is_threat = Column(Boolean, index=True, default=False)
    attack_type = Column(String(50))
    processing_time_ms = Column(Float)
    
    # Full AI context for debugging
    features = Column(JSON, nullable=True) # Normalized data used by models
    decision_details = Column(JSON) # JSON dump of Anomaly + Classification + Risk data
    
    tenant = relationship("DBTenant", back_populates="inspections")

class DBIPReputation(Base):
    """
    📈 LONG-TERM IP BEHAVIOR
    Stores historical reputation and risk trajectory for an IP.
    """
    __tablename__ = "ip_reputation"
    
    ip_address = Column(String(50), primary_key=True, index=True)
    tenant_id = Column(String(36), ForeignKey("tenants.id"), index=True, primary_key=True)
    
    reputation_score = Column(Float, default=0.0) # 0.0 to 1.0 (malicious)
    total_inspections = Column(Integer, default=0)
    total_alerts = Column(Integer, default=0)
    
    first_seen = Column(DateTime, default=datetime.utcnow)
    last_seen = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    behavior_profile = Column(JSON, nullable=True) # Frequency, common ports, etc.

class DBSystemEvent(Base):
    """
    🩺 THE GOD VIEW: Internal SOC Logging
    Records all non-alert system events like worker status, database reconnects, etc.
    """
    __tablename__ = "system_events"
    __table_args__ = (
        Index("idx_sys_events_tenant_level_ts", "tenant_id", "level", "timestamp"),
    )
    
    id = Column(String(36), primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(String(36), ForeignKey("tenants.id"), index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    
    # Severity & Component
    level = Column(String(20), index=True) # INFO, WARNING, ERROR, CRITICAL
    component = Column(String(50), index=True) # Collector, Worker, DB, etc.
    message = Column(String(500))
    stack_trace = Column(String(2000), nullable=True)
    metadata_json = Column(JSON, nullable=True)
    
    tenant = relationship("DBTenant", back_populates="system_events")


class DBBlockedIP(Base):
    __tablename__ = "blocked_ips"
    
    ip_address = Column(String(50), primary_key=True, index=True)
    tenant_id = Column(String(36), ForeignKey("tenants.id"), index=True, primary_key=True)
    block_timestamp = Column(DateTime, default=datetime.utcnow)
    reason = Column(String(500))
    auto_blocked = Column(Boolean, default=True)
    expires_at = Column(DateTime, nullable=True)
    
    # 🧠 Neural Auditing
    risk_score = Column(Float, nullable=True)
    confidence = Column(Float, nullable=True)
    attack_type = Column(String(50), nullable=True)


class DBModelMetric(Base):
    """
    📉 MODEL PERFORMANCE MONITORING
    Tracks the health and accuracy of each model version over time.
    """
    __tablename__ = "model_metrics"
    
    version = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    # Core Metrics
    accuracy = Column(Float)
    precision = Column(Float)
    recall = Column(Float)
    f1_score = Column(Float)
    
    # Metadata
    total_samples = Column(Integer)
    false_positives_count = Column(Integer)
    training_duration_s = Column(Float)


class DBSystemMetric(Base):
    """
    📈 PERFORMANCE TRENDS
    Persistent snapshots of system health and throughput.
    Used for historical graphing in the production dashboard.
    """
    __tablename__ = "system_metrics"
    
    id = Column(String(36), primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    
    # Host Infrastructure
    cpu_usage = Column(Float)
    ram_usage = Column(Float)
    disk_usage = Column(Float)
    
    # Application Layer
    active_workers = Column(Integer)
    queue_size = Column(Integer)
    packets_per_second = Column(Float)
    avg_latency_ms = Column(Float)
    dropped_packets = Column(Integer)


class DBAuditLog(Base):
    """
    📜 THE OVERWATCH: Forensic Audit Trail
    Records all sensitive user and system actions.
    Crucial for SOC compliance and internal security audits.
    """
    __tablename__ = "audit_logs"
    __table_args__ = (
        Index("idx_audit_tenant_action_ts", "tenant_id", "action", "timestamp"),
    )
    
    id = Column(String(36), primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    
    # Who
    user_id = Column(String(36), ForeignKey("users.id"), nullable=True) # None for system-level actions
    username = Column(String(50), index=True)
    tenant_id = Column(String(36), ForeignKey("tenants.id"), index=True)
    
    # What
    action = Column(String(100), index=True) # e.g. LOGIN, RETRAIN_MODEL, BLOCK_IP
    target = Column(String(100), index=True) # The affected resource ID or IP
    result = Column(String(20)) # SUCCESS, FAILURE, DENIED
    
    # Context
    metadata_json = Column(JSON, nullable=True) # Original request ID, Source IP, Browser, etc.
    message = Column(String(500))
