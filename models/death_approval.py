from sqlalchemy import Column, Integer, ForeignKey, TIMESTAMP, func, Enum, UniqueConstraint
from app.database import Base
from app.models.enums import ApprovalStatus

class DeathApproval(Base):
    __tablename__ = "death_approvals"
    __table_args__ = (
        # One approval record per (declaration, trustee)
        UniqueConstraint("declaration_id", "trustee_id", name="uq_approval_decl_trustee"),
    )

    id = Column(Integer, primary_key=True)
    # Root/owner of the declaration (kept for convenience/filtering)
    user_id = Column(ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    # Which declaration this approval applies to
    declaration_id = Column(ForeignKey("death_declarations.id", ondelete="CASCADE"), index=True, nullable=False)
    # The trustee providing the approval/retraction
    trustee_id = Column(ForeignKey("trustees.id", ondelete="CASCADE"), index=True, nullable=False)
    status = Column(Enum(ApprovalStatus), nullable=False)
    approved_at = Column(TIMESTAMP, server_default=func.now())
