from sqlalchemy import Boolean, Column, Integer, String, Text, TIMESTAMP, ForeignKey, func
from sqlalchemy.orm import relationship
from app.database import Base

class File(Base):
    __tablename__ = "files"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    folder_id = Column(Integer, ForeignKey("folders.id", ondelete="CASCADE"), nullable=True)
    name = Column(Text, nullable=False)
    storage_ref = Column(Text, nullable=False)  # path or object storage key
    hash_sha256 = Column(String(64), nullable=False)
    size = Column(Integer, nullable=False)
    mime_type = Column(String, nullable=False)
    is_deleted = Column(Boolean, default=False)
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

    user = relationship("User", back_populates="files")
    folder = relationship("Folder", back_populates="files")
