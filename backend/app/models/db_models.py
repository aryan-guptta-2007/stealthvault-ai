import uuid
from datetime import datetime
from sqlalchemy import Column, String, Float, DateTime, Boolean, JSON, Integer, ForeignKey
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
    
    users = relationship("DBUser", back_populates="tenant", cascade="all, delete-orphan")
    alerts = relationship("DBAlert", back_populates="tenant", cascade="all, delete-orphan")
    inspections = relationship("DBInspectionLog", back_populates="tenant", cascade="all, delete-orphan")
    system_events = relationship("DBSystemEvent", back_populates="tenant", cascade="all, delete-orphan")

class DBUser(Base):
    __tablename__ = "users"
    
    id = Column(String(36), primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(String(36), ForeignKey("tenants.id"), index=True)
    username = Column(String(50), unique=True, index=True)
    password_hash = Column(String(255))
    roles = Column(JSON) # e.g., ["admin", "soc_analyst"]
    created_at = Column(DateTime, default=datetime.utcnow)
    
    tenant = relationship("DBTenant", back_populates="users")

class DBAlert(Base):
    __tablename__ = "alerts"

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
