# app/models/reminder_preference.py
from sqlalchemy import Column, Integer, Boolean, ForeignKey, Time, String, DateTime
from sqlalchemy.orm import relationship
from app.database import Base
from datetime import datetime, time

class ReminderPreference(Base):
    __tablename__ = "reminder_preferences"
    
    # Primary Key
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    
    # Expiry Preferences
    expiry_in_app = Column(Boolean, nullable=False, default=True)
    expiry_email = Column(Boolean, nullable=False, default=True)
    expiry_sms = Column(Boolean, nullable=False, default=True)
    expiry_push = Column(Boolean, nullable=False, default=True)
    
    # Renewal Preferences
    renewal_in_app = Column(Boolean, nullable=False, default=True)
    renewal_email = Column(Boolean, nullable=False, default=True)
    renewal_sms = Column(Boolean, nullable=False, default=False)
    renewal_push = Column(Boolean, nullable=False, default=True)
    
    # Maturity Preferences
    maturity_in_app = Column(Boolean, nullable=False, default=True)
    maturity_email = Column(Boolean, nullable=False, default=True)
    maturity_sms = Column(Boolean, nullable=False, default=False)
    maturity_push = Column(Boolean, nullable=False, default=True)
    
    # Recurring Payment Preferences
    recurring_payment_in_app = Column(Boolean, nullable=False, default=True)
    recurring_payment_email = Column(Boolean, nullable=False, default=True)
    recurring_payment_sms = Column(Boolean, nullable=False, default=True)
    recurring_payment_push = Column(Boolean, nullable=False, default=True)
    
    # Health Preferences
    health_in_app = Column(Boolean, nullable=False, default=True)
    health_email = Column(Boolean, nullable=False, default=True)
    health_sms = Column(Boolean, nullable=False, default=False)
    health_push = Column(Boolean, nullable=False, default=True)
    
    # Custom Preferences (ADDED)
    custom_in_app = Column(Boolean, nullable=False, default=True)
    custom_email = Column(Boolean, nullable=False, default=True)
    custom_sms = Column(Boolean, nullable=False, default=False)
    custom_push = Column(Boolean, nullable=False, default=False)
    
    # Timing Preferences
    preferred_time = Column(Time, nullable=False, default=time(9, 0, 0))
    timezone = Column(String(50), nullable=False, default='Asia/Kolkata')
    
    # Quiet Hours
    quiet_hours_start = Column(Time, nullable=False, default=time(22, 0, 0))
    quiet_hours_end = Column(Time, nullable=False, default=time(7, 0, 0))
    
    # Advanced Settings
    group_similar_reminders = Column(Boolean, nullable=False, default=True)
    reduce_auto_pay_frequency = Column(Boolean, nullable=False, default=True)
    send_daily_digest = Column(Boolean, nullable=False, default=False)  # ADDED
    send_weekly_summary = Column(Boolean, nullable=False, default=False)
    remind_missing_info = Column(Boolean, nullable=False, default=True)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="reminder_preference", foreign_keys=[user_id])