from sqlalchemy import Column, Date, Integer, String, Enum, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base
import enum
from datetime import datetime

class UserStatus(enum.Enum):
    unknown = "unknown"
    guest = "guest"
    verified = "verified"
    member = "member"

class User(Base):
    __tablename__ = "users"

    # --- Identity/Auth & Meta ONLY ---
    id = Column(Integer, primary_key=True)
    display_name = Column(String, nullable=True)
    email = Column(String, unique=True, index=True, nullable=True)
    country_code = Column(String, nullable=True)
    phone = Column(String, unique=True, index=True, nullable=True)
    password = Column(String, nullable=True)
    status = Column(Enum(UserStatus), default=UserStatus.unknown, nullable=False)
    communication_channel = Column(String, nullable=True)
    otp = Column(String, nullable=True)
    otp_expires_at = Column(DateTime, nullable=True)
    otp_verified = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # --- 1–1 Profile relation (moved fields to UserProfile) ---
    profile = relationship(
        "UserProfile",
        uselist=False,
        back_populates="user",
        cascade="all, delete-orphan"
    )

    # --- Existing relationships (unchanged) ---
    contacts = relationship(
        "Contact",
        back_populates="owner_user",
        cascade="all, delete-orphan",
        foreign_keys="[Contact.owner_user_id]"
    )
    files = relationship("File", back_populates="user", cascade="all, delete-orphan")
    verifications = relationship("IdentityVerification", back_populates="user")
    status_history = relationship("UserStatusHistory", back_populates="user")
    
    # --- NEW: Reminder relationships ---
    reminders = relationship("Reminder", back_populates="user", cascade="all, delete-orphan")
    reminder_preference = relationship("ReminderPreference", uselist=False, back_populates="user", cascade="all, delete-orphan")

    # Roles property (left as-is; assumes a 'role' column exists elsewhere)
    @property
    def roles(self):
        """Return roles as a list."""
        return self.role.split(",") if self.role else []

    @roles.setter
    def roles(self, roles):
        """Set roles as a comma-separated string."""
        if isinstance(roles, list):
            self.role = ",".join(roles)
        else:
            self.role = roles


class UserProfile(Base):
    __tablename__ = "user_profiles"

    # Primary key is also the FK to users.id to enforce 1–1
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)

    # --- Profile fields moved from users ---
    title = Column(String, nullable=True)
    first_name = Column(String, nullable=True)
    middle_name = Column(String, nullable=True)
    last_name = Column(String, nullable=True)
    date_of_birth = Column(Date, nullable=True)
    anniversary = Column(Date, nullable=True)
    gender = Column(String, nullable=True)
    address_line_1 = Column(String, nullable=True)
    address_line_2 = Column(String, nullable=True)
    city = Column(String, nullable=True)
    state = Column(String, nullable=True)
    zip_code = Column(String, nullable=True)
    country = Column(String, nullable=True)
    profile_image = Column(String, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # backref to User
    user = relationship("User", back_populates="profile")