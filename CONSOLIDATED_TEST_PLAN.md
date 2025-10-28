# CONSOLIDATED TEST PLAN - PLAN BEYOND
## Complete Test Suite: 1,644 Tests

**Last Updated:** 2025-10-28
**Total Tests:** 1,644
**Strategy:** Build incrementally, test locally, commit frequently

---

## 📊 Test Distribution Summary

| Category | Count | Percentage |
|----------|-------|------------|
| **Unit Tests** | 1,145 | 69.7% |
| **Integration Tests** | 290 | 17.6% |
| **E2E Tests** | 91 | 5.5% |
| **Specialized Tests** | 118 | 7.2% |
| **TOTAL** | **1,644** | **100%** |

---

## 🎯 Module Overview

| # | Module Name | Unit | Integration | E2E | Specialized | Total |
|---|-------------|------|-------------|-----|-------------|-------|
| **0** | **ORM Models (PRIORITY)** | **156** | **0** | **0** | **0** | **156** |
| 1 | Foundation (DB Operations) | 102 | 15 | 0 | 0 | 117 |
| 2 | Authentication & Authorization | 85 | 45 | 0 | 0 | 130 |
| 3 | Vault & Encryption | 125 | 50 | 0 | 0 | 175 |
| 4 | Categories & Digital Assets | 107 | 45 | 0 | 0 | 152 |
| 5 | Folders & Relationships | 77 | 20 | 0 | 0 | 97 |
| 6 | Memories & Messages | 73 | 20 | 0 | 0 | 93 |
| 7 | Death Declaration System | 129 | 45 | 0 | 0 | 174 |
| 8 | Reminder System | 82 | 20 | 0 | 0 | 102 |
| 9 | Policy Checker & OCR | 68 | 15 | 0 | 0 | 83 |
| 10 | File Storage & S3 | 52 | 15 | 0 | 0 | 67 |
| 11 | Admin Operations | 47 | 0 | 0 | 0 | 47 |
| 12 | External Services | 42 | 0 | 0 | 0 | 42 |
| **E2E** | **User Journeys** | **0** | **0** | **48** | **0** | **48** |
| **E2E** | **Workflows** | **0** | **0** | **43** | **0** | **43** |
| **Spec** | **Security** | **0** | **0** | **0** | **38** | **38** |
| **Spec** | **Performance** | **0** | **0** | **0** | **25** | **25** |
| **Spec** | **Concurrency** | **0** | **0** | **0** | **15** | **15** |
| **Spec** | **Regression** | **0** | **0** | **0** | **40** | **40** |
| | **TOTAL** | **1,145** | **290** | **91** | **118** | **1,644** |

---

## 🏗️ PRIORITY MODULE 0: ORM MODELS (156 tests)

**Why First:** SQLAlchemy models are the foundation. Must validate schema correctness before testing operations.

### Test Files Structure

```
tests/unit/models/
├── __init__.py
├── test_user_model.py                             # 15 tests
├── test_contact_model.py                          # 12 tests
├── test_vault_file_model.py                       # 15 tests
├── test_folder_model.py                           # 12 tests
├── test_memory_collection_model.py                # 12 tests
├── test_death_declaration_model.py                # 15 tests
├── test_trustee_model.py                          # 10 tests
├── test_category_model.py                         # 10 tests
├── test_section_model.py                          # 10 tests
├── test_step_model.py                             # 12 tests
├── test_reminder_model.py                         # 10 tests
├── test_admin_model.py                            # 8 tests
└── test_relationship_models.py                    # 15 tests
```

### What ORM Tests Validate

1. **Schema Correctness**
   - Table names match database
   - All columns defined
   - Column types correct (String, Integer, DateTime, JSON, Text, Enum)

2. **Constraints**
   - Unique constraints (email, phone, username)
   - Not null constraints
   - Check constraints (e.g., creation_mode IN ('manual', 'import'))
   - Default values

3. **Relationships**
   - Foreign keys properly defined
   - One-to-many relationships
   - Many-to-many relationships (through association tables)
   - One-to-one relationships
   - Cascade behavior (delete, update)

4. **Enums**
   - UserStatus enum (unknown, guest, verified, member)
   - VaultFileStatus enum (active, archived, deleted)
   - ReminderStatus, UrgencyLevel, etc.

5. **Model Methods**
   - `__repr__()` methods work correctly
   - `to_dict()` methods (if defined)
   - Custom model methods

### Module 0 Test Breakdown

#### tests/unit/models/test_user_model.py (15 tests)

| # | Test Name | What It Tests |
|---|-----------|---------------|
| 1 | test_user_model_table_name | Table name is 'users' |
| 2 | test_user_model_all_columns_exist | All columns present in schema |
| 3 | test_user_email_column_type | email is String type |
| 4 | test_user_phone_column_type | phone is String type |
| 5 | test_user_password_column_type | password is String type |
| 6 | test_user_status_column_enum | status is UserStatus enum |
| 7 | test_user_email_unique_constraint | email has UNIQUE constraint |
| 8 | test_user_phone_unique_constraint | phone has UNIQUE constraint |
| 9 | test_user_email_nullable_false | email NOT NULL |
| 10 | test_user_otp_nullable_true | otp can be NULL |
| 11 | test_user_relationships_defined | All relationships exist |
| 12 | test_user_profile_relationship | user.profile relationship |
| 13 | test_user_contacts_relationship | user.contacts relationship |
| 14 | test_user_repr_method | __repr__() works |
| 15 | test_user_to_dict_method | to_dict() works (if exists) |

#### tests/unit/models/test_contact_model.py (12 tests)

| # | Test Name | What It Tests |
|---|-----------|---------------|
| 16 | test_contact_model_table_name | Table 'contacts' |
| 17 | test_contact_all_columns_exist | All columns present |
| 18 | test_contact_first_name_column | first_name String |
| 19 | test_contact_owner_user_id_foreign_key | FK to users table |
| 20 | test_contact_linked_user_id_foreign_key | FK to users (nullable) |
| 21 | test_contact_emails_json_column | emails JSON type |
| 22 | test_contact_phone_numbers_json_column | phone_numbers JSON type |
| 23 | test_contact_is_emergency_default_false | Default false |
| 24 | test_contact_owner_relationship | contact.owner relationship |
| 25 | test_contact_linked_user_relationship | contact.linked_user relationship |
| 26 | test_contact_repr_method | __repr__() works |
| 27 | test_contact_cascade_delete | ON DELETE CASCADE configured |

#### tests/unit/models/test_vault_file_model.py (15 tests)

| # | Test Name | What It Tests |
|---|-----------|---------------|
| 28 | test_vault_file_table_name | Table 'vault_files' |
| 29 | test_vault_file_all_columns_exist | All columns present |
| 30 | test_vault_file_encrypted_dek_column | encrypted_dek Text type |
| 31 | test_vault_file_encrypted_form_data_column | encrypted_form_data Text type |
| 32 | test_vault_file_nonce_form_data_column | nonce_form_data String |
| 33 | test_vault_file_owner_user_id_foreign_key | FK to users |
| 34 | test_vault_file_template_id_column | template_id String |
| 35 | test_vault_file_creation_mode_check_constraint | CHECK ('manual', 'import') |
| 36 | test_vault_file_status_enum | status Enum type |
| 37 | test_vault_file_has_source_file_default | Default false |
| 38 | test_vault_file_owner_relationship | vault.owner relationship |
| 39 | test_vault_file_access_list_relationship | vault.access_list relationship |
| 40 | test_vault_file_timestamps | created_at, updated_at |
| 41 | test_vault_file_repr_method | __repr__() works |
| 42 | test_vault_file_cascade_delete | Cascade configured |

#### tests/unit/models/test_folder_model.py (12 tests)

| # | Test Name | What It Tests |
|---|-----------|---------------|
| 43 | test_folder_table_name | Table 'folders' |
| 44 | test_folder_all_columns_exist | All columns present |
| 45 | test_folder_name_column | name String |
| 46 | test_folder_user_id_foreign_key | FK to users |
| 47 | test_folder_user_relationship | folder.user relationship |
| 48 | test_folder_branches_relationship | folder.branches relationship |
| 49 | test_folder_leaves_relationship | folder.leaves relationship |
| 50 | test_folder_trigger_relationship | folder.trigger (one-to-one) |
| 51 | test_folder_files_relationship | folder.files relationship |
| 52 | test_folder_timestamps | created_at, updated_at |
| 53 | test_folder_repr_method | __repr__() works |
| 54 | test_folder_cascade_delete | Cascade configured |

#### tests/unit/models/test_memory_collection_model.py (12 tests)

| # | Test Name | What It Tests |
|---|-----------|---------------|
| 55 | test_memory_collection_table_name | Table 'memory_collections' |
| 56 | test_memory_collection_all_columns_exist | All columns present |
| 57 | test_memory_collection_user_id_foreign_key | FK to users |
| 58 | test_memory_collection_event_type_enum | event_type Enum |
| 59 | test_memory_collection_scheduled_at_nullable | scheduled_at nullable |
| 60 | test_memory_collection_is_armed_default | Default false |
| 61 | test_memory_collection_user_relationship | memory.user relationship |
| 62 | test_memory_collection_files_relationship | memory.files relationship |
| 63 | test_memory_collection_assignments_relationship | memory.assignments relationship |
| 64 | test_memory_collection_timestamps | created_at, updated_at |
| 65 | test_memory_collection_repr_method | __repr__() works |
| 66 | test_memory_collection_cascade_delete | Cascade configured |

#### tests/unit/models/test_death_declaration_model.py (15 tests)

| # | Test Name | What It Tests |
|---|-----------|---------------|
| 67 | test_death_declaration_table_name | Table 'death_declarations' |
| 68 | test_death_declaration_all_columns_exist | All columns present |
| 69 | test_death_declaration_root_user_id_foreign_key | FK to users (root_user) |
| 70 | test_death_declaration_declarer_user_id_foreign_key | FK to users (declarer) |
| 71 | test_death_declaration_type_enum | type Enum (soft/hard) |
| 72 | test_death_declaration_state_enum | state Enum |
| 73 | test_death_declaration_message_nullable | message nullable |
| 74 | test_death_declaration_evidence_file_url_nullable | evidence nullable |
| 75 | test_death_declaration_root_user_relationship | death.root_user relationship |
| 76 | test_death_declaration_declarer_relationship | death.declarer relationship |
| 77 | test_death_declaration_approvals_relationship | death.approvals relationship |
| 78 | test_death_declaration_broadcasts_relationship | death.broadcasts relationship |
| 79 | test_death_declaration_timestamps | created_at, updated_at |
| 80 | test_death_declaration_repr_method | __repr__() works |
| 81 | test_death_declaration_cascade_delete | Cascade configured |

#### tests/unit/models/test_trustee_model.py (10 tests)

| # | Test Name | What It Tests |
|---|-----------|---------------|
| 82 | test_trustee_table_name | Table 'trustees' |
| 83 | test_trustee_all_columns_exist | All columns present |
| 84 | test_trustee_user_id_foreign_key | FK to users |
| 85 | test_trustee_contact_id_foreign_key | FK to contacts |
| 86 | test_trustee_status_enum | status Enum |
| 87 | test_trustee_is_primary_default_false | Default false |
| 88 | test_trustee_version_column | version Integer |
| 89 | test_trustee_unique_constraint | UNIQUE (user_id, contact_id) |
| 90 | test_trustee_repr_method | __repr__() works |
| 91 | test_trustee_cascade_delete | Cascade configured |

#### tests/unit/models/test_category_model.py (10 tests)

| # | Test Name | What It Tests |
|---|-----------|---------------|
| 92 | test_category_table_name | Table 'categories' |
| 93 | test_category_all_columns_exist | All columns present |
| 94 | test_category_name_column_unique | name UNIQUE |
| 95 | test_category_description_nullable | description nullable |
| 96 | test_category_display_order_column | display_order Integer |
| 97 | test_category_sections_relationship | category.sections relationship |
| 98 | test_category_timestamps | created_at, updated_at |
| 99 | test_category_repr_method | __repr__() works |
| 100 | test_category_cascade_delete_sections | Cascade to sections |
| 101 | test_category_name_not_nullable | name NOT NULL |

#### tests/unit/models/test_section_model.py (10 tests)

| # | Test Name | What It Tests |
|---|-----------|---------------|
| 102 | test_section_table_name | Table 'sections' |
| 103 | test_section_all_columns_exist | All columns present |
| 104 | test_section_category_id_foreign_key | FK to categories |
| 105 | test_section_name_column | name String |
| 106 | test_section_allows_file_import_default | Default false |
| 107 | test_section_display_order_column | display_order Integer |
| 108 | test_section_category_relationship | section.category relationship |
| 109 | test_section_steps_relationship | section.steps relationship |
| 110 | test_section_repr_method | __repr__() works |
| 111 | test_section_cascade_delete | Cascade configured |

#### tests/unit/models/test_step_model.py (12 tests)

| # | Test Name | What It Tests |
|---|-----------|---------------|
| 112 | test_step_table_name | Table 'steps' |
| 113 | test_step_all_columns_exist | All columns present |
| 114 | test_step_section_id_foreign_key | FK to sections |
| 115 | test_step_label_column | label String |
| 116 | test_step_type_enum | type Enum (text/date/dropdown/file/multiselect) |
| 117 | test_step_is_required_default_false | Default false |
| 118 | test_step_display_order_column | display_order Integer |
| 119 | test_step_section_relationship | step.section relationship |
| 120 | test_step_options_relationship | step.options relationship |
| 121 | test_step_user_answers_relationship | step.user_answers relationship |
| 122 | test_step_repr_method | __repr__() works |
| 123 | test_step_cascade_delete | Cascade configured |

#### tests/unit/models/test_reminder_model.py (10 tests)

| # | Test Name | What It Tests |
|---|-----------|---------------|
| 124 | test_reminder_table_name | Table 'reminders' |
| 125 | test_reminder_all_columns_exist | All columns present |
| 126 | test_reminder_user_id_foreign_key | FK to users |
| 127 | test_reminder_vault_file_id_foreign_key | FK to vault_files |
| 128 | test_reminder_reminder_date_column | reminder_date DateTime |
| 129 | test_reminder_status_enum | status Enum |
| 130 | test_reminder_urgency_level_enum | urgency Enum |
| 131 | test_reminder_user_relationship | reminder.user relationship |
| 132 | test_reminder_vault_file_relationship | reminder.vault_file relationship |
| 133 | test_reminder_repr_method | __repr__() works |

#### tests/unit/models/test_admin_model.py (8 tests)

| # | Test Name | What It Tests |
|---|-----------|---------------|
| 134 | test_admin_table_name | Table 'admins' |
| 135 | test_admin_all_columns_exist | All columns present |
| 136 | test_admin_username_unique | username UNIQUE |
| 137 | test_admin_email_unique | email UNIQUE |
| 138 | test_admin_password_column | password String |
| 139 | test_admin_otp_nullable | otp nullable |
| 140 | test_admin_repr_method | __repr__() works |
| 141 | test_admin_to_dict_method | to_dict() works |

#### tests/unit/models/test_relationship_models.py (15 tests)

| # | Test Name | What It Tests |
|---|-----------|---------------|
| 142 | test_folder_branch_table_name | Table 'folder_branches' |
| 143 | test_folder_branch_unique_constraint | UNIQUE (folder_id, contact_id) |
| 144 | test_folder_leaf_table_name | Table 'folder_leaves' |
| 145 | test_folder_leaf_unique_constraint | UNIQUE (folder_id, contact_id, role) |
| 146 | test_leaf_assignment_table_name | Table 'leaf_assignments' |
| 147 | test_leaf_assignment_unique_constraint | UNIQUE (contact_id, section_id) |
| 148 | test_memory_assignment_table_name | Table 'memory_assignments' |
| 149 | test_memory_assignment_unique_constraint | UNIQUE (collection_id, contact_id, role) |
| 150 | test_vault_access_table_name | Table 'vault_file_access' |
| 151 | test_vault_access_status_enum | status Enum |
| 152 | test_death_approval_table_name | Table 'death_approvals' |
| 153 | test_death_approval_status_enum | status Enum |
| 154 | test_all_relationship_tables_have_timestamps | Timestamps present |
| 155 | test_all_relationship_tables_have_foreign_keys | FKs defined |
| 156 | test_all_relationship_tables_cascade_delete | Cascade configured |

**Module 0 Total: 156 tests**

---

## 📦 Remaining Modules Summary

*(Detailed breakdown continues with Modules 1-12, E2E, and Specialized tests as previously specified)*

### Module 1: Foundation - Database Operations (117 tests)
- Database transactions, config, security core, dependencies
- Already have 15 tests created in `test_database_models.py`
- Need 102 more tests

### Module 2-12: Continue as specified in original plan
- Total: 1,372 remaining tests after ORM
- Build incrementally, 15-20 tests at a time

---

## 🚀 Execution Strategy

### Phase 1: ORM Models (CURRENT PRIORITY)
✅ **Build 156 ORM tests FIRST**
- Validates SQLAlchemy model definitions
- Ensures schema correctness
- Foundation for all other tests

### Phase 2: Foundation Operations
- Database transactions, config, security
- Complete remaining 102 tests

### Phase 3: Core Modules (Modules 2-12)
- Build 15-20 tests at a time
- Test locally after each batch
- Commit and push successful batches

### Phase 4: E2E & Specialized
- User journeys, workflows
- Security, performance, concurrency, regression

---

## ✅ Current Progress

- **ORM Tests:** 0/156 (0%)
- **Foundation Operations:** 15/102 (14.7%)
- **Total:** 15/1,644 (0.9%)

---

## 📝 Next Steps

1. **Create all 13 ORM model test files** (156 tests)
2. **Test ORM batch locally**
3. **Commit and push ORM tests**
4. **Complete Foundation module** (102 tests)
5. **Continue with remaining modules**

---

**Document Version:** 2.0
**Last Updated:** 2025-10-28
**Status:** ORM tests prioritized, ready to implement
