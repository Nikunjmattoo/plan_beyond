"""
Module 6: Memories - Memory File Tests (Tests 620-644)

Tests MemoryFile attachment and management.

Test Categories:
- Attach files (Tests 620-624)
- File metadata (Tests 625-629)
- Delete files (Tests 630-632)
- File uniqueness (Tests 633-636)
- File relationships (Tests 637-644)
"""
# Standard library
import pytest

# Third-party
from sqlalchemy.exc import IntegrityError

# Application imports
from app.models.user import User, UserStatus
from app.models.memory import MemoryCollection, MemoryFile
from app.models.contact import Contact
from app.models.enums import AssignmentRole


# ==============================================================================
# ATTACH FILES TESTS (Tests 620-624)
# ==============================================================================

@pytest.mark.unit
@pytest.mark.memories
@pytest.mark.critical
def test_attach_file_to_collection(db_session):
    """
    Test #620: Attach file to memory collection

    Verifies file attachment functionality.
    """
    # Arrange
    user = User(email="attach@test.com", status=UserStatus.verified)
    db_session.add(user)
    db_session.commit()

    collection = MemoryCollection(user_id=user.id, name="Photos")
    db_session.add(collection)
    db_session.commit()

    # Act
    file = MemoryFile(
        collection_id=collection.id,
        app_url="https://example.com/photo.jpg",
        title="Vacation Photo",
        mime_type="image/jpeg",
        size=102400
    )
    db_session.add(file)
    db_session.commit()

    # Assert
    assert file.id is not None
    assert file.collection_id == collection.id
    assert file.app_url == "https://example.com/photo.jpg"


@pytest.mark.unit
@pytest.mark.memories
@pytest.mark.critical
def test_attach_multiple_files(db_session):
    """
    Test #621: Attach multiple files to same collection

    Collections can have many files.
    """
    # Arrange
    user = User(email="multi_files@test.com", status=UserStatus.verified)
    db_session.add(user)
    db_session.commit()

    collection = MemoryCollection(user_id=user.id, name="Album")
    db_session.add(collection)
    db_session.commit()

    # Act
    file1 = MemoryFile(collection_id=collection.id, app_url="https://example.com/1.jpg", title="Photo 1")
    file2 = MemoryFile(collection_id=collection.id, app_url="https://example.com/2.jpg", title="Photo 2")
    db_session.add_all([file1, file2])
    db_session.commit()

    # Assert
    files = db_session.query(MemoryFile).filter(MemoryFile.collection_id == collection.id).all()
    assert len(files) == 2


@pytest.mark.unit
@pytest.mark.memories
@pytest.mark.critical
def test_attach_file_with_file_id_reference(db_session):
    """
    Test #622: Attach file using file_id reference

    Can reference existing vault file.
    """
    # Arrange
    from app.models.vault import VaultFile

    user = User(email="file_ref@test.com", status=UserStatus.verified)
    db_session.add(user)
    db_session.commit()

    vault_file = VaultFile(user_id=user.id, filename="doc.pdf", file_path="/vault/doc.pdf")
    db_session.add(vault_file)
    db_session.commit()

    collection = MemoryCollection(user_id=user.id, name="Documents")
    db_session.add(collection)
    db_session.commit()

    # Act
    memory_file = MemoryFile(collection_id=collection.id, file_id=vault_file.id, title="Important Doc")
    db_session.add(memory_file)
    db_session.commit()

    # Assert
    assert memory_file.file_id == vault_file.id


@pytest.mark.unit
@pytest.mark.memories
@pytest.mark.critical
def test_attach_file_app_url_only(db_session):
    """
    Test #623: Attach file with app_url only (no file_id)

    External URL references supported.
    """
    # Arrange
    user = User(email="url_only@test.com", status=UserStatus.verified)
    db_session.add(user)
    db_session.commit()

    collection = MemoryCollection(user_id=user.id, name="External")
    db_session.add(collection)
    db_session.commit()

    # Act
    file = MemoryFile(
        collection_id=collection.id,
        app_url="https://youtube.com/watch?v=abc123",
        title="Video Memory"
    )
    db_session.add(file)
    db_session.commit()

    # Assert
    assert file.app_url is not None
    assert file.file_id is None


@pytest.mark.unit
@pytest.mark.memories
@pytest.mark.critical
def test_attach_file_cascade_from_collection(db_session):
    """
    Test #624: Collection has files relationship

    Verifies relationship configuration.
    """
    # Arrange
    user = User(email="relationship@test.com", status=UserStatus.verified)
    db_session.add(user)
    db_session.commit()

    collection = MemoryCollection(user_id=user.id, name="Relationship Test")
    db_session.add(collection)
    db_session.commit()

    file = MemoryFile(collection_id=collection.id, app_url="https://example.com/test.jpg")
    db_session.add(file)
    db_session.commit()

    # Act & Assert
    assert hasattr(collection, 'files')


# ==============================================================================
# FILE METADATA TESTS (Tests 625-629)
# ==============================================================================

@pytest.mark.unit
@pytest.mark.memories
@pytest.mark.critical
def test_memory_file_has_title(db_session):
    """
    Test #625: Memory file can have title

    Descriptive titles for files.
    """
    # Arrange
    user = User(email="title@test.com", status=UserStatus.verified)
    db_session.add(user)
    db_session.commit()

    collection = MemoryCollection(user_id=user.id, name="Titled")
    db_session.add(collection)
    db_session.commit()

    # Act
    file = MemoryFile(
        collection_id=collection.id,
        app_url="https://example.com/file.pdf",
        title="My Important Document"
    )
    db_session.add(file)
    db_session.commit()

    # Assert
    assert file.title == "My Important Document"


@pytest.mark.unit
@pytest.mark.memories
@pytest.mark.critical
def test_memory_file_has_mime_type(db_session):
    """
    Test #626: Memory file stores mime_type

    File type metadata stored.
    """
    # Arrange
    user = User(email="mime@test.com", status=UserStatus.verified)
    db_session.add(user)
    db_session.commit()

    collection = MemoryCollection(user_id=user.id, name="Mime Test")
    db_session.add(collection)
    db_session.commit()

    # Act
    file = MemoryFile(
        collection_id=collection.id,
        app_url="https://example.com/video.mp4",
        mime_type="video/mp4"
    )
    db_session.add(file)
    db_session.commit()

    # Assert
    assert file.mime_type == "video/mp4"


@pytest.mark.unit
@pytest.mark.memories
@pytest.mark.critical
def test_memory_file_has_size(db_session):
    """
    Test #627: Memory file stores size in bytes

    File size metadata stored.
    """
    # Arrange
    user = User(email="size@test.com", status=UserStatus.verified)
    db_session.add(user)
    db_session.commit()

    collection = MemoryCollection(user_id=user.id, name="Size Test")
    db_session.add(collection)
    db_session.commit()

    # Act
    file = MemoryFile(
        collection_id=collection.id,
        app_url="https://example.com/large.zip",
        size=5242880  # 5 MB
    )
    db_session.add(file)
    db_session.commit()

    # Assert
    assert file.size == 5242880


@pytest.mark.unit
@pytest.mark.memories
def test_memory_file_metadata_optional(db_session):
    """
    Test #628: File metadata fields are optional

    Minimal file with just URL works.
    """
    # Arrange
    user = User(email="minimal@test.com", status=UserStatus.verified)
    db_session.add(user)
    db_session.commit()

    collection = MemoryCollection(user_id=user.id, name="Minimal")
    db_session.add(collection)
    db_session.commit()

    # Act
    file = MemoryFile(collection_id=collection.id, app_url="https://example.com/file")
    db_session.add(file)
    db_session.commit()

    # Assert
    assert file.title is None
    assert file.mime_type is None
    assert file.size is None


@pytest.mark.unit
@pytest.mark.memories
def test_update_memory_file_metadata(db_session):
    """
    Test #629: Can update file metadata after creation

    Metadata updates supported.
    """
    # Arrange
    user = User(email="update_meta@test.com", status=UserStatus.verified)
    db_session.add(user)
    db_session.commit()

    collection = MemoryCollection(user_id=user.id, name="Update Meta")
    db_session.add(collection)
    db_session.commit()

    file = MemoryFile(collection_id=collection.id, app_url="https://example.com/file", title="Old Title")
    db_session.add(file)
    db_session.commit()

    # Act
    file.title = "New Title"
    file.mime_type = "image/png"
    file.size = 1024
    db_session.commit()

    # Assert
    assert file.title == "New Title"
    assert file.mime_type == "image/png"
    assert file.size == 1024


# ==============================================================================
# DELETE FILES TESTS (Tests 630-632)
# ==============================================================================

@pytest.mark.unit
@pytest.mark.memories
@pytest.mark.critical
def test_delete_memory_file(db_session):
    """
    Test #630: Delete memory file from collection

    Verifies file deletion.
    """
    # Arrange
    user = User(email="del_file@test.com", status=UserStatus.verified)
    db_session.add(user)
    db_session.commit()

    collection = MemoryCollection(user_id=user.id, name="Delete File")
    db_session.add(collection)
    db_session.commit()

    file = MemoryFile(collection_id=collection.id, app_url="https://example.com/delete.jpg")
    db_session.add(file)
    db_session.commit()

    file_id = file.id

    # Act
    db_session.delete(file)
    db_session.commit()

    # Assert
    deleted = db_session.query(MemoryFile).filter(MemoryFile.id == file_id).first()
    assert deleted is None


@pytest.mark.unit
@pytest.mark.memories
@pytest.mark.critical
def test_delete_file_preserves_collection(db_session):
    """
    Test #631: Deleting file doesn't delete collection

    Files can be removed independently.
    """
    # Arrange
    user = User(email="keep_coll@test.com", status=UserStatus.verified)
    db_session.add(user)
    db_session.commit()

    collection = MemoryCollection(user_id=user.id, name="Keep Collection")
    db_session.add(collection)
    db_session.commit()

    file = MemoryFile(collection_id=collection.id, app_url="https://example.com/file.jpg")
    db_session.add(file)
    db_session.commit()

    # Act
    db_session.delete(file)
    db_session.commit()

    # Assert
    still_exists = db_session.query(MemoryCollection).filter(MemoryCollection.id == collection.id).first()
    assert still_exists is not None


@pytest.mark.unit
@pytest.mark.memories
@pytest.mark.critical
def test_delete_file_on_vault_file_deletion(db_session):
    """
    Test #632: Deleting vault file sets memory file_id to NULL

    CASCADE SET NULL on file_id foreign key.
    """
    # Arrange
    from app.models.vault import VaultFile

    user = User(email="cascade_null@test.com", status=UserStatus.verified)
    db_session.add(user)
    db_session.commit()

    vault_file = VaultFile(user_id=user.id, filename="test.pdf", file_path="/vault/test.pdf")
    db_session.add(vault_file)
    db_session.commit()

    collection = MemoryCollection(user_id=user.id, name="Cascade Null")
    db_session.add(collection)
    db_session.commit()

    memory_file = MemoryFile(collection_id=collection.id, file_id=vault_file.id, app_url="https://example.com/backup")
    db_session.add(memory_file)
    db_session.commit()

    # Act
    db_session.delete(vault_file)
    db_session.commit()
    db_session.refresh(memory_file)

    # Assert
    assert memory_file.file_id is None  # SET NULL
    assert memory_file.app_url is not None  # Still has URL backup


# ==============================================================================
# FILE UNIQUENESS TESTS (Tests 633-636)
# ==============================================================================

@pytest.mark.unit
@pytest.mark.memories
@pytest.mark.critical
def test_duplicate_app_url_same_collection_fails(db_session):
    """
    Test #633: Cannot add same app_url twice to same collection

    CRITICAL: Uniqueness constraint on (collection_id, app_url).
    """
    # Arrange
    user = User(email="dup_url@test.com", status=UserStatus.verified)
    db_session.add(user)
    db_session.commit()

    collection = MemoryCollection(user_id=user.id, name="Dup URL")
    db_session.add(collection)
    db_session.commit()

    url = "https://example.com/photo.jpg"

    file1 = MemoryFile(collection_id=collection.id, app_url=url)
    db_session.add(file1)
    db_session.commit()

    # Act & Assert
    file2 = MemoryFile(collection_id=collection.id, app_url=url)
    db_session.add(file2)

    with pytest.raises(IntegrityError):
        db_session.commit()


@pytest.mark.unit
@pytest.mark.memories
@pytest.mark.critical
def test_same_url_different_collections_allowed(db_session):
    """
    Test #634: Same app_url can exist in different collections

    Uniqueness is per collection.
    """
    # Arrange
    user = User(email="multi_coll_url@test.com", status=UserStatus.verified)
    db_session.add(user)
    db_session.commit()

    collection1 = MemoryCollection(user_id=user.id, name="Collection 1")
    collection2 = MemoryCollection(user_id=user.id, name="Collection 2")
    db_session.add_all([collection1, collection2])
    db_session.commit()

    url = "https://example.com/shared.jpg"

    # Act
    file1 = MemoryFile(collection_id=collection1.id, app_url=url)
    file2 = MemoryFile(collection_id=collection2.id, app_url=url)
    db_session.add_all([file1, file2])
    db_session.commit()

    # Assert
    assert file1.id != file2.id


@pytest.mark.unit
@pytest.mark.memories
def test_null_app_url_allowed_multiple(db_session):
    """
    Test #635: Multiple files with NULL app_url allowed (file_id only)

    NULL app_url doesn't trigger uniqueness constraint.
    """
    # Arrange
    from app.models.vault import VaultFile

    user = User(email="null_url@test.com", status=UserStatus.verified)
    db_session.add(user)
    db_session.commit()

    vault1 = VaultFile(user_id=user.id, filename="file1.pdf", file_path="/vault/1.pdf")
    vault2 = VaultFile(user_id=user.id, filename="file2.pdf", file_path="/vault/2.pdf")
    db_session.add_all([vault1, vault2])
    db_session.commit()

    collection = MemoryCollection(user_id=user.id, name="Null URLs")
    db_session.add(collection)
    db_session.commit()

    # Act
    file1 = MemoryFile(collection_id=collection.id, file_id=vault1.id, app_url=None)
    file2 = MemoryFile(collection_id=collection.id, file_id=vault2.id, app_url=None)
    db_session.add_all([file1, file2])
    db_session.commit()

    # Assert
    assert file1.id != file2.id


@pytest.mark.unit
@pytest.mark.memories
def test_get_files_for_collection(db_session):
    """
    Test #636: Retrieve all files for a collection

    Query files by collection_id.
    """
    # Arrange
    user = User(email="get_files@test.com", status=UserStatus.verified)
    db_session.add(user)
    db_session.commit()

    collection = MemoryCollection(user_id=user.id, name="Get Files")
    db_session.add(collection)
    db_session.commit()

    file1 = MemoryFile(collection_id=collection.id, app_url="https://example.com/1.jpg")
    file2 = MemoryFile(collection_id=collection.id, app_url="https://example.com/2.jpg")
    db_session.add_all([file1, file2])
    db_session.commit()

    # Act
    files = db_session.query(MemoryFile).filter(MemoryFile.collection_id == collection.id).all()

    # Assert
    assert len(files) == 2


# ==============================================================================
# FILE RELATIONSHIPS TESTS (Tests 637-644)
# ==============================================================================

@pytest.mark.unit
@pytest.mark.memories
@pytest.mark.critical
def test_memory_file_has_vault_file_relationship(db_session):
    """
    Test #637: MemoryFile can reference VaultFile

    Foreign key relationship to vault.
    """
    # Arrange
    from app.models.vault import VaultFile

    user = User(email="vault_rel@test.com", status=UserStatus.verified)
    db_session.add(user)
    db_session.commit()

    vault_file = VaultFile(user_id=user.id, filename="doc.pdf", file_path="/vault/doc.pdf")
    db_session.add(vault_file)
    db_session.commit()

    collection = MemoryCollection(user_id=user.id, name="Vault Rel")
    db_session.add(collection)
    db_session.commit()

    # Act
    memory_file = MemoryFile(collection_id=collection.id, file_id=vault_file.id, app_url="https://backup.com/doc.pdf")
    db_session.add(memory_file)
    db_session.commit()

    # Assert
    assert memory_file.file_id == vault_file.id


@pytest.mark.unit
@pytest.mark.memories
@pytest.mark.critical
def test_memory_file_belongs_to_collection(db_session):
    """
    Test #638: MemoryFile belongs to MemoryCollection

    Foreign key relationship enforced.
    """
    # Arrange
    user = User(email="belongs@test.com", status=UserStatus.verified)
    db_session.add(user)
    db_session.commit()

    collection = MemoryCollection(user_id=user.id, name="Belongs")
    db_session.add(collection)
    db_session.commit()

    # Act
    file = MemoryFile(collection_id=collection.id, app_url="https://example.com/file")
    db_session.add(file)
    db_session.commit()

    # Assert
    assert file.collection_id == collection.id


@pytest.mark.unit
@pytest.mark.memories
@pytest.mark.critical
def test_orphan_memory_file_not_allowed(db_session):
    """
    Test #639: MemoryFile requires collection_id (NOT NULL)

    Cannot create file without collection.
    """
    # Arrange & Act & Assert
    file = MemoryFile(collection_id=None, app_url="https://example.com/orphan")
    db_session.add(file)

    with pytest.raises(IntegrityError):
        db_session.commit()


@pytest.mark.unit
@pytest.mark.memories
def test_collection_files_relationship(db_session):
    """
    Test #640: Collection has files relationship

    Can access collection.files.
    """
    # Arrange
    user = User(email="coll_files@test.com", status=UserStatus.verified)
    db_session.add(user)
    db_session.commit()

    collection = MemoryCollection(user_id=user.id, name="Files Rel")
    db_session.add(collection)
    db_session.commit()

    file = MemoryFile(collection_id=collection.id, app_url="https://example.com/test")
    db_session.add(file)
    db_session.commit()

    db_session.refresh(collection)

    # Act & Assert
    assert hasattr(collection, 'files')
    assert len(collection.files) == 1


@pytest.mark.unit
@pytest.mark.memories
def test_memory_file_cascade_delete_on_collection(db_session):
    """
    Test #641: Files are deleted when collection is deleted

    Cascade delete verified.
    """
    # Arrange
    user = User(email="cascade_files@test.com", status=UserStatus.verified)
    db_session.add(user)
    db_session.commit()

    collection = MemoryCollection(user_id=user.id, name="Cascade Files")
    db_session.add(collection)
    db_session.commit()

    file = MemoryFile(collection_id=collection.id, app_url="https://example.com/cascade")
    db_session.add(file)
    db_session.commit()

    file_id = file.id

    # Act
    db_session.delete(collection)
    db_session.commit()

    # Assert
    deleted_file = db_session.query(MemoryFile).filter(MemoryFile.id == file_id).first()
    assert deleted_file is None


@pytest.mark.unit
@pytest.mark.memories
def test_multiple_collections_multiple_files(db_session):
    """
    Test #642: User can have multiple collections with multiple files

    Complex scenario validation.
    """
    # Arrange
    user = User(email="complex@test.com", status=UserStatus.verified)
    db_session.add(user)
    db_session.commit()

    coll1 = MemoryCollection(user_id=user.id, name="Collection 1")
    coll2 = MemoryCollection(user_id=user.id, name="Collection 2")
    db_session.add_all([coll1, coll2])
    db_session.commit()

    # Act
    file1 = MemoryFile(collection_id=coll1.id, app_url="https://example.com/c1f1")
    file2 = MemoryFile(collection_id=coll1.id, app_url="https://example.com/c1f2")
    file3 = MemoryFile(collection_id=coll2.id, app_url="https://example.com/c2f1")
    db_session.add_all([file1, file2, file3])
    db_session.commit()

    # Assert
    coll1_files = db_session.query(MemoryFile).filter(MemoryFile.collection_id == coll1.id).all()
    coll2_files = db_session.query(MemoryFile).filter(MemoryFile.collection_id == coll2.id).all()

    assert len(coll1_files) == 2
    assert len(coll2_files) == 1


@pytest.mark.unit
@pytest.mark.memories
def test_file_count_per_collection(db_session):
    """
    Test #643: Can count files in a collection

    Query aggregation works.
    """
    # Arrange
    from sqlalchemy import func

    user = User(email="count_files@test.com", status=UserStatus.verified)
    db_session.add(user)
    db_session.commit()

    collection = MemoryCollection(user_id=user.id, name="Count Test")
    db_session.add(collection)
    db_session.commit()

    for i in range(5):
        file = MemoryFile(collection_id=collection.id, app_url=f"https://example.com/file{i}")
        db_session.add(file)
    db_session.commit()

    # Act
    count = db_session.query(func.count(MemoryFile.id)).filter(
        MemoryFile.collection_id == collection.id
    ).scalar()

    # Assert
    assert count == 5


@pytest.mark.unit
@pytest.mark.memories
def test_empty_collection_has_zero_files(db_session):
    """
    Test #644: Empty collection has zero files

    Edge case validation.
    """
    # Arrange
    user = User(email="empty_coll@test.com", status=UserStatus.verified)
    db_session.add(user)
    db_session.commit()

    collection = MemoryCollection(user_id=user.id, name="Empty")
    db_session.add(collection)
    db_session.commit()

    db_session.refresh(collection)

    # Act & Assert
    assert len(collection.files) == 0
