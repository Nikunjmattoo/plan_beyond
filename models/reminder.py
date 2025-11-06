# app/models/reminder.py
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime, Date, Text
from sqlalchemy.orm import relationship
from app.database import Base
from datetime import datetime
import uuid
from sqlalchemy.dialects.postgresql import UUID

class Reminder(Base):
    __tablename__ = "reminders"
    
    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Foreign Keys
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    vault_file_id = Column(String(64), ForeignKey("vault_files.file_id", ondelete="CASCADE"), index=True, nullable=False)
    
    # Reminder Context
    field_name = Column(String(100), nullable=False)
    reminder_category = Column(String(50), nullable=False)
    
    # Dates
    trigger_date = Column(Date, nullable=False)
    reminder_date = Column(Date, nullable=False)
    
    # Content
    title = Column(String(200), nullable=False)
    message = Column(Text, nullable=False)
    urgency_level = Column(String(20), nullable=False)
    
    # Status
    status = Column(String(20), nullable=False, default='pending')
    
    # Multi-Channel Delivery Tracking
    in_app_sent = Column(Boolean, nullable=False, default=False)
    in_app_sent_at = Column(DateTime, nullable=True)
    
    email_sent = Column(Boolean, nullable=False, default=False)
    email_sent_at = Column(DateTime, nullable=True)
    email_opened = Column(Boolean, nullable=False, default=False)
    email_clicked = Column(Boolean, nullable=False, default=False)
    
    sms_sent = Column(Boolean, nullable=False, default=False)
    sms_sent_at = Column(DateTime, nullable=True)
    
    push_sent = Column(Boolean, nullable=False, default=False)
    push_sent_at = Column(DateTime, nullable=True)
    push_opened = Column(Boolean, nullable=False, default=False)
    
    # User Action Tracking
    acknowledged_at = Column(DateTime, nullable=True)
    acknowledged_by = Column(String(20), nullable=True)
    
    completed_at = Column(DateTime, nullable=True)
    completion_action = Column(String(50), nullable=True)
    
    dismissed_at = Column(DateTime, nullable=True)
    
    snoozed_at = Column(DateTime, nullable=True)
    snoozed_until = Column(DateTime, nullable=True)
    snooze_count = Column(Integer, nullable=False, default=0)
    
    # Escalation
    escalation_level = Column(Integer, nullable=False, default=0)
    last_escalated_at = Column(DateTime, nullable=True)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="reminders", foreign_keys=[user_id])
    vault_file = relationship("app.models.vault.VaultFile", foreign_keys=[vault_file_id])  # ← FIXED THIS LINE