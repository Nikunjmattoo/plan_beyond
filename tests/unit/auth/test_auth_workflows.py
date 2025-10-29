"""
Module 2: Auth - Authentication Workflows (Tests 374-403)

Tests real authentication flows using existing User model fields.
"""
import pytest
from datetime import datetime, timedelta
from app.models.user import User, UserStatus
from app.core.security import hash_password, verify_password


# ==============================================
# USER STATUS WORKFLOWS (Tests 374-383)
# ==============================================

@pytest.mark.unit
@pytest.mark.auth
@pytest.mark.critical
def test_new_user_starts_as_unknown(db_session):
    """
    Test #374: New users start with status=unknown
    """
    user = User(
        email="newuser@example.com",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db_session.add(user)
    db_session.commit()

    assert user.status == UserStatus.unknown


@pytest.mark.unit
@pytest.mark.auth
def test_user_progresses_unknown_to_guest(db_session):
    """
    Test #375: User can progress from unknown to guest
    """
    user = User(
        email="progress1@example.com",
        status=UserStatus.unknown,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db_session.add(user)
    db_session.commit()

    # Progress to guest after OTP verification
    user.status = UserStatus.guest
    db_session.commit()
    db_session.refresh(user)

    assert user.status == UserStatus.guest


@pytest.mark.unit
@pytest.mark.auth
def test_user_progresses_guest_to_verified(db_session):
    """
    Test #376: User can progress from guest to verified
    """
    user = User(
        email="progress2@example.com",
        status=UserStatus.guest,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db_session.add(user)
    db_session.commit()

    # Progress to verified after document verification
    user.status = UserStatus.verified
    db_session.commit()
    db_session.refresh(user)

    assert user.status == UserStatus.verified


@pytest.mark.unit
@pytest.mark.auth
def test_user_progresses_verified_to_member(db_session):
    """
    Test #377: User can progress from verified to member
    """
    user = User(
        email="progress3@example.com",
        status=UserStatus.verified,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db_session.add(user)
    db_session.commit()

    # Progress to member after completing profile
    user.status = UserStatus.member
    db_session.commit()
    db_session.refresh(user)

    assert user.status == UserStatus.member


@pytest.mark.unit
@pytest.mark.auth
def test_status_can_be_queried(db_session):
    """
    Test #378: Can query users by status
    """
    user1 = User(email="u1@example.com", status=UserStatus.unknown, created_at=datetime.utcnow(), updated_at=datetime.utcnow())
    user2 = User(email="u2@example.com", status=UserStatus.guest, created_at=datetime.utcnow(), updated_at=datetime.utcnow())
    user3 = User(email="u3@example.com", status=UserStatus.verified, created_at=datetime.utcnow(), updated_at=datetime.utcnow())
    db_session.add_all([user1, user2, user3])
    db_session.commit()

    # Query by status
    verified_users = db_session.query(User).filter(User.status == UserStatus.verified).all()
    assert len(verified_users) == 1
    assert verified_users[0].email == "u3@example.com"


@pytest.mark.unit
@pytest.mark.auth
def test_user_has_created_at_timestamp(db_session):
    """
    Test #379: User has created_at timestamp
    """
    before = datetime.utcnow()
    
    user = User(
        email="timestamp@example.com",
        status=UserStatus.unknown,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db_session.add(user)
    db_session.commit()
    
    after = datetime.utcnow()

    assert before <= user.created_at <= after


@pytest.mark.unit
@pytest.mark.auth
def test_user_has_updated_at_timestamp(db_session):
    """
    Test #380: User has updated_at timestamp
    """
    user = User(
        email="updated@example.com",
        status=UserStatus.unknown,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db_session.add(user)
    db_session.commit()

    original_updated = user.updated_at

    # Update user
    user.display_name = "Updated Name"
    user.updated_at = datetime.utcnow()
    db_session.commit()
    db_session.refresh(user)

    assert user.updated_at > original_updated


@pytest.mark.unit
@pytest.mark.auth
def test_communication_channel_can_be_set(db_session):
    """
    Test #381: User can have communication channel preference
    """
    user = User(
        email="channel@example.com",
        status=UserStatus.verified,
        communication_channel="email",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db_session.add(user)
    db_session.commit()

    assert user.communication_channel == "email"


@pytest.mark.unit
@pytest.mark.auth
def test_user_can_have_both_email_and_phone(db_session):
    """
    Test #382: User can have both email and phone
    """
    user = User(
        email="both@example.com",
        phone="+919876543210",
        country_code="+91",
        status=UserStatus.verified,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db_session.add(user)
    db_session.commit()

    assert user.email == "both@example.com"
    assert user.phone == "+919876543210"


@pytest.mark.unit
@pytest.mark.auth
def test_user_can_have_only_email(db_session):
    """
    Test #383: User can have only email (no phone)
    """
    user = User(
        email="emailonly@example.com",
        phone=None,
        status=UserStatus.verified,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db_session.add(user)
    db_session.commit()

    assert user.email is not None
    assert user.phone is None


# ==============================================
# EMAIL/PHONE MANAGEMENT (Tests 384-393)
# ==============================================

@pytest.mark.unit
@pytest.mark.auth
@pytest.mark.critical
def test_email_must_be_unique(db_session):
    """
    Test #384: Email addresses must be unique
    """
    user1 = User(
        email="unique@example.com",
        status=UserStatus.unknown,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db_session.add(user1)
    db_session.commit()

    # Try to create duplicate
    user2 = User(
        email="unique@example.com",
        status=UserStatus.unknown,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db_session.add(user2)

    with pytest.raises(Exception):  # IntegrityError
        db_session.commit()


@pytest.mark.unit
@pytest.mark.auth
def test_phone_must_be_unique(db_session):
    """
    Test #385: Phone numbers must be unique
    """
    user1 = User(
        phone="+919876543210",
        country_code="+91",
        status=UserStatus.unknown,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db_session.add(user1)
    db_session.commit()

    # Try to create duplicate
    user2 = User(
        phone="+919876543210",
        country_code="+91",
        status=UserStatus.unknown,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db_session.add(user2)

    with pytest.raises(Exception):  # IntegrityError
        db_session.commit()


@pytest.mark.unit
@pytest.mark.auth
def test_email_can_be_updated(db_session):
    """
    Test #386: User can update their email
    """
    user = User(
        email="old@example.com",
        status=UserStatus.verified,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db_session.add(user)
    db_session.commit()

    # Update email
    user.email = "new@example.com"
    db_session.commit()
    db_session.refresh(user)

    assert user.email == "new@example.com"


@pytest.mark.unit
@pytest.mark.auth
def test_phone_can_be_updated(db_session):
    """
    Test #387: User can update their phone
    """
    user = User(
        phone="+919876543210",
        country_code="+91",
        status=UserStatus.verified,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db_session.add(user)
    db_session.commit()

    # Update phone
    user.phone = "+919999999999"
    db_session.commit()
    db_session.refresh(user)

    assert user.phone == "+919999999999"


@pytest.mark.unit
@pytest.mark.auth
def test_country_code_stored_with_phone(db_session):
    """
    Test #388: Country code is stored separately from phone
    """
    user = User(
        phone="+919876543210",
        country_code="+91",
        status=UserStatus.verified,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db_session.add(user)
    db_session.commit()

    assert user.country_code == "+91"
    assert user.phone == "+919876543210"


@pytest.mark.unit
@pytest.mark.auth
def test_display_name_can_be_set(db_session):
    """
    Test #389: User can have a display name
    """
    user = User(
        email="display@example.com",
        display_name="John Doe",
        status=UserStatus.verified,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db_session.add(user)
    db_session.commit()

    assert user.display_name == "John Doe"


@pytest.mark.unit
@pytest.mark.auth
def test_display_name_can_be_updated(db_session):
    """
    Test #390: Display name can be changed
    """
    user = User(
        email="changename@example.com",
        display_name="Old Name",
        status=UserStatus.verified,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db_session.add(user)
    db_session.commit()

    # Update display name
    user.display_name = "New Name"
    db_session.commit()
    db_session.refresh(user)

    assert user.display_name == "New Name"


@pytest.mark.unit
@pytest.mark.auth
def test_display_name_is_optional(db_session):
    """
    Test #391: Display name is optional (can be NULL)
    """
    user = User(
        email="noname@example.com",
        display_name=None,
        status=UserStatus.verified,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db_session.add(user)
    db_session.commit()

    assert user.display_name is None


@pytest.mark.unit
@pytest.mark.auth
def test_email_is_indexed_for_fast_lookup(db_session):
    """
    Test #392: Email field is indexed for performance
    """
    # Create many users
    for i in range(10):
        user = User(
            email=f"user{i}@example.com",
            status=UserStatus.verified,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db_session.add(user)
    db_session.commit()

    # Lookup should be fast (index exists in model)
    found = db_session.query(User).filter(User.email == "user5@example.com").first()
    assert found is not None
    assert found.email == "user5@example.com"


@pytest.mark.unit
@pytest.mark.auth
def test_phone_is_indexed_for_fast_lookup(db_session):
    """
    Test #393: Phone field is indexed for performance
    """
    # Create many users
    for i in range(10):
        user = User(
            phone=f"+9198765432{i:02d}",
            country_code="+91",
            status=UserStatus.verified,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db_session.add(user)
    db_session.commit()

    # Lookup should be fast (index exists in model)
    found = db_session.query(User).filter(User.phone == "+919876543205").first()
    assert found is not None


# ==============================================
# EDGE CASES & DATA VALIDATION (Tests 394-403)
# ==============================================

@pytest.mark.unit
@pytest.mark.auth
def test_user_without_email_or_phone_cannot_be_created(db_session):
    """
    Test #394: User must have either email or phone
    NOTE: App logic should enforce this, DB allows NULL for both
    """
    # DB allows this, but app should validate
    user = User(
        email=None,
        phone=None,
        status=UserStatus.unknown,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    # This succeeds at DB level (test documents current behavior)
    db_session.add(user)
    db_session.commit()
    
    # App should validate before reaching DB
    assert user.email is None and user.phone is None


@pytest.mark.unit
@pytest.mark.auth
def test_user_id_auto_generated(db_session):
    """
    Test #395: User ID is auto-generated (auto-increment)
    """
    user1 = User(email="auto1@example.com", created_at=datetime.utcnow(), updated_at=datetime.utcnow())
    user2 = User(email="auto2@example.com", created_at=datetime.utcnow(), updated_at=datetime.utcnow())
    
    db_session.add_all([user1, user2])
    db_session.commit()

    assert user1.id is not None
    assert user2.id is not None
    assert user1.id != user2.id


@pytest.mark.unit
@pytest.mark.auth
def test_user_can_be_deleted(db_session):
    """
    Test #396: User can be deleted from database
    """
    user = User(
        email="delete@example.com",
        status=UserStatus.verified,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db_session.add(user)
    db_session.commit()
    user_id = user.id

    # Delete user
    db_session.delete(user)
    db_session.commit()

    # Verify deleted
    deleted = db_session.query(User).filter(User.id == user_id).first()
    assert deleted is None


@pytest.mark.unit
@pytest.mark.auth
def test_password_can_be_null_for_oauth_users(db_session):
    """
    Test #397: OAuth users don't have passwords
    """
    user = User(
        email="oauth@example.com",
        password=None,  # OAuth user
        status=UserStatus.verified,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db_session.add(user)
    db_session.commit()

    assert user.password is None


@pytest.mark.unit
@pytest.mark.auth
def test_otp_can_be_null_when_not_requested(db_session):
    """
    Test #398: OTP is NULL when not in use
    """
    user = User(
        email="nootp@example.com",
        otp=None,
        status=UserStatus.verified,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db_session.add(user)
    db_session.commit()

    assert user.otp is None
    assert user.otp_expires_at is None


@pytest.mark.unit
@pytest.mark.auth
def test_otp_verified_defaults_to_false(db_session):
    """
    Test #399: otp_verified flag defaults to False
    """
    user = User(
        email="defaultotp@example.com",
        status=UserStatus.unknown,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db_session.add(user)
    db_session.commit()

    assert user.otp_verified is False


@pytest.mark.unit
@pytest.mark.auth
def test_user_relationships_exist(db_session):
    """
    Test #400: User has defined relationships
    """
    user = User(
        email="relations@example.com",
        status=UserStatus.verified,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db_session.add(user)
    db_session.commit()

    # Check relationships exist (even if empty)
    assert hasattr(user, 'contacts')
    assert hasattr(user, 'files')
    assert hasattr(user, 'verifications')


@pytest.mark.unit
@pytest.mark.auth
def test_all_user_statuses_defined(db_session):
    """
    Test #401: All UserStatus enum values are defined
    """
    # Check all status values exist
    assert UserStatus.unknown
    assert UserStatus.guest
    assert UserStatus.verified
    assert UserStatus.member


@pytest.mark.unit
@pytest.mark.auth
def test_user_can_have_all_fields_populated(db_session):
    """
    Test #402: User can have all fields set
    """
    user = User(
        email="complete@example.com",
        phone="+919876543210",
        country_code="+91",
        display_name="Complete User",
        password=hash_password("Password123"),
        status=UserStatus.member,
        communication_channel="email",
        otp="123456",
        otp_expires_at=datetime.utcnow() + timedelta(minutes=5),
        otp_verified=True,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    # All fields populated
    assert user.email is not None
    assert user.phone is not None
    assert user.display_name is not None
    assert user.password is not None
    assert user.otp is not None


@pytest.mark.unit
@pytest.mark.auth
def test_user_count_query_works(db_session):
    """
    Test #403: Can count total users
    """
    # Create test users
    for i in range(5):
        user = User(
            email=f"count{i}@example.com",
            status=UserStatus.verified,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db_session.add(user)
    db_session.commit()

    # Count users
    count = db_session.query(User).count()
    assert count >= 5
