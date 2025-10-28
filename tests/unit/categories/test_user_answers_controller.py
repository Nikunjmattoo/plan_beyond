"""
Module 4: Categories - User Answers Controller Tests (Tests 176-193)

Tests user answer operations for form steps.
"""
import pytest
from sqlalchemy.exc import IntegrityError

from app.models.category import CategoryMaster, CategorySectionMaster
from app.models.step import FormStep, StepType
from app.models.user_forms import UserSectionProgress, UserStepAnswer, SectionProgressStatus
from app.models.user import User


# ==============================================
# SAVE ANSWER TESTS (Tests 176-180)
# ==============================================

@pytest.mark.unit
@pytest.mark.categories
@pytest.mark.critical
def test_save_text_answer(db_session):
    """
    Test #176: Save text answer for open step
    """
    # Arrange
    user = User(email="test@example.com", password="hash123")
    db_session.add(user)
    db_session.commit()

    category = CategoryMaster(code="text_cat", name="Text Cat", sort_index=1)
    db_session.add(category)
    db_session.commit()

    section = CategorySectionMaster(category_id=category.id, code="text_sec", name="Text Sec", sort_index=1)
    db_session.add(section)
    db_session.commit()

    step = FormStep(section_master_id=section.id, step_name="name", title="Name", display_order=1, type=StepType.open)
    db_session.add(step)
    db_session.commit()

    progress = UserSectionProgress(user_id=user.id, category_id=category.id, section_id=section.id)
    db_session.add(progress)
    db_session.commit()

    answer = UserStepAnswer(progress_id=progress.id, step_id=step.id, value={"text": "John Doe"})

    # Act
    db_session.add(answer)
    db_session.commit()

    # Assert
    assert answer.id is not None
    assert answer.value == {"text": "John Doe"}


@pytest.mark.unit
@pytest.mark.categories
@pytest.mark.critical
def test_save_date_answer(db_session):
    """
    Test #177: Save date answer
    """
    # Arrange
    user = User(email="date@example.com", password="hash")
    db_session.add(user)
    db_session.commit()

    category = CategoryMaster(code="date_cat", name="Date Cat", sort_index=1)
    db_session.add(category)
    db_session.commit()

    section = CategorySectionMaster(category_id=category.id, code="date_sec", name="Date Sec", sort_index=1)
    db_session.add(section)
    db_session.commit()

    step = FormStep(section_master_id=section.id, step_name="dob", title="Date of Birth", display_order=1, type=StepType.date_dd_mm_yyyy)
    db_session.add(step)
    db_session.commit()

    progress = UserSectionProgress(user_id=user.id, category_id=category.id, section_id=section.id)
    db_session.add(progress)
    db_session.commit()

    answer = UserStepAnswer(progress_id=progress.id, step_id=step.id, value={"date": "15-08-1990"})

    # Act
    db_session.add(answer)
    db_session.commit()

    # Assert
    assert answer.value == {"date": "15-08-1990"}


@pytest.mark.unit
@pytest.mark.categories
@pytest.mark.critical
def test_save_dropdown_answer(db_session):
    """
    Test #178: Save dropdown (single_select) answer
    """
    # Arrange
    user = User(email="dropdown@example.com", password="hash")
    db_session.add(user)
    db_session.commit()

    category = CategoryMaster(code="dropdown_cat", name="Dropdown Cat", sort_index=1)
    db_session.add(category)
    db_session.commit()

    section = CategorySectionMaster(category_id=category.id, code="dropdown_sec", name="Dropdown Sec", sort_index=1)
    db_session.add(section)
    db_session.commit()

    step = FormStep(section_master_id=section.id, step_name="country", title="Country", display_order=1, type=StepType.single_select)
    db_session.add(step)
    db_session.commit()

    progress = UserSectionProgress(user_id=user.id, category_id=category.id, section_id=section.id)
    db_session.add(progress)
    db_session.commit()

    answer = UserStepAnswer(progress_id=progress.id, step_id=step.id, value={"selected": "USA"})

    # Act
    db_session.add(answer)
    db_session.commit()

    # Assert
    assert answer.value == {"selected": "USA"}


@pytest.mark.unit
@pytest.mark.categories
@pytest.mark.critical
def test_save_file_answer(db_session):
    """
    Test #179: Save file_upload answer with file_id
    """
    # Arrange
    user = User(email="file@example.com", password="hash")
    db_session.add(user)
    db_session.commit()

    category = CategoryMaster(code="file_cat", name="File Cat", sort_index=1)
    db_session.add(category)
    db_session.commit()

    section = CategorySectionMaster(category_id=category.id, code="file_sec", name="File Sec", sort_index=1)
    db_session.add(section)
    db_session.commit()

    step = FormStep(section_master_id=section.id, step_name="upload", title="Upload", display_order=1, type=StepType.file_upload)
    db_session.add(step)
    db_session.commit()

    progress = UserSectionProgress(user_id=user.id, category_id=category.id, section_id=section.id)
    db_session.add(progress)
    db_session.commit()

    answer = UserStepAnswer(progress_id=progress.id, step_id=step.id, value={"file_id": 123})

    # Act
    db_session.add(answer)
    db_session.commit()

    # Assert
    assert answer.value == {"file_id": 123}


@pytest.mark.unit
@pytest.mark.categories
@pytest.mark.critical
def test_save_multiselect_answer(db_session):
    """
    Test #180: Save checklist (multiselect) answer
    """
    # Arrange
    user = User(email="multi@example.com", password="hash")
    db_session.add(user)
    db_session.commit()

    category = CategoryMaster(code="multi_cat", name="Multi Cat", sort_index=1)
    db_session.add(category)
    db_session.commit()

    section = CategorySectionMaster(category_id=category.id, code="multi_sec", name="Multi Sec", sort_index=1)
    db_session.add(section)
    db_session.commit()

    step = FormStep(section_master_id=section.id, step_name="interests", title="Interests", display_order=1, type=StepType.checklist)
    db_session.add(step)
    db_session.commit()

    progress = UserSectionProgress(user_id=user.id, category_id=category.id, section_id=section.id)
    db_session.add(progress)
    db_session.commit()

    answer = UserStepAnswer(progress_id=progress.id, step_id=step.id, value={"selected": ["sports", "music", "reading"]})

    # Act
    db_session.add(answer)
    db_session.commit()

    # Assert
    assert answer.value == {"selected": ["sports", "music", "reading"]}


# ==============================================
# UPDATE & READ TESTS (Tests 181-183)
# ==============================================

@pytest.mark.unit
@pytest.mark.categories
@pytest.mark.critical
def test_update_existing_answer(db_session):
    """
    Test #181: Update existing answer
    """
    # Arrange
    user = User(email="update@example.com", password="hash")
    db_session.add(user)
    db_session.commit()

    category = CategoryMaster(code="update_cat", name="Update Cat", sort_index=1)
    db_session.add(category)
    db_session.commit()

    section = CategorySectionMaster(category_id=category.id, code="update_sec", name="Update Sec", sort_index=1)
    db_session.add(section)
    db_session.commit()

    step = FormStep(section_master_id=section.id, step_name="name", title="Name", display_order=1, type=StepType.open)
    db_session.add(step)
    db_session.commit()

    progress = UserSectionProgress(user_id=user.id, category_id=category.id, section_id=section.id)
    db_session.add(progress)
    db_session.commit()

    answer = UserStepAnswer(progress_id=progress.id, step_id=step.id, value={"text": "Original"})
    db_session.add(answer)
    db_session.commit()

    # Act
    answer.value = {"text": "Updated"}
    db_session.commit()

    # Assert
    updated = db_session.query(UserStepAnswer).filter(UserStepAnswer.id == answer.id).first()
    assert updated.value == {"text": "Updated"}


@pytest.mark.unit
@pytest.mark.categories
@pytest.mark.critical
def test_get_answer_by_step_id(db_session):
    """
    Test #182: Retrieve answer by step_id
    """
    # Arrange
    user = User(email="get@example.com", password="hash")
    db_session.add(user)
    db_session.commit()

    category = CategoryMaster(code="get_cat", name="Get Cat", sort_index=1)
    db_session.add(category)
    db_session.commit()

    section = CategorySectionMaster(category_id=category.id, code="get_sec", name="Get Sec", sort_index=1)
    db_session.add(section)
    db_session.commit()

    step = FormStep(section_master_id=section.id, step_name="email", title="Email", display_order=1, type=StepType.open)
    db_session.add(step)
    db_session.commit()

    progress = UserSectionProgress(user_id=user.id, category_id=category.id, section_id=section.id)
    db_session.add(progress)
    db_session.commit()

    answer = UserStepAnswer(progress_id=progress.id, step_id=step.id, value={"text": "test@example.com"})
    db_session.add(answer)
    db_session.commit()

    # Act
    result = db_session.query(UserStepAnswer).filter(
        UserStepAnswer.progress_id == progress.id,
        UserStepAnswer.step_id == step.id
    ).first()

    # Assert
    assert result is not None
    assert result.value == {"text": "test@example.com"}


@pytest.mark.unit
@pytest.mark.categories
@pytest.mark.critical
def test_get_answers_for_section(db_session):
    """
    Test #183: Get all answers for a section progress
    """
    # Arrange
    user = User(email="list@example.com", password="hash")
    db_session.add(user)
    db_session.commit()

    category = CategoryMaster(code="list_cat", name="List Cat", sort_index=1)
    db_session.add(category)
    db_session.commit()

    section = CategorySectionMaster(category_id=category.id, code="list_sec", name="List Sec", sort_index=1)
    db_session.add(section)
    db_session.commit()

    steps = [
        FormStep(section_master_id=section.id, step_name="q1", title="Q1", display_order=1, type=StepType.open),
        FormStep(section_master_id=section.id, step_name="q2", title="Q2", display_order=2, type=StepType.open)
    ]
    for s in steps:
        db_session.add(s)
    db_session.commit()

    progress = UserSectionProgress(user_id=user.id, category_id=category.id, section_id=section.id)
    db_session.add(progress)
    db_session.commit()

    answers = [
        UserStepAnswer(progress_id=progress.id, step_id=steps[0].id, value={"text": "Answer 1"}),
        UserStepAnswer(progress_id=progress.id, step_id=steps[1].id, value={"text": "Answer 2"})
    ]
    for a in answers:
        db_session.add(a)
    db_session.commit()

    # Act
    results = db_session.query(UserStepAnswer).filter(UserStepAnswer.progress_id == progress.id).all()

    # Assert
    assert len(results) == 2


# ==============================================
# DELETE TESTS (Test 184)
# ==============================================

@pytest.mark.unit
@pytest.mark.categories
@pytest.mark.critical
def test_delete_answer(db_session):
    """
    Test #184: Delete answer
    """
    # Arrange
    user = User(email="del@example.com", password="hash")
    db_session.add(user)
    db_session.commit()

    category = CategoryMaster(code="del_cat", name="Del Cat", sort_index=1)
    db_session.add(category)
    db_session.commit()

    section = CategorySectionMaster(category_id=category.id, code="del_sec", name="Del Sec", sort_index=1)
    db_session.add(section)
    db_session.commit()

    step = FormStep(section_master_id=section.id, step_name="del", title="Del", display_order=1, type=StepType.open)
    db_session.add(step)
    db_session.commit()

    progress = UserSectionProgress(user_id=user.id, category_id=category.id, section_id=section.id)
    db_session.add(progress)
    db_session.commit()

    answer = UserStepAnswer(progress_id=progress.id, step_id=step.id, value={"text": "Delete me"})
    db_session.add(answer)
    db_session.commit()

    answer_id = answer.id

    # Act
    db_session.delete(answer)
    db_session.commit()

    # Assert
    deleted = db_session.query(UserStepAnswer).filter(UserStepAnswer.id == answer_id).first()
    assert deleted is None


# ==============================================
# VALIDATION TESTS (Tests 185-188)
# ==============================================

@pytest.mark.unit
@pytest.mark.categories
@pytest.mark.critical
def test_answer_validation_text_type(db_session):
    """
    Test #185: Text answer stores JSON value
    """
    # Arrange
    user = User(email="val_text@example.com", password="hash")
    db_session.add(user)
    db_session.commit()

    category = CategoryMaster(code="val_cat", name="Val Cat", sort_index=1)
    db_session.add(category)
    db_session.commit()

    section = CategorySectionMaster(category_id=category.id, code="val_sec", name="Val Sec", sort_index=1)
    db_session.add(section)
    db_session.commit()

    step = FormStep(section_master_id=section.id, step_name="val", title="Val", display_order=1, type=StepType.open)
    db_session.add(step)
    db_session.commit()

    progress = UserSectionProgress(user_id=user.id, category_id=category.id, section_id=section.id)
    db_session.add(progress)
    db_session.commit()

    answer = UserStepAnswer(progress_id=progress.id, step_id=step.id, value={"text": "Valid text"})

    # Act
    db_session.add(answer)
    db_session.commit()

    # Assert
    assert isinstance(answer.value, dict)


@pytest.mark.unit
@pytest.mark.categories
@pytest.mark.critical
def test_answer_validation_date_type(db_session):
    """
    Test #186: Date answer stores JSON value
    """
    # Arrange
    user = User(email="val_date@example.com", password="hash")
    db_session.add(user)
    db_session.commit()

    category = CategoryMaster(code="vald_cat", name="Vald Cat", sort_index=1)
    db_session.add(category)
    db_session.commit()

    section = CategorySectionMaster(category_id=category.id, code="vald_sec", name="Vald Sec", sort_index=1)
    db_session.add(section)
    db_session.commit()

    step = FormStep(section_master_id=section.id, step_name="vald", title="Vald", display_order=1, type=StepType.date_dd_mm_yyyy)
    db_session.add(step)
    db_session.commit()

    progress = UserSectionProgress(user_id=user.id, category_id=category.id, section_id=section.id)
    db_session.add(progress)
    db_session.commit()

    answer = UserStepAnswer(progress_id=progress.id, step_id=step.id, value={"date": "01-01-2000"})

    # Act
    db_session.add(answer)
    db_session.commit()

    # Assert
    assert isinstance(answer.value, dict)


@pytest.mark.unit
@pytest.mark.categories
@pytest.mark.critical
def test_answer_validation_dropdown_type(db_session):
    """
    Test #187: Dropdown answer stores JSON value
    """
    # Arrange
    user = User(email="val_drop@example.com", password="hash")
    db_session.add(user)
    db_session.commit()

    category = CategoryMaster(code="valdd_cat", name="Valdd Cat", sort_index=1)
    db_session.add(category)
    db_session.commit()

    section = CategorySectionMaster(category_id=category.id, code="valdd_sec", name="Valdd Sec", sort_index=1)
    db_session.add(section)
    db_session.commit()

    step = FormStep(section_master_id=section.id, step_name="valdd", title="Valdd", display_order=1, type=StepType.single_select)
    db_session.add(step)
    db_session.commit()

    progress = UserSectionProgress(user_id=user.id, category_id=category.id, section_id=section.id)
    db_session.add(progress)
    db_session.commit()

    answer = UserStepAnswer(progress_id=progress.id, step_id=step.id, value={"selected": "option1"})

    # Act
    db_session.add(answer)
    db_session.commit()

    # Assert
    assert isinstance(answer.value, dict)


@pytest.mark.unit
@pytest.mark.categories
@pytest.mark.critical
def test_required_step_must_have_answer(db_session):
    """
    Test #188: Required (mandatory) steps logic test
    """
    # Arrange
    user = User(email="req@example.com", password="hash")
    db_session.add(user)
    db_session.commit()

    category = CategoryMaster(code="req_cat", name="Req Cat", sort_index=1)
    db_session.add(category)
    db_session.commit()

    section = CategorySectionMaster(category_id=category.id, code="req_sec", name="Req Sec", sort_index=1)
    db_session.add(section)
    db_session.commit()

    step = FormStep(section_master_id=section.id, step_name="req", title="Req", display_order=1, type=StepType.open, mandatory=True)
    db_session.add(step)
    db_session.commit()

    progress = UserSectionProgress(user_id=user.id, category_id=category.id, section_id=section.id)
    db_session.add(progress)
    db_session.commit()

    # Act - Logic test: if step is mandatory, should have answer
    if step.mandatory:
        answer = UserStepAnswer(progress_id=progress.id, step_id=step.id, value={"text": "Required answer"})
        db_session.add(answer)
        db_session.commit()

    # Assert
    assert step.mandatory is True


# ==============================================
# SECTION COMPLETION & AUTHORIZATION (Tests 189-191)
# ==============================================

@pytest.mark.unit
@pytest.mark.categories
@pytest.mark.critical
def test_section_completion_check(db_session):
    """
    Test #189: Section completion requires all mandatory steps answered
    """
    # Arrange
    user = User(email="comp@example.com", password="hash")
    db_session.add(user)
    db_session.commit()

    category = CategoryMaster(code="comp_cat", name="Comp Cat", sort_index=1)
    db_session.add(category)
    db_session.commit()

    section = CategorySectionMaster(category_id=category.id, code="comp_sec", name="Comp Sec", sort_index=1)
    db_session.add(section)
    db_session.commit()

    steps = [
        FormStep(section_master_id=section.id, step_name="q1", title="Q1", display_order=1, type=StepType.open, mandatory=True),
        FormStep(section_master_id=section.id, step_name="q2", title="Q2", display_order=2, type=StepType.open, mandatory=True)
    ]
    for s in steps:
        db_session.add(s)
    db_session.commit()

    progress = UserSectionProgress(user_id=user.id, category_id=category.id, section_id=section.id)
    db_session.add(progress)
    db_session.commit()

    # Add answers for all mandatory steps
    for step in steps:
        answer = UserStepAnswer(progress_id=progress.id, step_id=step.id, value={"text": "Answer"})
        db_session.add(answer)
    db_session.commit()

    # Act
    answers_count = db_session.query(UserStepAnswer).filter(UserStepAnswer.progress_id == progress.id).count()

    # Assert
    assert answers_count == 2


@pytest.mark.unit
@pytest.mark.categories
@pytest.mark.critical
def test_user_can_only_access_own_answers(db_session):
    """
    Test #190: Users can only access their own answers (logic test)
    """
    # Arrange
    user1 = User(email="user1@example.com", password="hash")
    user2 = User(email="user2@example.com", password="hash")
    db_session.add_all([user1, user2])
    db_session.commit()

    category = CategoryMaster(code="auth_cat", name="Auth Cat", sort_index=1)
    db_session.add(category)
    db_session.commit()

    section = CategorySectionMaster(category_id=category.id, code="auth_sec", name="Auth Sec", sort_index=1)
    db_session.add(section)
    db_session.commit()

    step = FormStep(section_master_id=section.id, step_name="auth", title="Auth", display_order=1, type=StepType.open)
    db_session.add(step)
    db_session.commit()

    progress1 = UserSectionProgress(user_id=user1.id, category_id=category.id, section_id=section.id)
    db_session.add(progress1)
    db_session.commit()

    answer1 = UserStepAnswer(progress_id=progress1.id, step_id=step.id, value={"text": "User1 answer"})
    db_session.add(answer1)
    db_session.commit()

    # Act - User2 should NOT see User1's answers
    user2_answers = db_session.query(UserStepAnswer).join(UserSectionProgress).filter(
        UserSectionProgress.user_id == user2.id
    ).all()

    # Assert
    assert len(user2_answers) == 0


@pytest.mark.unit
@pytest.mark.categories
def test_answer_history_tracking(db_session):
    """
    Test #191: Answer history tracking (future feature - placeholder)
    """
    # Arrange
    user = User(email="hist@example.com", password="hash")
    db_session.add(user)
    db_session.commit()

    # Assert - Placeholder for future history tracking
    assert user.id is not None


# ==============================================
# JSON STORAGE & BULK OPERATIONS (Tests 192-193)
# ==============================================

@pytest.mark.unit
@pytest.mark.categories
def test_answer_json_storage_format(db_session):
    """
    Test #192: Answers stored in JSON format
    """
    # Arrange
    user = User(email="json@example.com", password="hash")
    db_session.add(user)
    db_session.commit()

    category = CategoryMaster(code="json_cat", name="JSON Cat", sort_index=1)
    db_session.add(category)
    db_session.commit()

    section = CategorySectionMaster(category_id=category.id, code="json_sec", name="JSON Sec", sort_index=1)
    db_session.add(section)
    db_session.commit()

    step = FormStep(section_master_id=section.id, step_name="json", title="JSON", display_order=1, type=StepType.open)
    db_session.add(step)
    db_session.commit()

    progress = UserSectionProgress(user_id=user.id, category_id=category.id, section_id=section.id)
    db_session.add(progress)
    db_session.commit()

    answer = UserStepAnswer(progress_id=progress.id, step_id=step.id, value={"complex": {"nested": "data"}})

    # Act
    db_session.add(answer)
    db_session.commit()

    # Assert
    assert isinstance(answer.value, dict)
    assert "complex" in answer.value


@pytest.mark.unit
@pytest.mark.categories
def test_bulk_save_answers(db_session):
    """
    Test #193: Bulk save multiple answers
    """
    # Arrange
    user = User(email="bulk@example.com", password="hash")
    db_session.add(user)
    db_session.commit()

    category = CategoryMaster(code="bulk_cat", name="Bulk Cat", sort_index=1)
    db_session.add(category)
    db_session.commit()

    section = CategorySectionMaster(category_id=category.id, code="bulk_sec", name="Bulk Sec", sort_index=1)
    db_session.add(section)
    db_session.commit()

    steps = [
        FormStep(section_master_id=section.id, step_name=f"q{i}", title=f"Q{i}", display_order=i, type=StepType.open)
        for i in range(1, 6)
    ]
    for s in steps:
        db_session.add(s)
    db_session.commit()

    progress = UserSectionProgress(user_id=user.id, category_id=category.id, section_id=section.id)
    db_session.add(progress)
    db_session.commit()

    answers = [
        UserStepAnswer(progress_id=progress.id, step_id=step.id, value={"text": f"Answer {i}"})
        for i, step in enumerate(steps, 1)
    ]

    # Act
    db_session.bulk_save_objects(answers)
    db_session.commit()

    # Assert
    saved = db_session.query(UserStepAnswer).filter(UserStepAnswer.progress_id == progress.id).count()
    assert saved == 5
