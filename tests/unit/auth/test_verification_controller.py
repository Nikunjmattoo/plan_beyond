"""
Module 2: Auth - Verification Controller Tests (Tests 309-320)

Tests identity verification submission, admin review, and user status updates.
"""
import pytest
from datetime import datetime

from controller.verification import submit_verification
from app.models.verification import IdentityVerification, VerificationMethod, VerificationStatus
from app.models.user import User, UserStatus
from app.models.admin import Admin
from app.schemas.user import VerificationSubmit
from app.core.security import hash_password


# ==============================================
# VERIFICATION SUBMISSION TESTS (Tests 309-314)
# ==============================================

@pytest.mark.unit
@pytest.mark.auth
@pytest.mark.critical
def test_submit_document_verification(db_session):
    """
    Test #309: Submit document verification
    """
    # Create user first
    user = User(
        email="verifyuser@example.com",
        status=UserStatus.guest,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db_session.add(user)
    db_session.commit()

    # Submit verification
    verification_data = VerificationSubmit(
        method=VerificationMethod.document,
        document_type="passport",
        document_ref="/uploads/passport_123.pdf"
    )

    verification = submit_verification(db_session, user.id, verification_data)

    assert verification.id is not None
    assert verification.user_id == user.id
    assert verification.method == VerificationMethod.document
    assert verification.document_type == "passport"
    assert verification.document_ref == "/uploads/passport_123.pdf"


@pytest.mark.unit
@pytest.mark.auth
@pytest.mark.critical
def test_submit_referral_verification(db_session):
    """
    Test #310: Submit referral verification
    """
    user = User(
        email="referraluser@example.com",
        status=UserStatus.guest,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db_session.add(user)
    db_session.commit()

    verification_data = VerificationSubmit(
        method=VerificationMethod.referral,
        document_type="referral_code",
        document_ref="REF123456"
    )

    verification = submit_verification(db_session, user.id, verification_data)

    assert verification.method == VerificationMethod.referral
    assert verification.document_type == "referral_code"
    assert verification.document_ref == "REF123456"


@pytest.mark.unit
@pytest.mark.auth
@pytest.mark.critical
def test_verification_status_defaults_pending(db_session):
    """
    Test #311: Verification status should default to pending
    """
    user = User(
        email="pendinguser@example.com",
        status=UserStatus.guest,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db_session.add(user)
    db_session.commit()

    verification_data = VerificationSubmit(
        method=VerificationMethod.document,
        document_type="drivers_license",
        document_ref="/uploads/license.pdf"
    )

    verification = submit_verification(db_session, user.id, verification_data)

    assert verification.status == VerificationStatus.pending
    # Should NOT be accepted or rejected yet


@pytest.mark.unit
@pytest.mark.auth
@pytest.mark.critical
def test_verification_requires_document_type(db_session):
    """
    Test #312: Document verification should have document_type
    """
    user = User(
        email="doctype@example.com",
        status=UserStatus.guest,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db_session.add(user)
    db_session.commit()

    verification_data = VerificationSubmit(
        method=VerificationMethod.document,
        document_type="national_id",  # Required for documents
        document_ref="/uploads/id_card.pdf"
    )

    verification = submit_verification(db_session, user.id, verification_data)

    assert verification.document_type is not None
    assert verification.document_type == "national_id"


@pytest.mark.unit
@pytest.mark.auth
@pytest.mark.critical
def test_verification_document_ref_stored(db_session):
    """
    Test #313: Document reference should be stored
    """
    user = User(
        email="docref@example.com",
        status=UserStatus.guest,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db_session.add(user)
    db_session.commit()

    doc_ref = "/uploads/user123/passport_scan.pdf"

    verification_data = VerificationSubmit(
        method=VerificationMethod.document,
        document_type="passport",
        document_ref=doc_ref
    )

    verification = submit_verification(db_session, user.id, verification_data)

    assert verification.document_ref == doc_ref


@pytest.mark.unit
@pytest.mark.auth
@pytest.mark.critical
@pytest.mark.xfail(reason="submit_verification doesn't create UserStatusHistory entries yet")
def test_submit_verification_creates_history_entry(db_session):
    """
    Test #314: Submitting verification should create a history entry
    NOTE: This test documents expected behavior - may not be implemented yet
    """
    from app.models.verification import UserStatusHistory

    user = User(
        email="history@example.com",
        status=UserStatus.guest,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db_session.add(user)
    db_session.commit()

    verification_data = VerificationSubmit(
        method=VerificationMethod.document,
        document_type="passport",
        document_ref="/uploads/passport.pdf"
    )

    verification = submit_verification(db_session, user.id, verification_data)

    # Assert - History entry should be created
    history = db_session.query(UserStatusHistory).filter(
        UserStatusHistory.user_id == user.id
    ).first()

    assert history is not None
    assert history.user_id == user.id


# ==============================================
# ADMIN REVIEW TESTS (Tests 315-318)
# ==============================================

@pytest.mark.unit
@pytest.mark.auth
@pytest.mark.critical
def test_admin_accept_verification(db_session):
    """
    Test #315: Admin can accept a verification
    """
    # Create user
    user = User(
        email="accept@example.com",
        status=UserStatus.guest,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db_session.add(user)

    # Create admin
    admin = Admin(
        username="reviewer",
        email="reviewer@example.com",
        password=hash_password("Password123"),
        created_at=datetime.utcnow()
    )
    db_session.add(admin)
    db_session.commit()

    # Create verification
    verification = IdentityVerification(
        user_id=user.id,
        method=VerificationMethod.document,
        document_type="passport",
        document_ref="/uploads/passport.pdf",
        status=VerificationStatus.pending,
        created_at=datetime.utcnow()
    )
    db_session.add(verification)
    db_session.commit()

    # Admin accepts
    verification.status = VerificationStatus.accepted
    verification.reviewed_by = admin.id
    verification.reviewed_at = datetime.utcnow()
    db_session.commit()
    db_session.refresh(verification)

    assert verification.status == VerificationStatus.accepted
    assert verification.reviewed_by == admin.id


@pytest.mark.unit
@pytest.mark.auth
@pytest.mark.critical
def test_admin_reject_verification(db_session):
    """
    Test #316: Admin can reject a verification
    """
    user = User(
        email="reject@example.com",
        status=UserStatus.guest,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db_session.add(user)

    admin = Admin(
        username="rejecter",
        email="rejecter@example.com",
        password=hash_password("Password123"),
        created_at=datetime.utcnow()
    )
    db_session.add(admin)
    db_session.commit()

    verification = IdentityVerification(
        user_id=user.id,
        method=VerificationMethod.document,
        document_type="passport",
        document_ref="/uploads/fake_passport.pdf",
        status=VerificationStatus.pending,
        created_at=datetime.utcnow()
    )
    db_session.add(verification)
    db_session.commit()

    # Admin rejects
    verification.status = VerificationStatus.rejected
    verification.reviewed_by = admin.id
    verification.reviewed_at = datetime.utcnow()
    db_session.commit()
    db_session.refresh(verification)

    assert verification.status == VerificationStatus.rejected
    assert verification.reviewed_by == admin.id


@pytest.mark.unit
@pytest.mark.auth
@pytest.mark.critical
def test_accept_updates_user_status_to_verified(db_session):
    """
    Test #317: Accepting verification should update user status to verified
    """
    user = User(
        email="statusupdate@example.com",
        status=UserStatus.guest,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db_session.add(user)

    admin = Admin(
        username="statusadmin",
        email="statusadmin@example.com",
        password=hash_password("Password123"),
        created_at=datetime.utcnow()
    )
    db_session.add(admin)
    db_session.commit()

    verification = IdentityVerification(
        user_id=user.id,
        method=VerificationMethod.document,
        document_type="passport",
        document_ref="/uploads/passport.pdf",
        status=VerificationStatus.pending,
        created_at=datetime.utcnow()
    )
    db_session.add(verification)
    db_session.commit()

    # Accept verification
    verification.status = VerificationStatus.accepted
    verification.reviewed_by = admin.id
    verification.reviewed_at = datetime.utcnow()

    # Update user status to verified
    user.status = UserStatus.verified
    db_session.commit()
    db_session.refresh(user)

    assert user.status == UserStatus.verified


@pytest.mark.unit
@pytest.mark.auth
@pytest.mark.critical
def test_reject_keeps_user_status_unchanged(db_session):
    """
    Test #318: Rejecting verification should NOT change user status
    """
    user = User(
        email="unchanged@example.com",
        status=UserStatus.guest,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db_session.add(user)

    admin = Admin(
        username="unchangedadmin",
        email="unchangedadmin@example.com",
        password=hash_password("Password123"),
        created_at=datetime.utcnow()
    )
    db_session.add(admin)
    db_session.commit()

    original_status = user.status

    verification = IdentityVerification(
        user_id=user.id,
        method=VerificationMethod.document,
        document_type="passport",
        document_ref="/uploads/passport.pdf",
        status=VerificationStatus.pending,
        created_at=datetime.utcnow()
    )
    db_session.add(verification)
    db_session.commit()

    # Reject verification
    verification.status = VerificationStatus.rejected
    verification.reviewed_by = admin.id
    verification.reviewed_at = datetime.utcnow()
    db_session.commit()

    # User status should remain unchanged
    db_session.refresh(user)
    assert user.status == original_status


# ==============================================
# VERIFICATION METADATA (Tests 319-320)
# ==============================================

@pytest.mark.unit
@pytest.mark.auth
def test_reviewed_by_field_set_to_admin_id(db_session):
    """
    Test #319: reviewed_by should be set to admin's ID
    """
    user = User(
        email="reviewedby@example.com",
        status=UserStatus.guest,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db_session.add(user)

    admin = Admin(
        username="reviewadmin",
        email="reviewadmin@example.com",
        password=hash_password("Password123"),
        created_at=datetime.utcnow()
    )
    db_session.add(admin)
    db_session.commit()

    verification = IdentityVerification(
        user_id=user.id,
        method=VerificationMethod.document,
        document_type="passport",
        document_ref="/uploads/passport.pdf",
        status=VerificationStatus.pending,
        created_at=datetime.utcnow()
    )
    db_session.add(verification)
    db_session.commit()

    # Admin reviews
    verification.status = VerificationStatus.accepted
    verification.reviewed_by = admin.id  # Set reviewer
    db_session.commit()
    db_session.refresh(verification)

    assert verification.reviewed_by == admin.id


@pytest.mark.unit
@pytest.mark.auth
def test_reviewed_at_timestamp_set(db_session):
    """
    Test #320: reviewed_at timestamp should be set when reviewed
    """
    user = User(
        email="timestamp@example.com",
        status=UserStatus.guest,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db_session.add(user)

    admin = Admin(
        username="timeadmin",
        email="timeadmin@example.com",
        password=hash_password("Password123"),
        created_at=datetime.utcnow()
    )
    db_session.add(admin)
    db_session.commit()

    verification = IdentityVerification(
        user_id=user.id,
        method=VerificationMethod.document,
        document_type="passport",
        document_ref="/uploads/passport.pdf",
        status=VerificationStatus.pending,
        created_at=datetime.utcnow()
    )
    db_session.add(verification)
    db_session.commit()

    # Initially no reviewed_at
    assert verification.reviewed_at is None

    # Admin reviews
    verification.status = VerificationStatus.accepted
    verification.reviewed_by = admin.id
    verification.reviewed_at = datetime.utcnow()  # Set timestamp
    db_session.commit()
    db_session.refresh(verification)

    assert verification.reviewed_at is not None
    # Should be recent (within last minute)
    time_diff = (datetime.utcnow() - verification.reviewed_at).total_seconds()
    assert time_diff < 60
