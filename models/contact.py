# app/models/contact.py
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, JSON, DateTime
from sqlalchemy.orm import relationship
from app.database import Base
from datetime import datetime

class Contact(Base):
    __tablename__ = "contacts"

    id = Column(Integer, primary_key=True)

    # Foreign keys
    owner_user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    linked_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    # Personal Information
    title = Column(String(50), default="")                 # ← NEW
    first_name = Column(String(255))
    middle_name = Column(String(255), default="")
    last_name = Column(String(255), default="")
    local_name = Column(String(255), default="")
    company = Column(String(255), default="")
    job_type = Column(String(255), default="")
    website = Column(String(255), default="")
    category = Column(String(255), default="")
    relation = Column(String(100), default="")

    # Contact Information
    phone_numbers = Column(JSON)
    whatsapp_numbers = Column(JSON)
    emails = Column(JSON)

    # Address Information
    flat_building_no = Column(String(255), default="")
    street = Column(String, default=None)
    city = Column(String(100), default="")
    state = Column(String(100), default="")
    country = Column(String(100), default="")
    postal_code = Column(String(20), default="")

    # Additional Information
    date_of_birth = Column(String(10), default="")
    anniversary = Column(String(10), default="")
    notes = Column(String, default=None)
    contact_image = Column(String(255), default="")

    # UI Preference Flags
    share_by_whatsapp = Column(Boolean, default=False)
    share_by_sms = Column(Boolean, default=False)
    share_by_email = Column(Boolean, default=False)
    share_after_death = Column(Boolean, default=True)  # stored field
    is_emergency_contact = Column(Boolean, default=False)  # stored field

    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    owner_user = relationship(
        "User",
        back_populates="contacts",
        foreign_keys=[owner_user_id]
    )
    linked_user = relationship(
        "User",
        foreign_keys=[linked_user_id]
    )
