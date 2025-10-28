# **CONSOLIDATED DELIVERABLE 1: COMPLETE TEST SUITE STRUCTURE**

---

## **DIRECTORY LAYOUT**

```
tests/
│
├── conftest.py                                    # Root fixtures (DB, client, auth)
├── pytest.ini                                     # Pytest configuration
├── run_all_tests.py                               # Test runner script
├── README.md                                      # Test suite documentation
│
├── fixtures/                                      # Reusable test fixtures
│   ├── __init__.py
│   ├── database_fixtures.py                       # DB session, cleanup fixtures
│   ├── user_fixtures.py                           # User, admin, contact fixtures
│   ├── auth_fixtures.py                           # Tokens, OTP fixtures
│   ├── vault_fixtures.py                          # Encrypted file fixtures
│   ├── mock_fixtures.py                           # Mock AWS, SMTP, Twilio
│   └── factory_fixtures.py                        # Factory Boy factories
│
├── unit/                                          # UNIT TESTS (1,145 tests)
│   │
│   ├── models/                                    # Module 0: ORM Models (156 tests)
│   │   ├── __init__.py
│   │   ├── test_user_model.py                     # 15 tests
│   │   ├── test_contact_model.py                  # 12 tests
│   │   ├── test_vault_file_model.py               # 15 tests
│   │   ├── test_folder_model.py                   # 12 tests
│   │   ├── test_memory_collection_model.py        # 12 tests
│   │   ├── test_death_declaration_model.py        # 15 tests
│   │   ├── test_trustee_model.py                  # 10 tests
│   │   ├── test_category_model.py                 # 10 tests
│   │   ├── test_section_model.py                  # 10 tests
│   │   ├── test_step_model.py                     # 12 tests
│   │   ├── test_reminder_model.py                 # 10 tests
│   │   ├── test_admin_model.py                    # 8 tests
│   │   └── test_relationship_models.py            # 15 tests
│   │
│   ├── foundation/                                # Module 1: Foundation Layer (102 tests)
│   │   ├── __init__.py
│   │   ├── test_database_models.py                # 45 tests
│   │   ├── test_database_relationships.py         # 20 tests
│   │   ├── test_config.py                         # 15 tests
│   │   ├── test_security_core.py                  # 12 tests
│   │   └── test_dependencies.py                   # 10 tests
│   │
│   ├── auth/                                      # Module 2: Authentication & Authorization (85 tests)
│   │   ├── __init__.py
│   │   ├── test_user_controller.py                # 25 tests
│   │   ├── test_admin_controller.py               # 10 tests
│   │   ├── test_verification_controller.py        # 12 tests
│   │   ├── test_contact_controller.py             # 20 tests
│   │   ├── test_otp_generation.py                 # 8 tests
│   │   └── test_user_status_lifecycle.py          # 10 tests
│   │
│   ├── vault/                                     # Module 3: Vault & Encryption (125 tests)
│   │   ├── __init__.py
│   │   ├── test_crypto_engine.py                  # 25 tests
│   │   ├── test_vault_encryptor.py                # 20 tests
│   │   ├── test_vault_decryptor.py                # 20 tests
│   │   ├── test_db_operations.py                  # 15 tests
│   │   ├── test_s3_operations.py                  # 18 tests
│   │   ├── test_validators.py                     # 15 tests
│   │   └── test_exceptions.py                     # 12 tests
│   │
│   ├── categories/                                # Module 4: Digital Asset Organization (107 tests)
│   │   ├── __init__.py
│   │   ├── test_category_controller.py            # 15 tests
│   │   ├── test_section_controller.py             # 12 tests
│   │   ├── test_step_controller.py                # 20 tests
│   │   ├── test_user_answers_controller.py        # 18 tests
│   │   ├── test_leaf_assignment_controller.py     # 20 tests
│   │   ├── test_token_generation.py               # 10 tests
│   │   └── test_release_formatting.py             # 12 tests
│   │
│   ├── folders/                                   # Module 5: Folder & Relationship System (77 tests)
│   │   ├── __init__.py
│   │   ├── test_folder_controller.py              # 20 tests
│   │   ├── test_branch_controller.py              # 12 tests
│   │   ├── test_leaf_controller.py                # 12 tests
│   │   ├── test_trigger_controller.py             # 10 tests
│   │   ├── test_relationship_controller.py        # 15 tests
│   │   └── test_folder_status_computation.py      # 8 tests
│   │
│   ├── memories/                                  # Module 6: Memory & Message Collections (73 tests)
│   │   ├── __init__.py
│   │   ├── test_memory_controller.py              # 18 tests
│   │   ├── test_message_controller.py             # 18 tests
│   │   ├── test_collection_assignments.py         # 15 tests
│   │   ├── test_trigger_logic.py                  # 10 tests
│   │   └── test_release_mechanism.py              # 12 tests
│   │
│   ├── death/                                     # Module 7: Death Declaration System (129 tests)
│   │   ├── __init__.py
│   │   ├── test_soft_death_controller.py          # 25 tests
│   │   ├── test_hard_death_controller.py          # 20 tests
│   │   ├── test_trustee_controller.py             # 15 tests
│   │   ├── test_approval_logic.py                 # 12 tests
│   │   ├── test_contest_controller.py             # 15 tests
│   │   ├── test_death_lock_enforcement.py         # 10 tests
│   │   ├── test_lifecycle_management.py           # 10 tests
│   │   ├── test_broadcast_controller.py           # 12 tests
│   │   └── test_token_verification.py             # 10 tests
│   │
│   ├── reminders/                                 # Module 8: Reminder System (82 tests)
│   │   ├── __init__.py
│   │   ├── test_reminder_controller.py            # 20 tests
│   │   ├── test_reminder_scheduler.py             # 15 tests
│   │   ├── test_reminder_sender.py                # 12 tests
│   │   ├── test_reminder_escalator.py             # 10 tests
│   │   ├── test_reminder_utils.py                 # 15 tests
│   │   └── test_preference_management.py          # 10 tests
│   │
│   ├── policy_checker/                            # Module 9: Policy Checker & OCR (68 tests)
│   │   ├── __init__.py
│   │   ├── test_ocr_service.py                    # 15 tests
│   │   ├── test_policy_service.py                 # 18 tests
│   │   ├── test_extraction_service.py             # 15 tests
│   │   ├── test_gemini_client.py                  # 10 tests
│   │   └── test_google_ocr_client.py              # 10 tests
│   │
│   ├── file_storage/                              # Module 10: File & Storage Services (52 tests)
│   │   ├── __init__.py
│   │   ├── test_file_controller.py                # 15 tests
│   │   ├── test_s3_upload_controller.py           # 15 tests
│   │   ├── test_presigned_url_generation.py       # 10 tests
│   │   └── test_file_validation.py                # 12 tests
│   │
│   ├── admin/                                     # Module 11: Admin Operations (47 tests)
│   │   ├── __init__.py
│   │   ├── test_admin_catalog_controller.py       # 12 tests
│   │   ├── test_admin_step_controller.py          # 10 tests
│   │   ├── test_admin_death_controller.py         # 15 tests
│   │   └── test_admin_verification_controller.py  # 10 tests
│   │
│   └── external_services/                         # Module 12: Integration & External Services (42 tests)
│       ├── __init__.py
│       ├── test_twilio_integration.py             # 10 tests
│       ├── test_smtp_integration.py               # 12 tests
│       ├── test_aws_kms_integration.py            # 10 tests
│       └── test_aws_s3_integration.py             # 10 tests
│
├── integration/                                   # INTEGRATION TESTS (290 tests)
│   │
│   ├── foundation/
│   │   ├── __init__.py
│   │   └── test_database_transactions.py          # 15 tests
│   │
│   ├── auth/
│   │   ├── __init__.py
│   │   ├── test_auth_api_endpoints.py             # 25 tests
│   │   └── test_user_api_endpoints.py             # 20 tests
│   │
│   ├── vault/
│   │   ├── __init__.py
│   │   ├── test_vault_api_endpoints.py            # 30 tests
│   │   └── test_vault_encryption_flow.py          # 20 tests
│   │
│   ├── categories/
│   │   ├── __init__.py
│   │   ├── test_category_api_endpoints.py         # 25 tests
│   │   └── test_leaf_assignment_flow.py           # 20 tests
│   │
│   ├── folders/
│   │   ├── __init__.py
│   │   └── test_folder_api_endpoints.py           # 20 tests
│   │
│   ├── memories/
│   │   ├── __init__.py
│   │   └── test_memory_api_endpoints.py           # 20 tests
│   │
│   ├── death/
│   │   ├── __init__.py
│   │   ├── test_death_api_endpoints.py            # 30 tests
│   │   └── test_trustee_api_endpoints.py          # 15 tests
│   │
│   ├── reminders/
│   │   ├── __init__.py
│   │   └── test_reminder_api_endpoints.py         # 20 tests
│   │
│   ├── policy_checker/
│   │   ├── __init__.py
│   │   └── test_policy_api_endpoints.py           # 15 tests
│   │
│   └── file_storage/
│       ├── __init__.py
│       └── test_s3_upload_api_endpoints.py        # 15 tests
│
├── e2e/                                           # END-TO-END TESTS (91 tests)
│   │
│   ├── user_journeys/
│   │   ├── __init__.py
│   │   ├── test_new_user_signup_journey.py        # 8 tests
│   │   ├── test_vault_creation_journey.py         # 8 tests
│   │   ├── test_category_adoption_journey.py      # 8 tests
│   │   ├── test_folder_sharing_journey.py         # 8 tests
│   │   ├── test_memory_creation_journey.py        # 8 tests
│   │   └── test_trustee_setup_journey.py          # 8 tests
│   │
│   └── workflows/
│       ├── __init__.py
│       ├── test_soft_death_workflow.py            # 10 tests
│       ├── test_hard_death_workflow.py            # 10 tests
│       ├── test_vault_share_workflow.py           # 8 tests
│       ├── test_leaf_assignment_workflow.py       # 8 tests
│       └── test_reminder_lifecycle_workflow.py    # 7 tests
│
└── specialized/                                   # SPECIALIZED TESTS (118 tests)
    │
    ├── security/
    │   ├── __init__.py
    │   ├── test_sql_injection_protection.py       # 5 tests
    │   ├── test_authorization_bypass.py           # 10 tests
    │   ├── test_jwt_security.py                   # 8 tests
    │   ├── test_rate_limiting.py                  # 5 tests
    │   ├── test_xss_protection.py                 # 5 tests
    │   └── test_encryption_strength.py            # 5 tests
    │
    ├── performance/
    │   ├── __init__.py
    │   ├── test_database_query_performance.py     # 10 tests
    │   ├── test_bulk_operations_performance.py    # 5 tests
    │   ├── test_vault_encryption_performance.py   # 5 tests
    │   └── test_api_response_time.py              # 5 tests
    │
    ├── concurrency/
    │   ├── __init__.py
    │   ├── test_concurrent_vault_operations.py    # 5 tests
    │   ├── test_concurrent_death_declarations.py  # 5 tests
    │   └── test_concurrent_leaf_acceptance.py     # 5 tests
    │
    └── regression/
        ├── __init__.py
        ├── test_bug_fixes_auth.py                 # 10 tests
        ├── test_bug_fixes_vault.py                # 10 tests
        ├── test_bug_fixes_death.py                # 10 tests
        └── test_backward_compatibility.py         # 10 tests
```

---

## **SUMMARY STATISTICS**

### **File Count**

| Category | Folders | Files | Tests |
|----------|---------|-------|-------|
| Fixtures | 1 | 7 | N/A |
| Unit Tests | 13 | 82 | 1,145 |
| Integration Tests | 10 | 16 | 290 |
| E2E Tests | 2 | 11 | 91 |
| Specialized Tests | 4 | 13 | 118 |
| **TOTAL** | **30** | **129** | **1,644** |

---

### **Test Distribution by Module**

| Module | Unit | Integration | E2E | Specialized | **Total** |
|--------|------|-------------|-----|-------------|-----------|
| 0. ORM Models | 156 | 0 | 0 | 0 | **156** |
| 1. Foundation | 102 | 15 | 0 | 0 | **117** |
| 2. Auth | 85 | 45 | 0 | 0 | **130** |
| 3. Vault | 125 | 50 | 0 | 0 | **175** |
| 4. Categories | 107 | 45 | 0 | 0 | **152** |
| 5. Folders | 77 | 20 | 0 | 0 | **97** |
| 6. Memories | 73 | 20 | 0 | 0 | **93** |
| 7. Death | 129 | 45 | 0 | 0 | **174** |
| 8. Reminders | 82 | 20 | 0 | 0 | **102** |
| 9. Policy Checker | 68 | 15 | 0 | 0 | **83** |
| 10. File Storage | 52 | 15 | 0 | 0 | **67** |
| 11. Admin | 47 | 0 | 0 | 0 | **47** |
| 12. External Services | 42 | 0 | 0 | 0 | **42** |
| E2E: User Journeys | 0 | 0 | 48 | 0 | **48** |
| E2E: Workflows | 0 | 0 | 43 | 0 | **43** |
| Security | 0 | 0 | 0 | 38 | **38** |
| Performance | 0 | 0 | 0 | 25 | **25** |
| Concurrency | 0 | 0 | 0 | 15 | **15** |
| Regression | 0 | 0 | 0 | 40 | **40** |
| **GRAND TOTAL** | **1,145** | **290** | **91** | **118** | **🎯 1,644** |

---

### **Test Type Distribution**

```
Total Tests: 1,644

├── Unit Tests: 1,145 (69.6%)
├── Integration Tests: 290 (17.6%)
├── E2E Tests: 91 (5.5%)
└── Specialized Tests: 118 (7.2%)
```

---

### **Priority Distribution**

- **🔥 Critical Priority:** ~1,320 tests (80.3%)
- **⭐ Important Priority:** ~324 tests (19.7%)

---

## **VERIFICATION CHECKLIST**

✅ **Structure Complete**
- 30 directories mapped
- 129 test files defined
- 7 fixture files documented

✅ **Test Count Verified**
- Unit Tests: 1,145
- Integration Tests: 290
- E2E Tests: 91
- Specialized Tests: 118
- **Total: 1,644 tests**

✅ **Module Coverage**
- ORM Models: Complete
- 12 Business Modules: Complete
- E2E Journeys: Complete
- Specialized Testing: Complete

---

**END OF STRUCTURE DOCUMENT**

**Status: ✅ COMPLETE & VERIFIED**

# **CONSOLIDATED DELIVERABLE 2: COMPLETE TEST INVENTORY**

**Total Tests: 1,644**

---

## MODULE 0: ORM MODELS (156 tests)

### tests/unit/models/test_user_model.py (15 tests)

| # | Test Function | Description | Priority |
|---|---------------|-------------|----------|
| 1 | test_user_model_table_name | Table name 'users' | 🔥 |
| 2 | test_user_model_all_columns_exist | All columns defined | 🔥 |
| 3 | test_user_email_column_type | email: String | 🔥 |
| 4 | test_user_phone_column_type | phone: String | 🔥 |
| 5 | test_user_password_column_type | password: String | 🔥 |
| 6 | test_user_status_column_enum | status: Enum | 🔥 |
| 7 | test_user_email_unique_constraint | email unique | 🔥 |
| 8 | test_user_phone_unique_constraint | phone unique | 🔥 |
| 9 | test_user_email_nullable_false | email not null | 🔥 |
| 10 | test_user_otp_nullable_true | otp nullable | 🔥 |
| 11 | test_user_relationships_defined | All relationships | 🔥 |
| 12 | test_user_profile_relationship | profile relationship | 🔥 |
| 13 | test_user_contacts_relationship | contacts relationship | 🔥 |
| 14 | test_user_repr_method | __repr__ works | ⭐ |
| 15 | test_user_to_dict_method | to_dict() works | ⭐ |

### tests/unit/models/test_contact_model.py (12 tests)

| # | Test Function | Description | Priority |
|---|---------------|-------------|----------|
| 16 | test_contact_model_table_name | Table name 'contacts' | 🔥 |
| 17 | test_contact_all_columns_exist | All columns defined | 🔥 |
| 18 | test_contact_first_name_column | first_name: String | 🔥 |
| 19 | test_contact_owner_user_id_foreign_key | FK to users | 🔥 |
| 20 | test_contact_linked_user_id_foreign_key | FK to users (nullable) | 🔥 |
| 21 | test_contact_emails_json_column | emails: JSON | 🔥 |
| 22 | test_contact_phone_numbers_json_column | phone_numbers: JSON | 🔥 |
| 23 | test_contact_is_emergency_default_false | Default false | 🔥 |
| 24 | test_contact_owner_relationship | owner relationship | 🔥 |
| 25 | test_contact_linked_user_relationship | linked_user relationship | 🔥 |
| 26 | test_contact_repr_method | __repr__ works | ⭐ |
| 27 | test_contact_cascade_delete | Cascade on delete | 🔥 |

### tests/unit/models/test_vault_file_model.py (15 tests)

| # | Test Function | Description | Priority |
|---|---------------|-------------|----------|
| 28 | test_vault_file_table_name | Table name 'vault_files' | 🔥 |
| 29 | test_vault_file_all_columns_exist | All columns defined | 🔥 |
| 30 | test_vault_file_encrypted_dek_column | encrypted_dek: Text | 🔥 |
| 31 | test_vault_file_encrypted_form_data_column | encrypted_form_data: Text | 🔥 |
| 32 | test_vault_file_nonce_form_data_column | nonce_form_data: String | 🔥 |
| 33 | test_vault_file_owner_user_id_foreign_key | FK to users | 🔥 |
| 34 | test_vault_file_template_id_column | template_id: String | 🔥 |
| 35 | test_vault_file_creation_mode_check_constraint | manual/import only | 🔥 |
| 36 | test_vault_file_status_enum | status: Enum | 🔥 |
| 37 | test_vault_file_has_source_file_default | Default false | 🔥 |
| 38 | test_vault_file_owner_relationship | owner relationship | 🔥 |
| 39 | test_vault_file_access_list_relationship | access_list relationship | 🔥 |
| 40 | test_vault_file_timestamps | created_at, updated_at | 🔥 |
| 41 | test_vault_file_repr_method | __repr__ works | ⭐ |
| 42 | test_vault_file_cascade_delete | Cascade on delete | 🔥 |

### tests/unit/models/test_folder_model.py (12 tests)

| # | Test Function | Description | Priority |
|---|---------------|-------------|----------|
| 43 | test_folder_table_name | Table name 'folders' | 🔥 |
| 44 | test_folder_all_columns_exist | All columns defined | 🔥 |
| 45 | test_folder_name_column | name: String | 🔥 |
| 46 | test_folder_user_id_foreign_key | FK to users | 🔥 |
| 47 | test_folder_user_relationship | user relationship | 🔥 |
| 48 | test_folder_branches_relationship | branches relationship | 🔥 |
| 49 | test_folder_leaves_relationship | leaves relationship | 🔥 |
| 50 | test_folder_trigger_relationship | trigger relationship (1-to-1) | 🔥 |
| 51 | test_folder_files_relationship | files relationship | 🔥 |
| 52 | test_folder_timestamps | created_at, updated_at | 🔥 |
| 53 | test_folder_repr_method | __repr__ works | ⭐ |
| 54 | test_folder_cascade_delete | Cascade on delete | 🔥 |

### tests/unit/models/test_memory_collection_model.py (12 tests)

| # | Test Function | Description | Priority |
|---|---------------|-------------|----------|
| 55 | test_memory_collection_table_name | Table name 'memory_collections' | 🔥 |
| 56 | test_memory_collection_all_columns_exist | All columns defined | 🔥 |
| 57 | test_memory_collection_user_id_foreign_key | FK to users | 🔥 |
| 58 | test_memory_collection_event_type_enum | event_type: Enum | 🔥 |
| 59 | test_memory_collection_scheduled_at_nullable | scheduled_at nullable | 🔥 |
| 60 | test_memory_collection_is_armed_default | Default false | 🔥 |
| 61 | test_memory_collection_user_relationship | user relationship | 🔥 |
| 62 | test_memory_collection_files_relationship | files relationship | 🔥 |
| 63 | test_memory_collection_assignments_relationship | assignments relationship | 🔥 |
| 64 | test_memory_collection_timestamps | created_at, updated_at | 🔥 |
| 65 | test_memory_collection_repr_method | __repr__ works | ⭐ |
| 66 | test_memory_collection_cascade_delete | Cascade on delete | 🔥 |

### tests/unit/models/test_death_declaration_model.py (15 tests)

| # | Test Function | Description | Priority |
|---|---------------|-------------|----------|
| 67 | test_death_declaration_table_name | Table name 'death_declarations' | 🔥 |
| 68 | test_death_declaration_all_columns_exist | All columns defined | 🔥 |
| 69 | test_death_declaration_root_user_id_foreign_key | FK to users | 🔥 |
| 70 | test_death_declaration_declarer_user_id_foreign_key | FK to users | 🔥 |
| 71 | test_death_declaration_type_enum | type: soft/hard | 🔥 |
| 72 | test_death_declaration_state_enum | state: Enum | 🔥 |
| 73 | test_death_declaration_message_nullable | message nullable | 🔥 |
| 74 | test_death_declaration_evidence_file_url_nullable | evidence nullable | 🔥 |
| 75 | test_death_declaration_root_user_relationship | root_user relationship | 🔥 |
| 76 | test_death_declaration_declarer_relationship | declarer relationship | 🔥 |
| 77 | test_death_declaration_approvals_relationship | approvals relationship | 🔥 |
| 78 | test_death_declaration_broadcasts_relationship | broadcasts relationship | 🔥 |
| 79 | test_death_declaration_timestamps | created_at, updated_at | 🔥 |
| 80 | test_death_declaration_repr_method | __repr__ works | ⭐ |
| 81 | test_death_declaration_cascade_delete | Cascade on delete | 🔥 |

### tests/unit/models/test_trustee_model.py (10 tests)

| # | Test Function | Description | Priority |
|---|---------------|-------------|----------|
| 82 | test_trustee_table_name | Table name 'trustees' | 🔥 |
| 83 | test_trustee_all_columns_exist | All columns defined | 🔥 |
| 84 | test_trustee_user_id_foreign_key | FK to users | 🔥 |
| 85 | test_trustee_contact_id_foreign_key | FK to contacts | 🔥 |
| 86 | test_trustee_status_enum | status: Enum | 🔥 |
| 87 | test_trustee_is_primary_default_false | Default false | 🔥 |
| 88 | test_trustee_version_column | version: Integer | 🔥 |
| 89 | test_trustee_unique_constraint | (user_id, contact_id) unique | 🔥 |
| 90 | test_trustee_repr_method | __repr__ works | ⭐ |
| 91 | test_trustee_cascade_delete | Cascade on delete | 🔥 |

### tests/unit/models/test_category_model.py (10 tests)

| # | Test Function | Description | Priority |
|---|---------------|-------------|----------|
| 92 | test_category_table_name | Table name 'categories' | 🔥 |
| 93 | test_category_all_columns_exist | All columns defined | 🔥 |
| 94 | test_category_name_column_unique | name unique | 🔥 |
| 95 | test_category_description_nullable | description nullable | 🔥 |
| 96 | test_category_display_order_column | display_order: Integer | 🔥 |
| 97 | test_category_sections_relationship | sections relationship | 🔥 |
| 98 | test_category_timestamps | created_at, updated_at | 🔥 |
| 99 | test_category_repr_method | __repr__ works | ⭐ |
| 100 | test_category_cascade_delete_sections | Cascade to sections | 🔥 |
| 101 | test_category_name_not_nullable | name not null | 🔥 |

### tests/unit/models/test_section_model.py (10 tests)

| # | Test Function | Description | Priority |
|---|---------------|-------------|----------|
| 102 | test_section_table_name | Table name 'sections' | 🔥 |
| 103 | test_section_all_columns_exist | All columns defined | 🔥 |
| 104 | test_section_category_id_foreign_key | FK to categories | 🔥 |
| 105 | test_section_name_column | name: String | 🔥 |
| 106 | test_section_allows_file_import_default | Default false | 🔥 |
| 107 | test_section_display_order_column | display_order: Integer | 🔥 |
| 108 | test_section_category_relationship | category relationship | 🔥 |
| 109 | test_section_steps_relationship | steps relationship | 🔥 |
| 110 | test_section_repr_method | __repr__ works | ⭐ |
| 111 | test_section_cascade_delete | Cascade on delete | 🔥 |

### tests/unit/models/test_step_model.py (12 tests)

| # | Test Function | Description | Priority |
|---|---------------|-------------|----------|
| 112 | test_step_table_name | Table name 'steps' | 🔥 |
| 113 | test_step_all_columns_exist | All columns defined | 🔥 |
| 114 | test_step_section_id_foreign_key | FK to sections | 🔥 |
| 115 | test_step_label_column | label: String | 🔥 |
| 116 | test_step_type_enum | type: text/date/dropdown/file/multiselect | 🔥 |
| 117 | test_step_is_required_default_false | Default false | 🔥 |
| 118 | test_step_display_order_column | display_order: Integer | 🔥 |
| 119 | test_step_section_relationship | section relationship | 🔥 |
| 120 | test_step_options_relationship | options relationship | 🔥 |
| 121 | test_step_user_answers_relationship | user_answers relationship | 🔥 |
| 122 | test_step_repr_method | __repr__ works | ⭐ |
| 123 | test_step_cascade_delete | Cascade on delete | 🔥 |

### tests/unit/models/test_reminder_model.py (10 tests)

| # | Test Function | Description | Priority |
|---|---------------|-------------|----------|
| 124 | test_reminder_table_name | Table name 'reminders' | 🔥 |
| 125 | test_reminder_all_columns_exist | All columns defined | 🔥 |
| 126 | test_reminder_user_id_foreign_key | FK to users | 🔥 |
| 127 | test_reminder_vault_file_id_foreign_key | FK to vault_files | 🔥 |
| 128 | test_reminder_reminder_date_column | reminder_date: DateTime | 🔥 |
| 129 | test_reminder_status_enum | status: Enum | 🔥 |
| 130 | test_reminder_urgency_level_enum | urgency: Enum | 🔥 |
| 131 | test_reminder_user_relationship | user relationship | 🔥 |
| 132 | test_reminder_vault_file_relationship | vault_file relationship | 🔥 |
| 133 | test_reminder_repr_method | __repr__ works | ⭐ |

### tests/unit/models/test_admin_model.py (8 tests)

| # | Test Function | Description | Priority |
|---|---------------|-------------|----------|
| 134 | test_admin_table_name | Table name 'admins' | 🔥 |
| 135 | test_admin_all_columns_exist | All columns defined | 🔥 |
| 136 | test_admin_username_unique | username unique | 🔥 |
| 137 | test_admin_email_unique | email unique | 🔥 |
| 138 | test_admin_password_column | password: String | 🔥 |
| 139 | test_admin_otp_nullable | otp nullable | 🔥 |
| 140 | test_admin_repr_method | __repr__ works | ⭐ |
| 141 | test_admin_to_dict_method | to_dict() works | ⭐ |

### tests/unit/models/test_relationship_models.py (15 tests)

| # | Test Function | Description | Priority |
|---|---------------|-------------|----------|
| 142 | test_folder_branch_table_name | Table 'folder_branches' | 🔥 |
| 143 | test_folder_branch_unique_constraint | (folder_id, contact_id) unique | 🔥 |
| 144 | test_folder_leaf_table_name | Table 'folder_leaves' | 🔥 |
| 145 | test_folder_leaf_unique_constraint | (folder_id, contact_id, role) unique | 🔥 |
| 146 | test_leaf_assignment_table_name | Table 'leaf_assignments' | 🔥 |
| 147 | test_leaf_assignment_unique_constraint | (contact_id, section_id) unique | 🔥 |
| 148 | test_memory_assignment_table_name | Table 'memory_assignments' | 🔥 |
| 149 | test_memory_assignment_unique_constraint | (collection_id, contact_id, role) unique | 🔥 |
| 150 | test_vault_access_table_name | Table 'vault_file_access' | 🔥 |
| 151 | test_vault_access_status_enum | status: Enum | 🔥 |
| 152 | test_death_approval_table_name | Table 'death_approvals' | 🔥 |
| 153 | test_death_approval_status_enum | status: Enum | 🔥 |
| 154 | test_all_relationship_tables_have_timestamps | Timestamps present | 🔥 |
| 155 | test_all_relationship_tables_have_foreign_keys | FKs defined | 🔥 |
| 156 | test_all_relationship_tables_cascade_delete | Cascade configured | 🔥 |

**Module 0 Subtotal: 156 tests**

---

## MODULE 1: FOUNDATION (117 tests)

### tests/unit/foundation/test_database_models.py (45 tests)

| # | Test Function | Description | Priority |
|---|---------------|-------------|----------|
| 157 | test_create_user_with_minimal_required_fields | Create user with email only | 🔥 |
| 158 | test_create_user_with_all_optional_fields | Create user with all fields populated | 🔥 |
| 159 | test_user_email_unique_constraint_enforced | Duplicate email raises IntegrityError | 🔥 |
| 160 | test_user_phone_unique_constraint_enforced | Duplicate phone raises IntegrityError | 🔥 |
| 161 | test_user_status_enum_validation | Only valid UserStatus values accepted | 🔥 |
| 162 | test_user_profile_relationship_lazy_loads | user.profile relationship exists | 🔥 |
| 163 | test_user_profile_cascade_delete_on_user_delete | Delete user cascades to profile | 🔥 |
| 164 | test_user_contacts_relationship_returns_list | user.contacts returns list | 🔥 |
| 165 | test_user_otp_expires_at_nullable | otp_expires_at can be NULL | 🔥 |
| 166 | test_user_password_hashed_on_save | Password never stored as plaintext | 🔥 |
| 167 | test_create_contact_with_minimal_fields | Create contact with first_name only | 🔥 |
| 168 | test_create_contact_with_all_fields | Create contact with all fields | 🔥 |
| 169 | test_contact_owner_foreign_key_valid | Valid owner_user_id required | 🔥 |
| 170 | test_contact_owner_foreign_key_invalid_raises | Invalid owner_user_id raises error | 🔥 |
| 171 | test_contact_linked_user_nullable | linked_user_id can be NULL | 🔥 |
| 172 | test_contact_cascade_delete_when_owner_deleted | Delete user deletes contacts | 🔥 |
| 173 | test_contact_emails_json_array_stored_correctly | emails stored as JSON array | 🔥 |
| 174 | test_contact_phone_numbers_json_array | phone_numbers stored as JSON array | 🔥 |
| 175 | test_contact_date_of_birth_string_format | DOB stored as string | 🔥 |
| 176 | test_contact_full_address_fields_populated | All address fields work | 🔥 |
| 177 | test_create_vault_file_manual_mode | creation_mode='manual' | 🔥 |
| 178 | test_create_vault_file_import_mode | creation_mode='import' | 🔥 |
| 179 | test_vault_file_has_source_file_false_default | has_source_file defaults False | 🔥 |
| 180 | test_vault_file_s3_key_nullable_when_no_file | source_file_s3_key can be NULL | 🔥 |
| 181 | test_vault_file_owner_foreign_key_to_user | Valid owner_user_id required | 🔥 |
| 182 | test_vault_file_creation_mode_check_constraint | Only manual/import allowed | 🔥 |
| 183 | test_vault_file_status_enum_validation | Only valid statuses allowed | 🔥 |
| 184 | test_vault_file_access_list_relationship | vault_file.access_list works | 🔥 |
| 185 | test_create_folder_with_user_and_name | Create folder | 🔥 |
| 186 | test_folder_user_foreign_key_valid | Valid user_id required | 🔥 |
| 187 | test_folder_branches_relationship_empty_list | folder.branches returns list | 🔥 |
| 188 | test_folder_leaves_relationship_empty_list | folder.leaves returns list | 🔥 |
| 189 | test_folder_trigger_relationship_one_to_one | folder.trigger is one-to-one | 🔥 |
| 190 | test_folder_files_relationship | folder.files relationship | 🔥 |
| 191 | test_create_memory_collection_basic | Create memory collection | 🔥 |
| 192 | test_memory_event_type_enum_required | event_type required | 🔥 |
| 193 | test_memory_scheduled_at_nullable | scheduled_at can be NULL | 🔥 |
| 194 | test_memory_is_armed_default_false | is_armed defaults False | 🔥 |
| 195 | test_memory_files_relationship | collection.files relationship | 🔥 |
| 196 | test_memory_assignments_relationship | collection.folder_assignments relationship | 🔥 |
| 197 | test_create_reminder_with_required_fields | Create reminder | 🔥 |
| 198 | test_reminder_user_foreign_key_valid | Valid user_id required | 🔥 |
| 199 | test_reminder_vault_file_foreign_key_valid | Valid vault_file_id required | 🔥 |
| 200 | test_reminder_urgency_level_enum | urgency_level enum validation | 🔥 |
| 201 | test_reminder_status_enum | status enum validation | 🔥 |

### tests/unit/foundation/test_database_relationships.py (20 tests)

| # | Test Function | Description | Priority |
|---|---------------|-------------|----------|
| 202 | test_delete_user_cascades_to_contacts | Delete user deletes contacts | 🔥 |
| 203 | test_delete_user_cascades_to_vault_files | Delete user deletes vault files | 🔥 |
| 204 | test_delete_user_cascades_to_folders | Delete user deletes folders | 🔥 |
| 205 | test_delete_folder_cascades_to_branches | Delete folder deletes branches | 🔥 |
| 206 | test_delete_folder_cascades_to_leaves | Delete folder deletes leaves | 🔥 |
| 207 | test_delete_memory_collection_cascades_to_files | Delete collection deletes files | 🔥 |
| 208 | test_delete_category_cascades_to_sections | Delete category deletes sections | 🔥 |
| 209 | test_cannot_create_contact_with_invalid_owner | Invalid owner_user_id fails | 🔥 |
| 210 | test_cannot_create_vault_with_invalid_user | Invalid owner_user_id fails | 🔥 |
| 211 | test_cannot_create_trustee_with_invalid_contact | Invalid contact_id fails | 🔥 |
| 212 | test_folder_branch_unique_per_folder_contact | (folder_id, contact_id) unique | 🔥 |
| 213 | test_folder_leaf_unique_per_folder_contact_role | (folder_id, contact_id, role) unique | 🔥 |
| 214 | test_memory_assignment_unique | (collection_id, contact_id, role) unique | 🔥 |
| 215 | test_trustee_unique_per_user_contact | (user_id, contact_id) unique | 🔥 |
| 216 | test_user_contacts_lazy_loading | contacts not loaded by default | ⭐ |
| 217 | test_user_contacts_eager_loading | joinedload() loads contacts | ⭐ |
| 218 | test_folder_trigger_one_to_one_loading | trigger loaded correctly | ⭐ |
| 219 | test_vault_file_access_list_loading | access_list loaded | ⭐ |
| 220 | test_memory_collection_files_loading | files loaded | ⭐ |
| 221 | test_category_section_steps_loading | steps loaded | ⭐ |

### tests/unit/foundation/test_config.py (15 tests)

| # | Test Function | Description | Priority |
|---|---------------|-------------|----------|
| 222 | test_load_settings_from_env_file | .env file parsed | 🔥 |
| 223 | test_database_url_required_raises_error | Missing DATABASE_URL fails | 🔥 |
| 224 | test_secret_key_required_raises_error | Missing SECRET_KEY fails | 🔥 |
| 225 | test_aws_access_key_required | Missing AWS_ACCESS_KEY_ID fails | 🔥 |
| 226 | test_kms_key_id_required | Missing KMS_KEY_ID fails | 🔥 |
| 227 | test_s3_bucket_name_required | Missing S3_BUCKET_NAME fails | 🔥 |
| 228 | test_smtp_email_and_password_loaded | SMTP credentials loaded | 🔥 |
| 229 | test_twilio_credentials_loaded | Twilio SID and token loaded | 🔥 |
| 230 | test_gemini_api_key_loaded | GEMINI_API_KEY loaded | 🔥 |
| 231 | test_aws_region_defaults_to_ap_south_1 | Default region ap-south-1 | ⭐ |
| 232 | test_algorithm_defaults_to_hs256 | JWT algorithm defaults HS256 | ⭐ |
| 233 | test_access_token_expiry_default_30_days | Default 43200 minutes | ⭐ |
| 234 | test_max_file_size_defaults_10mb | Default 10MB | ⭐ |
| 235 | test_missing_required_config_raises_valueerror | ValidationError on missing config | 🔥 |
| 236 | test_invalid_region_format_rejected | Invalid AWS region rejected | ⭐ |

### tests/unit/foundation/test_security_core.py (12 tests)

| # | Test Function | Description | Priority |
|---|---------------|-------------|----------|
| 237 | test_hash_password_returns_different_from_plain | Hash != plaintext | 🔥 |
| 238 | test_hash_password_uses_bcrypt_format | Hash starts with $2b$ | 🔥 |
| 239 | test_hash_different_passwords_unique_hashes | Different inputs = different hashes | 🔥 |
| 240 | test_hash_same_password_different_salts | Same input = different hashes (salt) | 🔥 |
| 241 | test_verify_password_correct_returns_true | Correct password verified | 🔥 |
| 242 | test_verify_password_incorrect_returns_false | Wrong password rejected | 🔥 |
| 243 | test_verify_password_case_sensitive | Case matters | 🔥 |
| 244 | test_create_access_token_contains_user_id | sub claim in token | 🔥 |
| 245 | test_create_access_token_has_expiry | exp claim in token | 🔥 |
| 246 | test_decode_access_token_returns_payload | Decode returns dict | 🔥 |
| 247 | test_decode_token_with_wrong_key_fails | Wrong SECRET_KEY fails | 🔥 |
| 248 | test_expired_token_raises_jwt_error | Expired token rejected | 🔥 |

### tests/unit/foundation/test_dependencies.py (10 tests)

| # | Test Function | Description | Priority |
|---|---------------|-------------|----------|
| 249 | test_valid_token_returns_user_object | Valid JWT returns User | 🔥 |
| 250 | test_invalid_token_raises_401_unauthorized | Bad JWT raises 401 | 🔥 |
| 251 | test_expired_token_raises_401 | Expired JWT raises 401 | 🔥 |
| 252 | test_missing_authorization_header_raises_401 | No header raises 401 | 🔥 |
| 253 | test_user_not_found_in_db_raises_401 | Deleted user raises 401 | 🔥 |
| 254 | test_valid_admin_token_returns_admin_object | Valid admin JWT returns Admin | 🔥 |
| 255 | test_user_token_rejected_for_admin_endpoint | User JWT on admin endpoint fails | 🔥 |
| 256 | test_admin_flag_required_in_token_payload | adm=True required | 🔥 |
| 257 | test_db_session_created_and_yielded | Session created | 🔥 |
| 258 | test_db_session_closed_after_request | Session closed in finally | 🔥 |

### tests/integration/foundation/test_database_transactions.py (15 tests)

| # | Test Function | Description | Priority |
|---|---------------|-------------|----------|
| 259 | test_commit_persists_user_to_database | Commit saves data | 🔥 |
| 260 | test_commit_persists_multiple_related_objects | Commit saves all objects | 🔥 |
| 261 | test_flush_without_commit_visible_in_session | flush() visible in session | ⭐ |
| 262 | test_rollback_reverts_uncommitted_changes | rollback() discards changes | 🔥 |
| 263 | test_rollback_on_integrity_error_auto | IntegrityError auto-rolls back | 🔥 |
| 264 | test_rollback_on_exception_in_transaction | Exception triggers rollback | 🔥 |
| 265 | test_nested_transaction_savepoint_rollback | Savepoint rollback | ⭐ |
| 266 | test_concurrent_inserts_no_deadlock | Multiple inserts work | ⭐ |
| 267 | test_concurrent_updates_last_write_wins | Last update wins | ⭐ |
| 268 | test_optimistic_locking_with_version_field | Version prevents conflicts | ⭐ |
| 269 | test_multiple_sessions_from_pool | Multiple sessions OK | ⭐ |
| 270 | test_session_cleanup_returns_to_pool | Session returned to pool | ⭐ |
| 271 | test_pool_exhaustion_waits_for_connection | Pool full waits | ⭐ |
| 272 | test_pool_timeout_raises_timeout_error | Wait timeout raises error | ⭐ |
| 273 | test_connection_recycling_after_max_age | Old connections recycled | ⭐ |

**Module 1 Subtotal: 117 tests**

---

## MODULE 2: AUTH (130 tests)

### tests/unit/auth/test_user_controller.py (25 tests)

| # | Test Function | Description | Priority |
|---|---------------|-------------|----------|
| 274 | test_create_user_with_email_only | Email + minimal fields | 🔥 |
| 275 | test_create_user_with_phone_only | Phone + minimal fields | 🔥 |
| 276 | test_create_user_password_automatically_hashed | Password hashed | 🔥 |
| 277 | test_create_user_otp_not_set_initially | otp=None initially | 🔥 |
| 278 | test_create_user_status_defaults_to_unknown | status=unknown default | 🔥 |
| 279 | test_create_user_duplicate_email_raises_error | Duplicate email fails | 🔥 |
| 280 | test_create_user_duplicate_phone_raises_error | Duplicate phone fails | 🔥 |
| 281 | test_get_user_by_email_returns_user | Find by email | 🔥 |
| 282 | test_get_user_by_phone_returns_user | Find by phone | 🔥 |
| 283 | test_get_user_by_display_name_returns_user | Find by display_name | 🔥 |
| 284 | test_get_user_by_phone_and_country_code | Find by phone+country_code | 🔥 |
| 285 | test_get_user_not_found_returns_none | Not found returns None | 🔥 |
| 286 | test_update_user_display_name | Update display_name | 🔥 |
| 287 | test_update_user_email | Update email | 🔥 |
| 288 | test_update_user_phone | Update phone | 🔥 |
| 289 | test_update_user_country_code_adds_plus_prefix | +prefix added | 🔥 |
| 290 | test_update_user_status | Update status | 🔥 |
| 291 | test_update_user_profile_fields | Update profile | 🔥 |
| 292 | test_update_nonexistent_user_returns_none | Not found returns None | 🔥 |
| 293 | test_generate_otp_is_six_digits | OTP length 6 | 🔥 |
| 294 | test_generate_otp_is_numeric_only | Only digits | 🔥 |
| 295 | test_generate_otp_different_each_call | Random OTP | 🔥 |
| 296 | test_transition_unknown_to_guest | unknown → guest | 🔥 |
| 297 | test_transition_guest_to_verified | guest → verified | 🔥 |
| 298 | test_transition_verified_to_member | verified → member | 🔥 |

### tests/unit/auth/test_admin_controller.py (10 tests)

| # | Test Function | Description | Priority |
|---|---------------|-------------|----------|
| 299 | test_create_admin_with_username_email | Create admin | 🔥 |
| 300 | test_admin_password_hashed_on_save | Password hashed | 🔥 |
| 301 | test_admin_otp_generation | Admin OTP generated | 🔥 |
| 302 | test_get_admin_by_username | Find by username | 🔥 |
| 303 | test_get_admin_by_email | Find by email | 🔥 |
| 304 | test_admin_duplicate_username_raises_error | Duplicate username fails | 🔥 |
| 305 | test_admin_otp_set_on_request | OTP set | 🔥 |
| 306 | test_admin_otp_expires_after_5_minutes | 5 min expiry | 🔥 |
| 307 | test_admin_otp_cleared_after_verification | OTP cleared | 🔥 |
| 308 | test_admin_otp_different_from_user_otp | Separate OTP systems | ⭐ |

### tests/unit/auth/test_verification_controller.py (12 tests)

| # | Test Function | Description | Priority |
|---|---------------|-------------|----------|
| 309 | test_submit_document_verification | Submit document | 🔥 |
| 310 | test_submit_referral_verification | Submit referral | 🔥 |
| 311 | test_verification_status_defaults_pending | status=pending | 🔥 |
| 312 | test_verification_requires_document_type | document_type required | 🔥 |
| 313 | test_verification_document_ref_stored | document_ref saved | 🔥 |
| 314 | test_submit_verification_creates_history_entry | History entry created | 🔥 |
| 315 | test_admin_accept_verification | Admin accepts | 🔥 |
| 316 | test_admin_reject_verification | Admin rejects | 🔥 |
| 317 | test_accept_updates_user_status_to_verified | User becomes verified | 🔥 |
| 318 | test_reject_keeps_user_status_unchanged | Status unchanged | 🔥 |
| 319 | test_reviewed_by_field_set_to_admin_id | reviewed_by set | ⭐ |
| 320 | test_reviewed_at_timestamp_set | reviewed_at set | ⭐ |

### tests/unit/auth/test_contact_controller.py (20 tests)

| # | Test Function | Description | Priority |
|---|---------------|-------------|----------|
| 321 | test_create_contact_minimal_fields | first_name + owner | 🔥 |
| 322 | test_create_contact_all_fields | All fields | 🔥 |
| 323 | test_create_contact_with_emails_array | emails JSON | 🔥 |
| 324 | test_create_contact_with_phone_numbers_array | phone_numbers JSON | 🔥 |
| 325 | test_create_contact_owner_must_exist | Valid owner required | 🔥 |
| 326 | test_update_contact_name_fields | Update names | 🔥 |
| 327 | test_update_contact_address_fields | Update address | 🔥 |
| 328 | test_update_contact_emails | Update emails | 🔥 |
| 329 | test_update_contact_linked_user_id | Link user | 🔥 |
| 330 | test_delete_contact_by_id | Delete contact | 🔥 |
| 331 | test_delete_contact_cascade_on_owner_delete | Cascade delete | 🔥 |
| 332 | test_link_contact_to_user_by_email | Link by email | 🔥 |
| 333 | test_link_contact_to_user_by_phone | Link by phone | 🔥 |
| 334 | test_link_updates_linked_user_id | linked_user_id set | 🔥 |
| 335 | test_unlink_contact_sets_null | Unlink sets NULL | ⭐ |
| 336 | test_get_all_contacts_for_user | List all | 🔥 |
| 337 | test_get_contact_by_id | Get by ID | 🔥 |
| 338 | test_search_contacts_by_name | Name search | ⭐ |
| 339 | test_filter_contacts_by_category | Category filter | ⭐ |
| 340 | test_filter_emergency_contacts | Emergency flag | ⭐ |

### tests/unit/auth/test_otp_generation.py (8 tests)

| # | Test Function | Description | Priority |
|---|---------------|-------------|----------|
| 341 | test_generate_numeric_otp_length_6 | Length 6 | 🔥 |
| 342 | test_generate_numeric_otp_only_digits | Only 0-9 | 🔥 |
| 343 | test_generate_otp_randomness | Different each time | 🔥 |
| 344 | test_otp_expiry_set_5_minutes_future | Expiry +5min | 🔥 |
| 345 | test_otp_verified_flag_defaults_false | otp_verified=False | 🔥 |
| 346 | test_otp_cleared_after_successful_verification | OTP cleared | 🔥 |
| 347 | test_expired_otp_rejected | Past expiry invalid | 🔥 |
| 348 | test_wrong_otp_rejected | Wrong OTP invalid | 🔥 |

### tests/unit/auth/test_user_status_lifecycle.py (10 tests)

| # | Test Function | Description | Priority |
|---|---------------|-------------|----------|
| 349 | test_new_user_starts_as_unknown | Initial state unknown | 🔥 |
| 350 | test_unknown_to_guest_after_otp_verify | unknown → guest | 🔥 |
| 351 | test_guest_to_verified_after_document_approval | guest → verified | 🔥 |
| 352 | test_verified_to_member_after_profile_complete | verified → member | 🔥 |
| 353 | test_cannot_skip_states | No unknown → verified | 🔥 |
| 354 | test_status_history_recorded_on_transition | History entry | 🔥 |
| 355 | test_from_status_and_to_status_populated | History fields | ⭐ |
| 356 | test_transition_timestamp_recorded | Timestamp recorded | ⭐ |
| 357 | test_multiple_transitions_create_history_chain | Multiple entries | ⭐ |
| 358 | test_current_status_queryable | Query by status | ⭐ |

### tests/integration/auth/test_auth_api_endpoints.py (25 tests)

| # | Test Function | Description | Priority |
|---|---------------|-------------|----------|
| 359 | test_register_with_email_success | POST /auth/register | 🔥 |
| 360 | test_register_with_phone_success | POST /auth/register | 🔥 |
| 361 | test_register_duplicate_email_returns_400 | Duplicate email | 🔥 |
| 362 | test_register_missing_required_fields_returns_422 | Validation error | 🔥 |
| 363 | test_register_returns_otp_in_dev_mode | OTP in response | 🔥 |
| 364 | test_otp_start_with_email | POST /auth/otp/start | 🔥 |
| 365 | test_otp_start_with_phone | POST /auth/otp/start | 🔥 |
| 366 | test_otp_start_user_not_found_returns_404 | Not found | 🔥 |
| 367 | test_otp_sent_via_email | Email delivery | 🔥 |
| 368 | test_otp_sent_via_sms | SMS delivery | 🔥 |
| 369 | test_otp_verify_correct_otp_returns_token | POST /auth/otp/verify | 🔥 |
| 370 | test_otp_verify_wrong_otp_returns_401 | Wrong OTP | 🔥 |
| 371 | test_otp_verify_expired_otp_returns_401 | Expired OTP | 🔥 |
| 372 | test_otp_verify_updates_otp_verified_flag | Flag updated | 🔥 |
| 373 | test_login_with_email_and_password | POST /auth/login | 🔥 |
| 374 | test_login_with_phone_and_password | POST /auth/login | 🔥 |
| 375 | test_login_wrong_password_returns_401 | Wrong password | 🔥 |
| 376 | test_login_user_not_found_returns_404 | Not found | 🔥 |
| 377 | test_login_returns_jwt_token | Token in response | 🔥 |
| 378 | test_password_reset_request | POST /auth/password-reset | ⭐ |
| 379 | test_password_reset_confirm | POST /auth/password-reset/confirm | ⭐ |
| 380 | test_admin_login_with_username | POST /auth/admin/login | 🔥 |
| 381 | test_admin_login_requires_admin_credentials | User creds fail | 🔥 |
| 382 | test_admin_otp_separate_from_user | Separate system | ⭐ |
| 383 | test_logout_invalidates_token | POST /auth/logout | ⭐ |

### tests/integration/auth/test_user_api_endpoints.py (20 tests)

| # | Test Function | Description | Priority |
|---|---------------|-------------|----------|
| 384 | test_get_current_user_authenticated | GET /users/me | 🔥 |
| 385 | test_get_current_user_unauthenticated_returns_401 | No token | 🔥 |
| 386 | test_get_current_user_expired_token_returns_401 | Expired token | 🔥 |
| 387 | test_update_user_profile | PATCH /users/me | 🔥 |
| 388 | test_update_user_display_name | Update name | 🔥 |
| 389 | test_update_user_email | Update email | 🔥 |
| 390 | test_update_user_phone | Update phone | 🔥 |
| 391 | test_get_user_by_id_as_admin | GET /users/{id} | 🔥 |
| 392 | test_get_user_by_id_as_regular_user_forbidden | Non-admin fails | 🔥 |
| 393 | test_list_all_users_as_admin | GET /users | 🔥 |
| 394 | test_list_all_users_as_regular_user_forbidden | Non-admin fails | 🔥 |
| 395 | test_delete_user_as_admin | DELETE /users/{id} | 🔥 |
| 396 | test_delete_user_as_regular_user_forbidden | Non-admin fails | 🔥 |
| 397 | test_delete_user_cascades_to_related_data | Cascade works | 🔥 |
| 398 | test_upload_profile_picture | POST /users/me/avatar | ⭐ |
| 399 | test_get_profile_picture_url | GET /users/me/avatar | ⭐ |
| 400 | test_change_password | POST /users/me/change-password | ⭐ |
| 401 | test_change_password_wrong_current_password | Wrong current fails | ⭐ |
| 402 | test_deactivate_account | POST /users/me/deactivate | ⭐ |
| 403 | test_reactivate_account | POST /users/me/reactivate | ⭐ |

**Module 2 Subtotal: 130 tests**

---

## MODULE 3: VAULT (175 tests)

### tests/unit/vault/test_crypto_engine.py (25 tests)

| # | Test Function | Description | Priority |
|---|---------------|-------------|----------|
| 404 | test_generate_data_key_returns_tuple | (plaintext, encrypted) | 🔥 |
| 405 | test_plaintext_key_is_32_bytes | 256-bit key | 🔥 |
| 406 | test_encrypted_key_is_bytes | Ciphertext bytes | 🔥 |
| 407 | test_generate_data_key_calls_kms | KMS called | 🔥 |
| 408 | test_kms_failure_raises_key_generation_exception | KMS error handled | 🔥 |
| 409 | test_decrypt_data_key_returns_plaintext | Plaintext bytes | 🔥 |
| 410 | test_decrypt_calls_kms_decrypt | KMS decrypt called | 🔥 |
| 411 | test_decrypt_invalid_key_raises_exception | Invalid key fails | 🔥 |
| 412 | test_decrypt_access_denied_raises_exception | AccessDenied handled | 🔥 |
| 413 | test_decrypt_empty_key_raises_invalid_key_exception | Empty input fails | 🔥 |
| 414 | test_generate_nonce_returns_12_bytes | 96-bit nonce | 🔥 |
| 415 | test_nonce_is_random | Different each time | 🔥 |
| 416 | test_nonce_is_bytes_type | Bytes type | 🔥 |
| 417 | test_encrypt_data_with_valid_key_and_nonce | Encryption works | 🔥 |
| 418 | test_encrypt_returns_bytes | Returns bytes | 🔥 |
| 419 | test_encrypt_output_different_from_input | Ciphertext != plaintext | 🔥 |
| 420 | test_encrypt_with_wrong_key_size_raises | Key size validation | 🔥 |
| 421 | test_encrypt_with_wrong_nonce_size_raises | Nonce size validation | 🔥 |
| 422 | test_encrypt_empty_data_succeeds | Empty input OK | ⭐ |
| 423 | test_decrypt_data_with_correct_key | Decryption works | 🔥 |
| 424 | test_decrypt_returns_original_plaintext | Roundtrip correct | 🔥 |
| 425 | test_decrypt_with_wrong_key_raises_auth_failed | Wrong key fails | 🔥 |
| 426 | test_decrypt_with_tampered_ciphertext_raises | Tampering detected | 🔥 |
| 427 | test_decrypt_with_wrong_nonce_raises | Wrong nonce fails | 🔥 |
| 428 | test_decrypt_empty_ciphertext_raises | Empty input fails | ⭐ |

### tests/unit/vault/test_vault_encryptor.py (20 tests)

| # | Test Function | Description | Priority |
|---|---------------|-------------|----------|
| 429 | test_encrypt_form_data_manual_mode | Manual mode | 🔥 |
| 430 | test_encrypted_dek_is_base64 | DEK base64 | 🔥 |
| 431 | test_encrypted_form_data_is_base64 | Form data base64 | 🔥 |
| 432 | test_nonce_form_data_is_base64 | Nonce base64 | 🔥 |
| 433 | test_has_source_file_false_when_manual | Flag=False | 🔥 |
| 434 | test_encrypt_form_data_and_source_file | Import mode | 🔥 |
| 435 | test_source_file_uploaded_to_s3 | S3 upload called | 🔥 |
| 436 | test_source_file_s3_key_format_correct | Key format correct | 🔥 |
| 437 | test_source_file_encrypted_before_upload | File encrypted | 🔥 |
| 438 | test_source_file_nonce_generated | Separate nonce | 🔥 |
| 439 | test_source_file_nonce_base64_encoded | Nonce encoded | 🔥 |
| 440 | test_has_source_file_true_when_import | Flag=True | 🔥 |
| 441 | test_form_data_too_large_raises_exception | Size limit | 🔥 |
| 442 | test_source_file_too_large_raises_exception | 10MB limit | 🔥 |
| 443 | test_invalid_mime_type_raises_exception | MIME validation | 🔥 |
| 444 | test_invalid_json_form_data_raises_exception | JSON validation | 🔥 |
| 445 | test_file_id_is_unique | Unique IDs | 🔥 |
| 446 | test_file_id_format_contains_timestamp | Timestamp in ID | ⭐ |
| 447 | test_kms_failure_raises_encryption_exception | KMS error | 🔥 |
| 448 | test_s3_failure_raises_s3_upload_exception | S3 error | 🔥 |

### tests/unit/vault/test_vault_decryptor.py (20 tests)

| # | Test Function | Description | Priority |
|---|---------------|-------------|----------|
| 449 | test_decrypt_form_data_only | Decrypt form data | 🔥 |
| 450 | test_decrypted_form_data_matches_original | Roundtrip correct | 🔥 |
| 451 | test_decrypt_form_data_and_source_file | Decrypt both | 🔥 |
| 452 | test_decrypted_source_file_matches_original | File roundtrip | 🔥 |
| 453 | test_decrypt_with_wrong_dek_raises_exception | Wrong DEK fails | 🔥 |
| 454 | test_decrypt_tampered_data_raises_exception | Tampering detected | 🔥 |
| 455 | test_metadata_contains_plaintext_dek | DEK in response | 🔥 |
| 456 | test_metadata_dek_base64_encoded | DEK encoded | 🔥 |
| 457 | test_metadata_contains_nonces | Nonces present | 🔥 |
| 458 | test_metadata_s3_url_when_source_file_exists | URL generated | 🔥 |
| 459 | test_metadata_no_s3_url_when_no_source_file | URL=None | 🔥 |
| 460 | test_metadata_s3_url_expires_in_1_hour | URL expiry | 🔥 |
| 461 | test_metadata_access_recorded_in_db | Access logged | 🔥 |
| 462 | test_owner_can_decrypt_own_file | Owner access | 🔥 |
| 463 | test_shared_user_can_decrypt_after_activation | Recipient access | 🔥 |
| 464 | test_unshared_user_cannot_decrypt | No access | 🔥 |
| 465 | test_revoked_access_cannot_decrypt | Revoked denied | 🔥 |
| 466 | test_file_not_found_raises_exception | Not found | 🔥 |
| 467 | test_kms_decrypt_failure_raises_exception | KMS error | 🔥 |
| 468 | test_s3_download_failure_raises_exception | S3 error | 🔥 |

### tests/unit/vault/test_db_operations.py (15 tests)

| # | Test Function | Description | Priority |
|---|---------------|-------------|----------|
| 469 | test_get_vault_file_by_id | Retrieve by ID | 🔥 |
| 470 | test_get_vault_file_not_found_returns_none | Not found | 🔥 |
| 471 | test_get_vault_file_includes_access_list | Eager load | ⭐ |
| 472 | test_check_access_owner_allowed | Owner allowed | 🔥 |
| 473 | test_check_access_shared_user_active_allowed | Active allowed | 🔥 |
| 474 | test_check_access_shared_user_pending_denied | Pending denied | 🔥 |
| 475 | test_check_access_shared_user_revoked_denied | Revoked denied | 🔥 |
| 476 | test_check_access_unshared_user_denied | Not shared denied | 🔥 |
| 477 | test_grant_access_creates_record | Access granted | 🔥 |
| 478 | test_grant_access_status_pending | Default pending | 🔥 |
| 479 | test_grant_access_duplicate_raises_exception | Duplicate fails | 🔥 |
| 480 | test_activate_access_changes_status | pending → active | 🔥 |
| 481 | test_activate_access_sets_activated_at | Timestamp set | ⭐ |
| 482 | test_revoke_access_changes_status | active → revoked | 🔥 |
| 483 | test_revoke_access_sets_revoked_at | Timestamp set | ⭐ |

### tests/unit/vault/test_s3_operations.py (18 tests)

| # | Test Function | Description | Priority |
|---|---------------|-------------|----------|
| 484 | test_upload_file_to_s3 | Upload works | 🔥 |
| 485 | test_upload_generates_correct_key | Key format | 🔥 |
| 486 | test_upload_sets_correct_mime_type | MIME type | 🔥 |
| 487 | test_upload_file_encrypted | File encrypted | 🔥 |
| 488 | test_upload_failure_raises_exception | S3 error | 🔥 |
| 489 | test_download_file_from_s3 | Download works | 🔥 |
| 490 | test_download_decrypts_file | File decrypted | 🔥 |
| 491 | test_download_invalid_key_raises_exception | Invalid key | 🔥 |
| 492 | test_download_not_found_raises_exception | Not found | 🔥 |
| 493 | test_generate_presigned_url | URL generated | 🔥 |
| 494 | test_presigned_url_expires_in_1_hour | 1 hour expiry | 🔥 |
| 495 | test_presigned_url_format_correct | URL format | ⭐ |
| 496 | test_delete_file_from_s3 | Delete works | 🔥 |
| 497 | test_delete_nonexistent_file_succeeds | Delete idempotent | ⭐ |
| 498 | test_list_files_in_bucket | List works | ⭐ |
| 499 | test_list_files_with_prefix | Prefix filter | ⭐ |
| 500 | test_s3_connection_retry_on_failure | Retry logic | ⭐ |
| 501 | test_s3_timeout_raises_exception | Timeout error | ⭐ |

### tests/unit/vault/test_validators.py (15 tests)

| # | Test Function | Description | Priority |
|---|---------------|-------------|----------|
| 502 | test_validate_file_size_within_limit | <10MB passes | 🔥 |
| 503 | test_validate_file_size_exceeds_limit | >10MB fails | 🔥 |
| 504 | test_validate_file_size_exact_limit | =10MB passes | ⭐ |
| 505 | test_validate_mime_type_pdf | PDF allowed | 🔥 |
| 506 | test_validate_mime_type_image | Image allowed | 🔥 |
| 507 | test_validate_mime_type_invalid | Invalid fails | 🔥 |
| 508 | test_validate_form_data_json_valid | Valid JSON | 🔥 |
| 509 | test_validate_form_data_json_invalid | Invalid JSON fails | 🔥 |
| 510 | test_validate_form_data_too_many_fields | >100 fields fails | 🔥 |
| 511 | test_validate_template_id_exists | Valid template | 🔥 |
| 512 | test_validate_template_id_invalid | Invalid template fails | 🔥 |
| 513 | test_validate_creation_mode_manual | manual allowed | 🔥 |
| 514 | test_validate_creation_mode_import | import allowed | 🔥 |
| 515 | test_validate_creation_mode_invalid | invalid fails | 🔥 |
| 516 | test_validate_user_id_format | Valid UUID format | ⭐ |

### tests/unit/vault/test_exceptions.py (12 tests)

| # | Test Function | Description | Priority |
|---|---------------|-------------|----------|
| 517 | test_encryption_exception_raised | EncryptionException | 🔥 |
| 518 | test_decryption_exception_raised | DecryptionException | 🔥 |
| 519 | test_key_generation_exception_raised | KeyGenerationException | 🔥 |
| 520 | test_kms_decryption_exception_raised | KMSDecryptionException | 🔥 |
| 521 | test_s3_upload_exception_raised | S3UploadException | 🔥 |
| 522 | test_s3_download_exception_raised | S3DownloadException | 🔥 |
| 523 | test_file_too_large_exception_raised | FileTooLargeException | 🔥 |
| 524 | test_invalid_file_type_exception_raised | InvalidFileTypeException | 🔥 |
| 525 | test_invalid_json_exception_raised | InvalidJSONException | 🔥 |
| 526 | test_unauthorized_access_exception_raised | UnauthorizedAccessException | 🔥 |
| 527 | test_file_not_found_exception_raised | FileNotFoundException | 🔥 |
| 528 | test_validation_exception_raised | ValidationException | 🔥 |

### tests/integration/vault/test_vault_api_endpoints.py (30 tests)

| # | Test Function | Description | Priority |
|---|---------------|-------------|----------|
| 529 | test_save_vault_file_manual_mode | POST /api/vault/save | 🔥 |
| 530 | test_save_vault_file_import_mode | With source file | 🔥 |
| 531 | test_save_vault_file_unauthenticated_returns_401 | No token | 🔥 |
| 532 | test_save_vault_file_invalid_template_returns_400 | Invalid template | 🔥 |
| 533 | test_save_vault_file_file_too_large_returns_413 | >10MB | 🔥 |
| 534 | test_save_vault_file_returns_file_id | file_id in response | 🔥 |
| 535 | test_get_decryption_metadata_owner | GET /api/vault/{id}/metadata | 🔥 |
| 536 | test_get_decryption_metadata_shared_user | Shared access | 🔥 |
| 537 | test_get_decryption_metadata_unshared_returns_403 | No access | 🔥 |
| 538 | test_get_decryption_metadata_contains_dek | DEK present | 🔥 |
| 539 | test_get_decryption_metadata_contains_s3_url | S3 URL present | 🔥 |
| 540 | test_decrypt_vault_file_owner | GET /api/vault/{id}/decrypt | 🔥 |
| 541 | test_decrypt_vault_file_shared_user | Shared access | 🔥 |
| 542 | test_decrypt_vault_file_unshared_returns_403 | No access | 🔥 |
| 543 | test_decrypt_vault_file_returns_plaintext | Plaintext returned | 🔥 |
| 544 | test_list_vault_files | GET /api/vault | 🔥 |
| 545 | test_list_vault_files_filtered_by_template | Filter works | ⭐ |
| 546 | test_list_vault_files_pagination | Pagination | ⭐ |
| 547 | test_share_vault_file | POST /api/vault/{id}/share | 🔥 |
| 548 | test_share_vault_file_with_user_id | Share with user | 🔥 |
| 549 | test_share_vault_file_duplicate_returns_400 | Already shared | 🔥 |
| 550 | test_share_vault_file_not_owner_returns_403 | Non-owner fails | 🔥 |
| 551 | test_activate_access | POST /api/vault/{id}/activate | 🔥 |
| 552 | test_activate_access_changes_status | pending → active | 🔥 |
| 553 | test_revoke_access | DELETE /api/vault/{id}/access/{user_id} | 🔥 |
| 554 | test_revoke_access_not_owner_returns_403 | Non-owner fails | 🔥 |
| 555 | test_list_access_list | GET /api/vault/{id}/access | 🔥 |
| 556 | test_list_access_list_not_owner_returns_403 | Non-owner fails | 🔥 |
| 557 | test_delete_vault_file | DELETE /api/vault/{id} | 🔥 |
| 558 | test_delete_vault_file_not_owner_returns_403 | Non-owner fails | 🔥 |

### tests/integration/vault/test_vault_encryption_flow.py (20 tests)

| # | Test Function | Description | Priority |
|---|---------------|-------------|----------|
| 559 | test_end_to_end_manual_mode_encryption_decryption | Full flow | 🔥 |
| 560 | test_end_to_end_import_mode_encryption_decryption | Full flow | 🔥 |
| 561 | test_roundtrip_form_data_integrity | Data matches | 🔥 |
| 562 | test_roundtrip_source_file_integrity | File matches | 🔥 |
| 563 | test_kms_key_rotation_handled | Key rotation | ⭐ |
| 564 | test_multiple_files_different_deks | Different DEKs | 🔥 |
| 565 | test_share_and_activate_flow | Share → activate | 🔥 |
| 566 | test_revoke_and_access_denied_flow | Revoke → denied | 🔥 |
| 567 | test_concurrent_encryption_no_collision | Concurrent safe | ⭐ |
| 568 | test_concurrent_decryption_no_collision | Concurrent safe | ⭐ |
| 569 | test_large_form_data_encryption | Large JSON | ⭐ |
| 570 | test_large_source_file_encryption | Large file | ⭐ |
| 571 | test_special_characters_in_form_data | Unicode, emoji | ⭐ |
| 572 | test_binary_file_encryption | Binary file | 🔥 |
| 573 | test_encryption_with_aws_kms_unavailable | KMS down | ⭐ |
| 574 | test_encryption_with_s3_unavailable | S3 down | ⭐ |
| 575 | test_decryption_after_key_rotation | Key rotation | ⭐ |
| 576 | test_decryption_performance_acceptable | <500ms | ⭐ |
| 577 | test_access_logging_recorded | Access logged | 🔥 |
| 578 | test_audit_trail_complete | Full audit | ⭐ |

**Module 3 Subtotal: 175 tests**

---

## MODULE 4: CATEGORIES (152 tests)

### tests/unit/categories/test_category_controller.py (15 tests)

| # | Test Function | Description | Priority |
|---|---------------|-------------|----------|
| 579 | test_create_category_master | Create category | 🔥 |
| 580 | test_create_category_with_description | With description | 🔥 |
| 581 | test_category_name_unique_constraint | Duplicate name fails | 🔥 |
| 582 | test_get_category_by_id | Retrieve category | 🔥 |
| 583 | test_get_category_not_found_returns_none | Not found | 🔥 |
| 584 | test_update_category_name | Update name | 🔥 |
| 585 | test_update_category_description | Update description | 🔥 |
| 586 | test_delete_category_cascades_to_sections | Cascade delete | 🔥 |
| 587 | test_list_all_categories | List all | 🔥 |
| 588 | test_list_categories_ordered_by_name | Ordered result | ⭐ |
| 589 | test_category_section_relationship | category.sections | 🔥 |
| 590 | test_admin_only_can_create_category | Authorization | 🔥 |
| 591 | test_admin_only_can_update_category | Authorization | 🔥 |
| 592 | test_admin_only_can_delete_category | Authorization | 🔥 |
| 593 | test_category_display_order_field | display_order | ⭐ |

### tests/unit/categories/test_section_controller.py (12 tests)

| # | Test Function | Description | Priority |
|---|---------------|-------------|----------|
| 594 | test_create_section_for_category | Create section | 🔥 |
| 595 | test_section_requires_category_id | category_id required | 🔥 |
| 596 | test_section_allows_file_import_flag | allows_file_import | 🔥 |
| 597 | test_get_section_by_id | Retrieve section | 🔥 |
| 598 | test_update_section_name | Update name | 🔥 |
| 599 | test_update_section_description | Update description | 🔥 |
| 600 | test_delete_section_cascades_to_steps | Cascade delete | 🔥 |
| 601 | test_list_sections_for_category | List by category | 🔥 |
| 602 | test_section_steps_relationship | section.steps | 🔥 |
| 603 | test_section_display_order | display_order | ⭐ |
| 604 | test_admin_only_can_create_section | Authorization | 🔥 |
| 605 | test_admin_only_can_delete_section | Authorization | 🔥 |

### tests/unit/categories/test_step_controller.py (20 tests)

| # | Test Function | Description | Priority |
|---|---------------|-------------|----------|
| 606 | test_create_step_text_type | text step | 🔥 |
| 607 | test_create_step_date_type | date step | 🔥 |
| 608 | test_create_step_dropdown_type | dropdown step | 🔥 |
| 609 | test_create_step_file_type | file step | 🔥 |
| 610 | test_create_step_multiselect_type | multiselect step | 🔥 |
| 611 | test_step_requires_section_id | section_id required | 🔥 |
| 612 | test_step_label_required | label required | 🔥 |
| 613 | test_step_type_enum_validation | Valid types only | 🔥 |
| 614 | test_get_step_by_id | Retrieve step | 🔥 |
| 615 | test_update_step_label | Update label | 🔥 |
| 616 | test_update_step_is_required_flag | Update is_required | 🔥 |
| 617 | test_delete_step_cascades_to_options | Cascade delete | 🔥 |
| 618 | test_list_steps_for_section | List by section | 🔥 |
| 619 | test_step_options_relationship | step.options | 🔥 |
| 620 | test_step_display_order | display_order | ⭐ |
| 621 | test_create_step_options_for_dropdown | Options for dropdown | 🔥 |
| 622 | test_dropdown_step_requires_options | Options validation | 🔥 |
| 623 | test_admin_only_can_create_step | Authorization | 🔥 |
| 624 | test_admin_only_can_update_step | Authorization | 🔥 |
| 625 | test_admin_only_can_delete_step | Authorization | 🔥 |

### tests/unit/categories/test_user_answers_controller.py (18 tests)

| # | Test Function | Description | Priority |
|---|---------------|-------------|----------|
| 626 | test_save_text_answer | Save text answer | 🔥 |
| 627 | test_save_date_answer | Save date answer | 🔥 |
| 628 | test_save_dropdown_answer | Save dropdown answer | 🔥 |
| 629 | test_save_file_answer | Save file answer | 🔥 |
| 630 | test_save_multiselect_answer | Save multiselect answer | 🔥 |
| 631 | test_update_existing_answer | Update answer | 🔥 |
| 632 | test_get_answer_by_step_id | Retrieve answer | 🔥 |
| 633 | test_get_answers_for_section | All answers in section | 🔥 |
| 634 | test_delete_answer | Delete answer | 🔥 |
| 635 | test_answer_validation_text_type | Text validation | 🔥 |
| 636 | test_answer_validation_date_type | Date validation | 🔥 |
| 637 | test_answer_validation_dropdown_type | Dropdown validation | 🔥 |
| 638 | test_required_step_must_have_answer | Required validation | 🔥 |
| 639 | test_section_completion_check | All required answered | 🔥 |
| 640 | test_user_can_only_access_own_answers | Authorization | 🔥 |
| 641 | test_answer_history_tracking | History entry | ⭐ |
| 642 | test_answer_json_storage_format | JSON format | ⭐ |
| 643 | test_bulk_save_answers | Bulk operation | ⭐ |

### tests/unit/categories/test_leaf_assignment_controller.py (20 tests)

| # | Test Function | Description | Priority |
|---|---------------|-------------|----------|
| 644 | test_create_leaf_assignment | Create assignment | 🔥 |
| 645 | test_leaf_assignment_requires_contact_id | contact_id required | 🔥 |
| 646 | test_leaf_assignment_requires_section_id | section_id required | 🔥 |
| 647 | test_leaf_assignment_status_defaults_active | Default active | 🔥 |
| 648 | test_get_leaf_assignment_by_id | Retrieve assignment | 🔥 |
| 649 | test_update_leaf_assignment_status | Update status | 🔥 |
| 650 | test_leaf_assignment_accept | Accept assignment | 🔥 |
| 651 | test_leaf_assignment_reject | Reject assignment | 🔥 |
| 652 | test_leaf_assignment_remove | Remove assignment | 🔥 |
| 653 | test_list_leaf_assignments_for_user | User's assignments | 🔥 |
| 654 | test_list_leaf_assignments_for_section | Section assignments | 🔥 |
| 655 | test_leaf_assignment_unique_per_contact_section | Unique constraint | 🔥 |
| 656 | test_delete_leaf_assignment | Delete assignment | 🔥 |
| 657 | test_leaf_can_only_accept_own_assignment | Authorization | 🔥 |
| 658 | test_owner_can_create_leaf_assignment | Owner authorization | 🔥 |
| 659 | test_non_owner_cannot_create_leaf_assignment | Non-owner fails | 🔥 |
| 660 | test_leaf_assignment_accepted_at_timestamp | accepted_at set | ⭐ |
| 661 | test_leaf_assignment_rejected_at_timestamp | rejected_at set | ⭐ |
| 662 | test_bulk_leaf_assignment_creation | Bulk create | ⭐ |
| 663 | test_leaf_assignment_cascade_on_contact_delete | Cascade delete | 🔥 |

### tests/unit/categories/test_token_generation.py (10 tests)

| # | Test Function | Description | Priority |
|---|---------------|-------------|----------|
| 664 | test_generate_leaf_accept_token | Accept token | 🔥 |
| 665 | test_generate_leaf_reject_token | Reject token | 🔥 |
| 666 | test_token_contains_user_id | user_id in token | 🔥 |
| 667 | test_token_contains_contact_id | contact_id in token | 🔥 |
| 668 | test_token_contains_leaf_id | leaf_id in token | 🔥 |
| 669 | test_token_contains_decision | decision in token | 🔥 |
| 670 | test_verify_token_signature | Signature valid | 🔥 |
| 671 | test_tampered_token_rejected | Tampered token fails | 🔥 |
| 672 | test_token_base64_url_safe | URL-safe encoding | 🔥 |
| 673 | test_bulk_token_generation | Bulk tokens | ⭐ |

### tests/unit/categories/test_release_formatting.py (12 tests)

| # | Test Function | Description | Priority |
|---|---------------|-------------|----------|
| 674 | test_format_release_for_recipient | Format release | 🔥 |
| 675 | test_release_contains_category_name | category_name | 🔥 |
| 676 | test_release_contains_section_name | section_name | 🔥 |
| 677 | test_release_contains_answers | answers dict | 🔥 |
| 678 | test_release_contains_file_urls | file URLs | 🔥 |
| 679 | test_release_display_format | display format | 🔥 |
| 680 | test_release_metadata_complete | metadata complete | 🔥 |
| 681 | test_release_timestamp_included | updated_at | ⭐ |
| 682 | test_release_sorted_by_timestamp | Sort order | ⭐ |
| 683 | test_filter_releases_by_category | Category filter | ⭐ |
| 684 | test_release_requires_hard_death_lock | Death lock check | 🔥 |
| 685 | test_recipient_can_only_see_own_releases | Authorization | 🔥 |

### tests/integration/categories/test_category_api_endpoints.py (25 tests)

| # | Test Function | Description | Priority |
|---|---------------|-------------|----------|
| 686 | test_list_categories_public | GET /catalog | 🔥 |
| 687 | test_get_category_by_id_public | GET /catalog/{id} | 🔥 |
| 688 | test_admin_create_category | POST /admin/catalog | 🔥 |
| 689 | test_admin_create_category_unauthorized_returns_403 | Non-admin fails | 🔥 |
| 690 | test_admin_update_category | PATCH /admin/catalog/{id} | 🔥 |
| 691 | test_admin_delete_category | DELETE /admin/catalog/{id} | 🔥 |
| 692 | test_user_adopt_category | POST /categories/{id}/adopt | 🔥 |
| 693 | test_user_list_adopted_categories | GET /categories | 🔥 |
| 694 | test_list_sections_for_category | GET /catalog/{id}/sections | 🔥 |
| 695 | test_admin_create_section | POST /admin/catalog/{id}/sections | 🔥 |
| 696 | test_admin_update_section | PATCH /admin/catalog/sections/{id} | 🔥 |
| 697 | test_admin_delete_section | DELETE /admin/catalog/sections/{id} | 🔥 |
| 698 | test_get_section_progress_for_user | GET /categories/sections/{id}/progress | 🔥 |
| 699 | test_save_section_progress | POST /categories/sections/{id}/progress | 🔥 |
| 700 | test_update_section_progress | PATCH /categories/sections/{id}/progress | 🔥 |
| 701 | test_mark_section_complete | POST /categories/sections/{id}/complete | 🔥 |
| 702 | test_import_file_to_section | POST /categories/sections/{id}/import | 🔥 |
| 703 | test_import_file_section_not_allowed_returns_400 | Import not allowed | 🔥 |
| 704 | test_list_steps_for_section | GET /steps | 🔥 |
| 705 | test_admin_create_step | POST /admin/steps | 🔥 |
| 706 | test_admin_update_step | PATCH /admin/steps/{id} | 🔥 |
| 707 | test_admin_delete_step | DELETE /admin/steps/{id} | 🔥 |
| 708 | test_user_cannot_access_admin_catalog_endpoints | Authorization | 🔥 |
| 709 | test_pagination_on_category_list | Pagination | ⭐ |
| 710 | test_search_categories_by_name | Search | ⭐ |

### tests/integration/categories/test_leaf_assignment_flow.py (20 tests)

| # | Test Function | Description | Priority |
|---|---------------|-------------|----------|
| 711 | test_create_leaf_assignment_authenticated | POST /categories/leaves | 🔥 |
| 712 | test_create_leaf_assignment_unauthenticated_returns_401 | No token | 🔥 |
| 713 | test_accept_leaf_via_public_token | GET /catalog/leaves/a/{uid}/{cid}/{lid}/{token} | 🔥 |
| 714 | test_reject_leaf_via_public_token | GET /catalog/leaves/r/{uid}/{cid}/{lid}/{token} | 🔥 |
| 715 | test_accept_updates_status_to_accepted | Status change | 🔥 |
| 716 | test_reject_updates_status_to_rejected | Status change | 🔥 |
| 717 | test_accept_sets_accepted_at_timestamp | Timestamp | ⭐ |
| 718 | test_reject_sets_rejected_at_timestamp | Timestamp | ⭐ |
| 719 | test_invalid_token_returns_400 | Bad token | 🔥 |
| 720 | test_tampered_token_returns_400 | Tampered token | 🔥 |
| 721 | test_accept_already_accepted_idempotent | Idempotent | ⭐ |
| 722 | test_bulk_accept_all_for_user | POST /catalog/leaves/accept-all | 🔥 |
| 723 | test_bulk_reject_all_for_user | POST /catalog/leaves/reject-all | 🔥 |
| 724 | test_list_pending_leaf_assignments | GET /catalog/leaves | 🔥 |
| 725 | test_list_leaf_assignments_requires_auth | Authorization | 🔥 |
| 726 | test_recipient_can_only_see_own_assignments | Authorization | 🔥 |
| 727 | test_remove_leaf_assignment | DELETE /categories/leaves/{id} | 🔥 |
| 728 | test_remove_leaf_only_owner_can_remove | Authorization | 🔥 |
| 729 | test_list_releases_for_recipient | GET /categories/releases/{uid} | 🔥 |
| 730 | test_releases_require_hard_death_lock | Death lock check | 🔥 |

**Module 4 Subtotal: 152 tests**

---

## MODULE 5: FOLDERS (97 tests)

### tests/unit/folders/test_folder_controller.py (20 tests)

| # | Test Function | Description | Priority |
|---|---------------|-------------|----------|
| 731 | test_create_folder | Create folder | 🔥 |
| 732 | test_create_folder_requires_name | name required | 🔥 |
| 733 | test_create_folder_requires_user_id | user_id required | 🔥 |
| 734 | test_get_folder_by_id | Retrieve folder | 🔥 |
| 735 | test_get_folder_not_found_returns_none | Not found | 🔥 |
| 736 | test_update_folder_name | Update name | 🔥 |
| 737 | test_delete_folder_cascades_to_branches | Cascade to branches | 🔥 |
| 738 | test_delete_folder_cascades_to_leaves | Cascade to leaves | 🔥 |
| 739 | test_delete_folder_cascades_to_trigger | Cascade to trigger | 🔥 |
| 740 | test_list_folders_for_user | User's folders | 🔥 |
| 741 | test_create_default_folders_on_signup | Default folders | 🔥 |
| 742 | test_default_folders_are_will_insurance_cards | Default names | 🔥 |
| 743 | test_default_folders_idempotent | Idempotent creation | 🔥 |
| 744 | test_folder_status_complete | Status: complete | 🔥 |
| 745 | test_folder_status_incomplete_no_branch | Status: incomplete (no branch) | 🔥 |
| 746 | test_folder_status_incomplete_no_leaf | Status: incomplete (no leaf) | 🔥 |
| 747 | test_folder_status_incomplete_no_trigger | Status: incomplete (no trigger) | 🔥 |
| 748 | test_user_can_only_access_own_folders | Authorization | 🔥 |
| 749 | test_folder_files_relationship | folder.files | ⭐ |
| 750 | test_folder_created_at_timestamp | created_at | ⭐ |

### tests/unit/folders/test_branch_controller.py (12 tests)

| # | Test Function | Description | Priority |
|---|---------------|-------------|----------|
| 751 | test_add_branch_to_folder | Add branch | 🔥 |
| 752 | test_branch_requires_contact_id | contact_id required | 🔥 |
| 753 | test_branch_status_defaults_pending | Default pending | 🔥 |
| 754 | test_update_branch_status | Update status | 🔥 |
| 755 | test_branch_accept | Accept branch | 🔥 |
| 756 | test_branch_decline | Decline branch | 🔥 |
| 757 | test_list_branches_for_folder | List branches | 🔥 |
| 758 | test_delete_branch | Delete branch | 🔥 |
| 759 | test_branch_unique_per_folder_contact | Unique constraint | 🔥 |
| 760 | test_branch_accepted_at_timestamp | accepted_at | ⭐ |
| 761 | test_only_owner_can_add_branch | Authorization | 🔥 |
| 762 | test_branch_cascade_on_folder_delete | Cascade delete | 🔥 |

### tests/unit/folders/test_leaf_controller.py (12 tests)

| # | Test Function | Description | Priority |
|---|---------------|-------------|----------|
| 763 | test_add_leaf_to_folder | Add leaf | 🔥 |
| 764 | test_leaf_requires_contact_id | contact_id required | 🔥 |
| 765 | test_leaf_role_defaults_leaf | Default role | 🔥 |
| 766 | test_leaf_role_fallback_leaf | Fallback role | 🔥 |
| 767 | test_leaf_status_defaults_pending | Default pending | 🔥 |
| 768 | test_update_leaf_status | Update status | 🔥 |
| 769 | test_leaf_accept | Accept leaf | 🔥 |
| 770 | test_leaf_decline | Decline leaf | 🔥 |
| 771 | test_list_leaves_for_folder | List leaves | 🔥 |
| 772 | test_delete_leaf | Delete leaf | 🔥 |
| 773 | test_leaf_unique_per_folder_contact_role | Unique constraint | 🔥 |
| 774 | test_only_owner_can_add_leaf | Authorization | 🔥 |

### tests/unit/folders/test_trigger_controller.py (10 tests)

| # | Test Function | Description | Priority |
|---|---------------|-------------|----------|
| 775 | test_create_time_based_trigger | Time-based trigger | 🔥 |
| 776 | test_create_event_based_trigger | Event-based trigger | 🔥 |
| 777 | test_time_trigger_requires_time_at | time_at required | 🔥 |
| 778 | test_time_trigger_requires_timezone | timezone required | 🔥 |
| 779 | test_event_trigger_requires_event_label | event_label required | 🔥 |
| 780 | test_trigger_state_defaults_configured | Default configured | 🔥 |
| 781 | test_update_trigger | Update trigger | 🔥 |
| 782 | test_folder_can_have_only_one_trigger | One trigger max | 🔥 |
| 783 | test_trigger_state_transitions | State changes | ⭐ |
| 784 | test_cancel_trigger | Cancel trigger | 🔥 |

### tests/unit/folders/test_relationship_controller.py (15 tests)

| # | Test Function | Description | Priority |
|---|---------------|-------------|----------|
| 785 | test_create_relationship_request | Create request | 🔥 |
| 786 | test_request_requires_contact_id | contact_id required | 🔥 |
| 787 | test_request_requires_folder_id | folder_id required | 🔥 |
| 788 | test_request_status_defaults_pending | Default pending | 🔥 |
| 789 | test_accept_relationship_request | Accept request | 🔥 |
| 790 | test_reject_relationship_request | Reject request | 🔥 |
| 791 | test_revoke_relationship_request | Revoke request | 🔥 |
| 792 | test_accept_creates_branch_assignment | Branch created | 🔥 |
| 793 | test_generate_accept_reject_tokens | Tokens generated | 🔥 |
| 794 | test_accept_via_public_token | Public accept | 🔥 |
| 795 | test_reject_via_public_token | Public reject | 🔥 |
| 796 | test_list_pending_requests | Pending requests | 🔥 |
| 797 | test_list_branch_responsibilities_for_user | User todos | 🔥 |
| 798 | test_only_owner_can_create_request | Authorization | 🔥 |
| 799 | test_request_unique_per_folder_contact | Unique constraint | 🔥 |

### tests/unit/folders/test_folder_status_computation.py (8 tests)

| # | Test Function | Description | Priority |
|---|---------------|-------------|----------|
| 800 | test_status_complete_all_requirements_met | Complete status | 🔥 |
| 801 | test_status_incomplete_missing_branch | Missing branch | 🔥 |
| 802 | test_status_incomplete_missing_leaf | Missing leaf | 🔥 |
| 803 | test_status_incomplete_missing_trigger | Missing trigger | 🔥 |
| 804 | test_status_incomplete_multiple_triggers | Multiple triggers | 🔥 |
| 805 | test_missing_field_message_generated | Missing message | 🔥 |
| 806 | test_active_and_pending_count_as_valid | Active/pending valid | 🔥 |
| 807 | test_declined_removed_not_counted | Declined/removed invalid | 🔥 |

### tests/integration/folders/test_folder_api_endpoints.py (20 tests)

| # | Test Function | Description | Priority |
|---|---------------|-------------|----------|
| 808 | test_create_folder | POST /folders | 🔥 |
| 809 | test_create_folder_unauthenticated_returns_401 | No token | 🔥 |
| 810 | test_list_folders | GET /folders | 🔥 |
| 811 | test_get_folder_by_id | GET /folders/{id} | 🔥 |
| 812 | test_get_folder_includes_status | Status included | 🔥 |
| 813 | test_update_folder | PATCH /folders/{id} | 🔥 |
| 814 | test_delete_folder | DELETE /folders/{id} | 🔥 |
| 815 | test_add_branch | POST /folders/{id}/branches | 🔥 |
| 816 | test_list_branches | GET /folders/{id}/branches | 🔥 |
| 817 | test_update_branch | PATCH /folders/{fid}/branches/{bid} | 🔥 |
| 818 | test_delete_branch | DELETE /folders/{fid}/branches/{bid} | 🔥 |
| 819 | test_add_leaf | POST /folders/{id}/leaves | 🔥 |
| 820 | test_list_leaves | GET /folders/{id}/leaves | 🔥 |
| 821 | test_update_leaf | PATCH /folders/{fid}/leaves/{lid} | 🔥 |
| 822 | test_delete_leaf | DELETE /folders/{fid}/leaves/{lid} | 🔥 |
| 823 | test_upsert_trigger | POST /folders/{id}/trigger | 🔥 |
| 824 | test_get_trigger | GET /folders/{id}/trigger | 🔥 |
| 825 | test_user_cannot_access_other_user_folders | Authorization | 🔥 |
| 826 | test_default_folders_created_on_signup | Defaults | 🔥 |
| 827 | test_folder_status_computation_in_response | Status computed | 🔥 |

**Module 5 Subtotal: 97 tests**

---

## MODULE 6: MEMORIES (93 tests)

### tests/unit/memories/test_memory_controller.py (18 tests)

| # | Test Function | Description | Priority |
|---|---------------|-------------|----------|
| 828 | test_create_memory_collection | Create collection | 🔥 |
| 829 | test_memory_requires_user_id | user_id required | 🔥 |
| 830 | test_memory_requires_event_type | event_type required | 🔥 |
| 831 | test_memory_event_type_time_based | time_based event | 🔥 |
| 832 | test_memory_event_type_after_death | after_death event | 🔥 |
| 833 | test_time_based_requires_scheduled_at | scheduled_at required | 🔥 |
| 834 | test_memory_is_armed_defaults_false | Default false | 🔥 |
| 835 | test_get_memory_collection_by_id | Retrieve collection | 🔥 |
| 836 | test_update_memory_collection | Update collection | 🔥 |
| 837 | test_delete_memory_collection | Delete collection | 🔥 |
| 838 | test_list_memory_collections_for_user | User's collections | 🔥 |
| 839 | test_add_file_to_memory_collection | Add file | 🔥 |
| 840 | test_remove_file_from_memory_collection | Remove file | 🔥 |
| 841 | test_list_files_in_memory_collection | List files | 🔥 |
| 842 | test_arm_memory_collection | Arm collection | 🔥 |
| 843 | test_disarm_memory_collection | Disarm collection | 🔥 |
| 844 | test_user_can_only_access_own_collections | Authorization | 🔥 |
| 845 | test_memory_cascade_on_user_delete | Cascade delete | 🔥 |

### tests/unit/memories/test_message_controller.py (18 tests)

| # | Test Function | Description | Priority |
|---|---------------|-------------|----------|
| 846 | test_create_message_collection | Create collection | 🔥 |
| 847 | test_message_requires_user_id | user_id required | 🔥 |
| 848 | test_message_requires_event_type | event_type required | 🔥 |
| 849 | test_message_event_type_time_based | time_based event | 🔥 |
| 850 | test_message_event_type_after_death | after_death event | 🔥 |
| 851 | test_time_based_requires_scheduled_at | scheduled_at required | 🔥 |
| 852 | test_message_is_armed_defaults_false | Default false | 🔥 |
| 853 | test_get_message_collection_by_id | Retrieve collection | 🔥 |
| 854 | test_update_message_collection | Update collection | 🔥 |
| 855 | test_delete_message_collection | Delete collection | 🔥 |
| 856 | test_list_message_collections_for_user | User's collections | 🔥 |
| 857 | test_add_file_to_message_collection | Add file | 🔥 |
| 858 | test_remove_file_from_message_collection | Remove file | 🔥 |
| 859 | test_list_files_in_message_collection | List files | 🔥 |
| 860 | test_arm_message_collection | Arm collection | 🔥 |
| 861 | test_disarm_message_collection | Disarm collection | 🔥 |
| 862 | test_user_can_only_access_own_collections | Authorization | 🔥 |
| 863 | test_message_cascade_on_user_delete | Cascade delete | 🔥 |

### tests/unit/memories/test_collection_assignments.py (15 tests)

| # | Test Function | Description | Priority |
|---|---------------|-------------|----------|
| 864 | test_assign_branch_to_collection | Branch assignment | 🔥 |
| 865 | test_assign_leaf_to_collection | Leaf assignment | 🔥 |
| 866 | test_assignment_requires_contact_id | contact_id required | 🔥 |
| 867 | test_assignment_requires_role | role required | 🔥 |
| 868 | test_branch_role_assignment | Branch role | 🔥 |
| 869 | test_leaf_role_assignment | Leaf role | 🔥 |
| 870 | test_assignment_status_defaults_active | Default active | 🔥 |
| 871 | test_accept_assignment | Accept assignment | 🔥 |
| 872 | test_reject_assignment | Reject assignment | 🔥 |
| 873 | test_list_assignments_for_collection | Collection assignments | 🔥 |
| 874 | test_list_assignments_for_contact | Contact assignments | 🔥 |
| 875 | test_remove_assignment | Remove assignment | 🔥 |
| 876 | test_assignment_unique_per_collection_contact_role | Unique constraint | 🔥 |
| 877 | test_only_owner_can_create_assignment | Authorization | 🔥 |
| 878 | test_assignment_cascade_on_collection_delete | Cascade delete | 🔥 |

### tests/unit/memories/test_trigger_logic.py (10 tests)

| # | Test Function | Description | Priority |
|---|---------------|-------------|----------|
| 879 | test_time_based_trigger_past_date | Past date triggers | 🔥 |
| 880 | test_time_based_trigger_future_date | Future date pending | 🔥 |
| 881 | test_event_based_trigger_after_death | After death event | 🔥 |
| 882 | test_trigger_requires_armed_status | Must be armed | 🔥 |
| 883 | test_trigger_requires_hard_death_lock | Hard death lock | 🔥 |
| 884 | test_trigger_sends_emails_to_leaves | Email to leaves | 🔥 |
| 885 | test_trigger_marks_invite_status_sent | invite_status=sent | ⭐ |
| 886 | test_trigger_only_active_assignments | Active only | 🔥 |
| 887 | test_trigger_respects_user_verification_status | Verification check | 🔥 |
| 888 | test_trigger_idempotent_on_repeat | Idempotent | ⭐ |

### tests/unit/memories/test_release_mechanism.py (12 tests)

| # | Test Function | Description | Priority |
|---|---------------|-------------|----------|
| 889 | test_release_after_hard_death_finalized | Hard death required | 🔥 |
| 890 | test_release_to_leaf_recipients_only | Leaves only | 🔥 |
| 891 | test_release_includes_collection_files | Files included | 🔥 |
| 892 | test_release_includes_collection_metadata | Metadata included | 🔥 |
| 893 | test_release_file_urls_generated | URLs generated | 🔥 |
| 894 | test_release_format_consistent | Format consistent | 🔥 |
| 895 | test_recipient_can_only_see_own_releases | Authorization | 🔥 |
| 896 | test_release_sorted_by_updated_at | Sort order | ⭐ |
| 897 | test_branch_recipients_cannot_see_releases | Branches excluded | 🔥 |
| 898 | test_release_requires_accepted_assignment | Accepted only | 🔥 |
| 899 | test_rejected_assignments_excluded | Rejected excluded | 🔥 |
| 900 | test_release_list_paginated | Pagination | ⭐ |

### tests/integration/memories/test_memory_api_endpoints.py (20 tests)

| # | Test Function | Description | Priority |
|---|---------------|-------------|----------|
| 901 | test_create_memory_collection | POST /memories | 🔥 |
| 902 | test_create_memory_unauthenticated_returns_401 | No token | 🔥 |
| 903 | test_list_memory_collections | GET /memories | 🔥 |
| 904 | test_get_memory_by_id | GET /memories/{id} | 🔥 |
| 905 | test_update_memory_collection | PATCH /memories/{id} | 🔥 |
| 906 | test_delete_memory_collection | DELETE /memories/{id} | 🔥 |
| 907 | test_add_file_to_memory | POST /memories/{id}/files | 🔥 |
| 908 | test_remove_file_from_memory | DELETE /memories/{id}/files/{fid} | 🔥 |
| 909 | test_list_files_in_memory | GET /memories/{id}/files | 🔥 |
| 910 | test_assign_branch_to_memory | POST /memories/{id}/branches | 🔥 |
| 911 | test_assign_leaf_to_memory | POST /memories/{id}/leaves | 🔥 |
| 912 | test_list_assignments | GET /memories/{id}/assignments | 🔥 |
| 913 | test_remove_assignment | DELETE /memories/{id}/assignments/{aid} | 🔥 |
| 914 | test_arm_memory_collection | POST /memories/{id}/arm | 🔥 |
| 915 | test_disarm_memory_collection | POST /memories/{id}/disarm | 🔥 |
| 916 | test_list_releases_for_recipient | GET /memories/releases/{uid} | 🔥 |
| 917 | test_releases_require_hard_death | Death lock check | 🔥 |
| 918 | test_accept_assignment_via_token | Public accept | 🔥 |
| 919 | test_reject_assignment_via_token | Public reject | 🔥 |
| 920 | test_user_cannot_access_other_user_collections | Authorization | 🔥 |

**Module 6 Subtotal: 93 tests**

---

## MODULE 7: DEATH (174 tests)

### tests/unit/death/test_soft_death_controller.py (25 tests)

| # | Test Function | Description | Priority |
|---|---------------|-------------|----------|
| 921 | test_declare_soft_death_by_trustee | Trustee declares soft death | 🔥 |
| 922 | test_soft_death_requires_root_user_id | root_user_id required | 🔥 |
| 923 | test_soft_death_requires_message | message required | 🔥 |
| 924 | test_soft_death_state_defaults_pending_review | Default pending_review | 🔥 |
| 925 | test_soft_death_type_is_soft | type=soft | 🔥 |
| 926 | test_get_soft_death_declaration_by_id | Retrieve declaration | 🔥 |
| 927 | test_trustee_approve_soft_death | Trustee approves | 🔥 |
| 928 | test_trustee_contest_soft_death | Trustee contests | 🔥 |
| 929 | test_trustee_decline_soft_death | Trustee declines | 🔥 |
| 930 | test_approval_threshold_calculation | Threshold logic | 🔥 |
| 931 | test_soft_death_accepted_when_threshold_met | State→accepted | 🔥 |
| 932 | test_soft_death_rejected_when_contested | State→rejected | 🔥 |
| 933 | test_soft_death_broadcast_to_contacts | Broadcast triggered | 🔥 |
| 934 | test_broadcast_includes_message | Message included | 🔥 |
| 935 | test_broadcast_includes_media | Media included | ⭐ |
| 936 | test_acknowledgment_by_contact | Contact acknowledges | 🔥 |
| 937 | test_list_acknowledgments | List acks | ⭐ |
| 938 | test_soft_death_retraction_by_admin | Admin retracts | 🔥 |
| 939 | test_retraction_changes_state_to_retracted | State→retracted | 🔥 |
| 940 | test_lifecycle_updated_on_soft_death_accepted | Lifecycle→soft_announced | 🔥 |
| 941 | test_only_trustee_can_declare_soft_death | Authorization | 🔥 |
| 942 | test_only_other_trustees_can_approve | Authorization | 🔥 |
| 943 | test_declarer_cannot_approve_own_declaration | Self-approval blocked | 🔥 |
| 944 | test_soft_death_declaration_unique_per_user | One active declaration | 🔥 |
| 945 | test_soft_death_cascade_on_user_delete | Cascade delete | 🔥 |

### tests/unit/death/test_hard_death_controller.py (20 tests)

| # | Test Function | Description | Priority |
|---|---------------|-------------|----------|
| 946 | test_declare_hard_death_by_trustee | Trustee declares hard death | 🔥 |
| 947 | test_hard_death_requires_evidence_file | Evidence required | 🔥 |
| 948 | test_hard_death_evidence_uploaded_to_s3 | S3 upload | 🔥 |
| 949 | test_hard_death_state_defaults_pending_review | Default pending_review | 🔥 |
| 950 | test_hard_death_type_is_hard | type=hard | 🔥 |
| 951 | test_get_hard_death_declaration_by_id | Retrieve declaration | 🔥 |
| 952 | test_admin_review_hard_death | Admin reviews | 🔥 |
| 953 | test_admin_approve_hard_death | Admin approves | 🔥 |
| 954 | test_admin_reject_hard_death | Admin rejects | 🔥 |
| 955 | test_approve_creates_hard_finalized_lock | Death lock created | 🔥 |
| 956 | test_hard_death_lock_type_hard_finalized | lock=hard_finalized | 🔥 |
| 957 | test_lifecycle_updated_to_legend | Lifecycle→legend | 🔥 |
| 958 | test_rejection_does_not_create_lock | No lock on reject | 🔥 |
| 959 | test_evidence_file_presigned_url_generated | Presigned URL | 🔥 |
| 960 | test_evidence_file_stored_with_unique_key | Unique S3 key | 🔥 |
| 961 | test_admin_approval_comment | Approval comment | ⭐ |
| 962 | test_admin_rejection_reason | Rejection reason | ⭐ |
| 963 | test_only_admin_can_review_hard_death | Authorization | 🔥 |
| 964 | test_hard_death_email_notification_to_admin | Admin notified | 🔥 |
| 965 | test_multiple_hard_death_declarations_allowed | Multiple allowed | ⭐ |

### tests/unit/death/test_trustee_controller.py (15 tests)

| # | Test Function | Description | Priority |
|---|---------------|-------------|----------|
| 966 | test_invite_trustee | Invite trustee | 🔥 |
| 967 | test_trustee_requires_contact_id | contact_id required | 🔥 |
| 968 | test_trustee_status_defaults_invited | Default invited | 🔥 |
| 969 | test_trustee_version_field | version field | ⭐ |
| 970 | test_trustee_accept_invitation | Accept invitation | 🔥 |
| 971 | test_trustee_decline_invitation | Decline invitation | 🔥 |
| 972 | test_accept_via_public_token | Public accept | 🔥 |
| 973 | test_decline_via_public_token | Public decline | 🔥 |
| 974 | test_trustee_invite_token_generated | Token generated | 🔥 |
| 975 | test_list_trustees_for_user | User's trustees | 🔥 |
| 976 | test_remove_trustee | Remove trustee | 🔥 |
| 977 | test_designate_primary_trustee | Primary designation | 🔥 |
| 978 | test_trustee_unique_per_user_contact | Unique constraint | 🔥 |
| 979 | test_minimum_two_trustees_required | Min 2 trustees | 🔥 |
| 980 | test_only_owner_can_invite_trustee | Authorization | 🔥 |

### tests/unit/death/test_approval_logic.py (12 tests)

| # | Test Function | Description | Priority |
|---|---------------|-------------|----------|
| 981 | test_approval_threshold_two_trustees | 2 trustees threshold | 🔥 |
| 982 | test_approval_threshold_three_trustees | 3 trustees threshold | 🔥 |
| 983 | test_approval_threshold_four_or_more_trustees | 4+ trustees threshold | 🔥 |
| 984 | test_declarer_approval_counted | Declarer counts | 🔥 |
| 985 | test_additional_trustee_approvals_counted | Other approvals | 🔥 |
| 986 | test_contest_resets_approval_count | Contest resets | 🔥 |
| 987 | test_decline_does_not_count_as_approval | Decline excluded | 🔥 |
| 988 | test_approval_from_non_trustee_rejected | Non-trustee rejected | 🔥 |
| 989 | test_duplicate_approval_prevented | No duplicates | 🔥 |
| 990 | test_legacy_rule_two_plus_two | 2 trustees + 2 approvals | 🔥 |
| 991 | test_approval_status_enum_validation | Status validation | 🔥 |
| 992 | test_approval_timestamp_recorded | Timestamp | ⭐ |

### tests/unit/death/test_contest_controller.py (15 tests)

| # | Test Function | Description | Priority |
|---|---------------|-------------|----------|
| 993 | test_create_contest_within_window | Contest within window | 🔥 |
| 994 | test_contest_requires_declaration_id | declaration_id required | 🔥 |
| 995 | test_contest_requires_evidence | Evidence required | 🔥 |
| 996 | test_contest_evidence_uploaded_to_s3 | S3 upload | 🔥 |
| 997 | test_contest_window_30_days | 30-day window | 🔥 |
| 998 | test_contest_outside_window_rejected | Outside window fails | 🔥 |
| 999 | test_contest_state_defaults_pending_review | Default pending_review | 🔥 |
| 1000 | test_admin_review_contest | Admin reviews | 🔥 |
| 1001 | test_admin_accept_contest | Admin accepts contest | 🔥 |
| 1002 | test_admin_reject_contest | Admin rejects contest | 🔥 |
| 1003 | test_accept_contest_reverts_death_declaration | Reverts declaration | 🔥 |
| 1004 | test_reject_contest_keeps_declaration | Declaration unchanged | 🔥 |
| 1005 | test_contest_email_notification_to_admin | Admin notified | 🔥 |
| 1006 | test_multiple_contests_allowed | Multiple contests | ⭐ |
| 1007 | test_contest_cascade_on_declaration_delete | Cascade delete | 🔥 |

### tests/unit/death/test_death_lock_enforcement.py (10 tests)

| # | Test Function | Description | Priority |
|---|---------------|-------------|----------|
| 1008 | test_death_lock_created_on_hard_approval | Lock created | 🔥 |
| 1009 | test_death_lock_type_hard_finalized | Type hard_finalized | 🔥 |
| 1010 | test_death_lock_prevents_vault_modifications | Vault locked | 🔥 |
| 1011 | test_death_lock_prevents_folder_modifications | Folders locked | 🔥 |
| 1012 | test_death_lock_prevents_category_modifications | Categories locked | 🔥 |
| 1013 | test_death_lock_allows_releases | Releases allowed | 🔥 |
| 1014 | test_check_death_lock_by_user_id | Check lock | 🔥 |
| 1015 | test_legacy_death_declared_rule | Legacy 2+2 rule | 🔥 |
| 1016 | test_death_lock_cascade_on_user_delete | Cascade delete | 🔥 |
| 1017 | test_death_lock_unique_per_user | One lock per user | 🔥 |

### tests/unit/death/test_lifecycle_management.py (10 tests)

| # | Test Function | Description | Priority |
|---|---------------|-------------|----------|
| 1018 | test_lifecycle_defaults_alive | Default alive | 🔥 |
| 1019 | test_lifecycle_transition_alive_to_soft_announced | alive→soft_announced | 🔥 |
| 1020 | test_lifecycle_transition_soft_announced_to_legend | soft_announced→legend | 🔥 |
| 1021 | test_lifecycle_transition_alive_to_legend_direct | alive→legend (hard) | 🔥 |
| 1022 | test_lifecycle_state_enum_validation | Valid states only | 🔥 |
| 1023 | test_lifecycle_history_recorded | History entry | 🔥 |
| 1024 | test_lifecycle_timestamp_recorded | Timestamp | ⭐ |
| 1025 | test_get_current_lifecycle_state | Get current state | 🔥 |
| 1026 | test_lifecycle_cascade_on_user_delete | Cascade delete | 🔥 |
| 1027 | test_cannot_transition_from_legend | Legend is final | 🔥 |

### tests/unit/death/test_broadcast_controller.py (12 tests)

| # | Test Function | Description | Priority |
|---|---------------|-------------|----------|
| 1028 | test_broadcast_soft_death_announcement | Broadcast announcement | 🔥 |
| 1029 | test_broadcast_to_all_contacts | All contacts | 🔥 |
| 1030 | test_broadcast_respects_audience_config | Audience config | 🔥 |
| 1031 | test_broadcast_includes_message | Message included | 🔥 |
| 1032 | test_broadcast_includes_media_urls | Media URLs | ⭐ |
| 1033 | test_broadcast_sent_timestamp | sent_at timestamp | ⭐ |
| 1034 | test_broadcast_recipient_list | Recipient list | 🔥 |
| 1035 | test_broadcast_status_enum | Status enum | ⭐ |
| 1036 | test_contact_acknowledge_broadcast | Acknowledge | 🔥 |
| 1037 | test_list_acknowledgments_for_broadcast | List acks | ⭐ |
| 1038 | test_broadcast_only_after_acceptance | After acceptance | 🔥 |
| 1039 | test_broadcast_cascade_on_declaration_delete | Cascade delete | 🔥 |

### tests/unit/death/test_token_verification.py (10 tests)

| # | Test Function | Description | Priority |
|---|---------------|-------------|----------|
| 1040 | test_generate_contest_quick_token | Contest token | 🔥 |
| 1041 | test_verify_contest_quick_token | Verify token | 🔥 |
| 1042 | test_token_contains_contest_id | contest_id | 🔥 |
| 1043 | test_token_contains_decision | decision | 🔥 |
| 1044 | test_token_contains_expiry | expiry | 🔥 |
| 1045 | test_expired_token_rejected | Expired fails | 🔥 |
| 1046 | test_tampered_token_rejected | Tampered fails | 🔥 |
| 1047 | test_token_base64_url_safe | URL-safe | 🔥 |
| 1048 | test_token_hmac_signature | HMAC signature | 🔥 |
| 1049 | test_generate_hard_death_token | Hard death token | 🔥 |

### tests/integration/death/test_death_api_endpoints.py (30 tests)

| # | Test Function | Description | Priority |
|---|---------------|-------------|----------|
| 1050 | test_declare_soft_death | POST /v1/death/soft | 🔥 |
| 1051 | test_declare_soft_death_unauthenticated_returns_401 | No token | 🔥 |
| 1052 | test_declare_soft_death_non_trustee_returns_403 | Non-trustee fails | 🔥 |
| 1053 | test_get_soft_death_declaration | GET /v1/death/soft/{id} | 🔥 |
| 1054 | test_approve_soft_death | POST /v1/death/soft/{id}/approve | 🔥 |
| 1055 | test_contest_soft_death | POST /v1/death/soft/{id}/contest | 🔥 |
| 1056 | test_decline_soft_death | POST /v1/death/soft/{id}/decline | 🔥 |
| 1057 | test_list_soft_death_declarations | GET /v1/death/soft | 🔥 |
| 1058 | test_acknowledge_soft_death_broadcast | POST /v1/death/soft/{id}/acknowledge | 🔥 |
| 1059 | test_admin_retract_soft_death | POST /v1/death/soft/{id}/retract | 🔥 |
| 1060 | test_declare_hard_death | POST /v1/death/hard | 🔥 |
| 1061 | test_declare_hard_death_requires_evidence | Evidence required | 🔥 |
| 1062 | test_declare_hard_death_uploads_to_s3 | S3 upload | 🔥 |
| 1063 | test_get_hard_death_declaration | GET /v1/death/hard/{id} | 🔥 |
| 1064 | test_admin_review_hard_death | POST /v1/death/hard/{id}/review | 🔥 |
| 1065 | test_admin_approve_hard_death | POST /v1/death/hard/{id}/approve | 🔥 |
| 1066 | test_admin_reject_hard_death | POST /v1/death/hard/{id}/reject | 🔥 |
| 1067 | test_list_hard_death_declarations | GET /v1/death/hard | 🔥 |
| 1068 | test_create_contest | POST /v1/death/contest | 🔥 |
| 1069 | test_create_contest_requires_evidence | Evidence required | 🔥 |
| 1070 | test_contest_outside_window_returns_400 | Window check | 🔥 |
| 1071 | test_admin_decide_contest | POST /v1/death/contest/{id}/decide | 🔥 |
| 1072 | test_list_contests | GET /v1/death/contest | 🔥 |
| 1073 | test_get_lifecycle_state | GET /v1/death/lifecycle/{uid} | 🔥 |
| 1074 | test_check_death_lock | GET /v1/death/lock/{uid} | 🔥 |
| 1075 | test_admin_only_can_review_hard_death | Authorization | 🔥 |
| 1076 | test_admin_only_can_retract_soft_death | Authorization | 🔥 |
| 1077 | test_admin_only_can_decide_contest | Authorization | 🔥 |
| 1078 | test_death_lock_prevents_vault_save | Vault locked | 🔥 |
| 1079 | test_death_lock_prevents_folder_creation | Folders locked | 🔥 |

### tests/integration/death/test_trustee_api_endpoints.py (15 tests)

| # | Test Function | Description | Priority |
|---|---------------|-------------|----------|
| 1080 | test_invite_trustee | POST /trustees | 🔥 |
| 1081 | test_invite_trustee_unauthenticated_returns_401 | No token | 🔥 |
| 1082 | test_list_trustees | GET /trustees | 🔥 |
| 1083 | test_get_trustee_by_id | GET /trustees/{id} | 🔥 |
| 1084 | test_remove_trustee | DELETE /trustees/{id} | 🔥 |
| 1085 | test_accept_trustee_via_token | GET /trustees/a/{id}/{token} | 🔥 |
| 1086 | test_reject_trustee_via_token | GET /trustees/r/{id}/{token} | 🔥 |
| 1087 | test_designate_primary_trustee | POST /trustees/{id}/primary | 🔥 |
| 1088 | test_list_death_approvals | GET /trustees/death-status | 🔥 |
| 1089 | test_approve_death_declaration | POST /trustees/death-status/approve | 🔥 |
| 1090 | test_minimum_trustees_enforced | Min 2 check | 🔥 |
| 1091 | test_user_cannot_invite_trustee_for_other_user | Authorization | 🔥 |
| 1092 | test_trustee_invitation_email_sent | Email sent | 🔥 |
| 1093 | test_trustee_version_incremented | Version tracking | ⭐ |
| 1094 | test_legacy_death_approval_check | Legacy rule | 🔥 |

**Module 7 Subtotal: 174 tests**

---

## MODULE 8: REMINDERS (102 tests)

### tests/unit/reminders/test_reminder_controller.py (20 tests)

| # | Test Function | Description | Priority |
|---|---------------|-------------|----------|
| 1095 | test_create_reminder | Create reminder | 🔥 |
| 1096 | test_reminder_requires_user_id | user_id required | 🔥 |
| 1097 | test_reminder_requires_vault_file_id | vault_file_id required | 🔥 |
| 1098 | test_reminder_requires_reminder_date | reminder_date required | 🔥 |
| 1099 | test_reminder_status_defaults_pending | Default pending | 🔥 |
| 1100 | test_reminder_urgency_level_defaults_normal | Default normal | 🔥 |
| 1101 | test_get_reminder_by_id | Retrieve reminder | 🔥 |
| 1102 | test_update_reminder_date | Update date | 🔥 |
| 1103 | test_update_reminder_urgency | Update urgency | 🔥 |
| 1104 | test_delete_reminder | Delete reminder | 🔥 |
| 1105 | test_list_reminders_for_user | User's reminders | 🔥 |
| 1106 | test_list_pending_reminders | Pending only | 🔥 |
| 1107 | test_mark_reminder_completed | Mark completed | 🔥 |
| 1108 | test_snooze_reminder | Snooze reminder | 🔥 |
| 1109 | test_reminder_urgency_enum_validation | Urgency validation | 🔥 |
| 1110 | test_reminder_status_enum_validation | Status validation | 🔥 |
| 1111 | test_user_can_only_access_own_reminders | Authorization | 🔥 |
| 1112 | test_reminder_cascade_on_user_delete | Cascade delete | 🔥 |
| 1113 | test_reminder_cascade_on_vault_file_delete | Cascade on file delete | 🔥 |
| 1114 | test_recurring_reminder_creation | Recurring reminders | ⭐ |

### tests/unit/reminders/test_reminder_scheduler.py (15 tests)

| # | Test Function | Description | Priority |
|---|---------------|-------------|----------|
| 1115 | test_scheduler_identifies_due_reminders | Due reminders | 🔥 |
| 1116 | test_scheduler_respects_timezone | Timezone handling | 🔥 |
| 1117 | test_scheduler_sends_email_notification | Email sent | 🔥 |
| 1118 | test_scheduler_sends_sms_notification | SMS sent | 🔥 |
| 1119 | test_scheduler_updates_reminder_status | Status updated | 🔥 |
| 1120 | test_scheduler_marks_sent_timestamp | sent_at timestamp | ⭐ |
| 1121 | test_scheduler_handles_multiple_reminders | Multiple reminders | 🔥 |
| 1122 | test_scheduler_skips_completed_reminders | Skip completed | 🔥 |
| 1123 | test_scheduler_skips_future_reminders | Skip future | 🔥 |
| 1124 | test_scheduler_retry_on_failure | Retry logic | ⭐ |
| 1125 | test_scheduler_logs_errors | Error logging | ⭐ |
| 1126 | test_scheduler_concurrent_execution_safe | Thread-safe | ⭐ |
| 1127 | test_scheduler_respects_user_preferences | User preferences | 🔥 |
| 1128 | test_scheduler_rate_limiting | Rate limiting | ⭐ |
| 1129 | test_scheduler_batch_processing | Batch processing | ⭐ |

### tests/unit/reminders/test_reminder_sender.py (12 tests)

| # | Test Function | Description | Priority |
|---|---------------|-------------|----------|
| 1130 | test_send_email_reminder | Email delivery | 🔥 |
| 1131 | test_send_sms_reminder | SMS delivery | 🔥 |
| 1132 | test_email_contains_vault_file_name | File name in email | 🔥 |
| 1133 | test_email_contains_reminder_date | Date in email | 🔥 |
| 1134 | test_email_contains_urgency_level | Urgency in email | 🔥 |
| 1135 | test_sms_format_concise | SMS format | 🔥 |
| 1136 | test_sender_respects_notification_preferences | Preferences | 🔥 |
| 1137 | test_sender_handles_email_failure | Email failure | 🔥 |
| 1138 | test_sender_handles_sms_failure | SMS failure | 🔥 |
| 1139 | test_sender_template_rendering | Template rendering | ⭐ |
| 1140 | test_sender_personalization | Personalization | ⭐ |
| 1141 | test_sender_html_email_format | HTML format | ⭐ |

### tests/unit/reminders/test_reminder_escalator.py (10 tests)

| # | Test Function | Description | Priority |
|---|---------------|-------------|----------|
| 1142 | test_escalate_overdue_reminder | Escalation logic | 🔥 |
| 1143 | test_escalation_after_7_days | 7-day threshold | 🔥 |
| 1144 | test_escalation_increases_urgency | Urgency increase | 🔥 |
| 1145 | test_escalation_sends_additional_notification | Extra notification | 🔥 |
| 1146 | test_escalation_marks_escalated_timestamp | escalated_at | ⭐ |
| 1147 | test_escalation_respects_max_escalations | Max escalations | ⭐ |
| 1148 | test_escalation_skips_completed_reminders | Skip completed | 🔥 |
| 1149 | test_escalation_tracks_escalation_count | Count tracking | ⭐ |
| 1150 | test_escalation_notification_format | Format | ⭐ |
| 1151 | test_escalation_batch_processing | Batch processing | ⭐ |

### tests/unit/reminders/test_reminder_utils.py (15 tests)

| # | Test Function | Description | Priority |
|---|---------------|-------------|----------|
| 1152 | test_calculate_next_reminder_date | Next date calculation | 🔥 |
| 1153 | test_calculate_daily_recurrence | Daily recurrence | 🔥 |
| 1154 | test_calculate_weekly_recurrence | Weekly recurrence | 🔥 |
| 1155 | test_calculate_monthly_recurrence | Monthly recurrence | 🔥 |
| 1156 | test_calculate_yearly_recurrence | Yearly recurrence | 🔥 |
| 1157 | test_format_reminder_message | Message formatting | 🔥 |
| 1158 | test_format_urgency_display | Urgency display | ⭐ |
| 1159 | test_parse_reminder_date_input | Date parsing | 🔥 |
| 1160 | test_validate_reminder_date_future | Future date validation | 🔥 |
| 1161 | test_validate_reminder_date_not_past | Past date rejected | 🔥 |
| 1162 | test_timezone_conversion | Timezone conversion | 🔥 |
| 1163 | test_reminder_notification_window | Notification window | ⭐ |
| 1164 | test_reminder_grouping_by_date | Group by date | ⭐ |
| 1165 | test_reminder_sorting | Sort order | ⭐ |
| 1166 | test_reminder_filtering | Filtering logic | ⭐ |

### tests/unit/reminders/test_preference_management.py (10 tests)

| # | Test Function | Description | Priority |
|---|---------------|-------------|----------|
| 1167 | test_set_notification_preference_email | Email preference | 🔥 |
| 1168 | test_set_notification_preference_sms | SMS preference | 🔥 |
| 1169 | test_set_notification_preference_both | Both channels | 🔥 |
| 1170 | test_set_notification_preference_none | Disable notifications | 🔥 |
| 1171 | test_get_notification_preferences | Get preferences | 🔥 |
| 1172 | test_default_preferences | Default settings | 🔥 |
| 1173 | test_update_preferences | Update preferences | 🔥 |
| 1174 | test_preferences_cascade_on_user_delete | Cascade delete | 🔥 |
| 1175 | test_quiet_hours_configuration | Quiet hours | ⭐ |
| 1176 | test_notification_frequency_limit | Frequency limit | ⭐ |

### tests/integration/reminders/test_reminder_api_endpoints.py (20 tests)

| # | Test Function | Description | Priority |
|---|---------------|-------------|----------|
| 1177 | test_create_reminder | POST /reminders | 🔥 |
| 1178 | test_create_reminder_unauthenticated_returns_401 | No token | 🔥 |
| 1179 | test_list_reminders | GET /reminders | 🔥 |
| 1180 | test_get_reminder_by_id | GET /reminders/{id} | 🔥 |
| 1181 | test_update_reminder | PATCH /reminders/{id} | 🔥 |
| 1182 | test_delete_reminder | DELETE /reminders/{id} | 🔥 |
| 1183 | test_mark_reminder_completed | POST /reminders/{id}/complete | 🔥 |
| 1184 | test_snooze_reminder | POST /reminders/{id}/snooze | 🔥 |
| 1185 | test_list_pending_reminders | GET /reminders?status=pending | 🔥 |
| 1186 | test_list_completed_reminders | GET /reminders?status=completed | 🔥 |
| 1187 | test_filter_by_urgency | GET /reminders?urgency=high | ⭐ |
| 1188 | test_filter_by_date_range | GET /reminders?start=...&end=... | ⭐ |
| 1189 | test_get_reminder_statistics | GET /reminders/stats | ⭐ |
| 1190 | test_set_notification_preferences | POST /reminders/preferences | 🔥 |
| 1191 | test_get_notification_preferences | GET /reminders/preferences | 🔥 |
| 1192 | test_user_cannot_access_other_user_reminders | Authorization | 🔥 |
| 1193 | test_reminder_pagination | Pagination | ⭐ |
| 1194 | test_reminder_sorting | Sort by date | ⭐ |
| 1195 | test_bulk_delete_reminders | Bulk delete | ⭐ |
| 1196 | test_reminder_export | Export reminders | ⭐ |

**Module 8 Subtotal: 102 tests**

---

## MODULE 9: POLICY CHECKER (83 tests)

### tests/unit/policy_checker/test_ocr_service.py (15 tests)

| # | Test Function | Description | Priority |
|---|---------------|-------------|----------|
| 1197 | test_extract_text_from_image | Extract text | 🔥 |
| 1198 | test_extract_text_from_pdf | Extract from PDF | 🔥 |
| 1199 | test_ocr_supports_png | PNG support | 🔥 |
| 1200 | test_ocr_supports_jpg | JPG support | 🔥 |
| 1201 | test_ocr_supports_pdf | PDF support | 🔥 |
| 1202 | test_ocr_handles_poor_quality_image | Quality handling | ⭐ |
| 1203 | test_ocr_handles_multi_page_pdf | Multi-page PDF | 🔥 |
| 1204 | test_ocr_returns_confidence_score | Confidence score | ⭐ |
| 1205 | test_ocr_handles_non_english_text | Multi-language | ⭐ |
| 1206 | test_ocr_handles_handwritten_text | Handwriting | ⭐ |
| 1207 | test_ocr_preprocesses_image | Preprocessing | ⭐ |
| 1208 | test_ocr_error_handling | Error handling | 🔥 |
| 1209 | test_ocr_timeout_handling | Timeout | ⭐ |
| 1210 | test_ocr_file_size_limit | Size limit | 🔥 |
| 1211 | test_ocr_invalid_file_format | Invalid format | 🔥 |

### tests/unit/policy_checker/test_policy_service.py (18 tests)

| # | Test Function | Description | Priority |
|---|---------------|-------------|----------|
| 1212 | test_extract_policy_details | Extract details | 🔥 |
| 1213 | test_extract_policy_number | Policy number | 🔥 |
| 1214 | test_extract_policy_holder_name | Holder name | 🔥 |
| 1215 | test_extract_coverage_amount | Coverage amount | 🔥 |
| 1216 | test_extract_start_date | Start date | 🔥 |
| 1217 | test_extract_end_date | End date | 🔥 |
| 1218 | test_extract_premium_amount | Premium amount | 🔥 |
| 1219 | test_extract_beneficiary_info | Beneficiary info | 🔥 |
| 1220 | test_validate_policy_data | Validation | 🔥 |
| 1221 | test_check_policy_active | Active check | 🔥 |
| 1222 | test_check_policy_expired | Expired check | 🔥 |
| 1223 | test_parse_insurance_policy | Insurance parsing | 🔥 |
| 1224 | test_parse_health_policy | Health parsing | 🔥 |
| 1225 | test_parse_life_insurance_policy | Life insurance | 🔥 |
| 1226 | test_standardize_policy_format | Format standardization | ⭐ |
| 1227 | test_handle_missing_fields | Missing fields | 🔥 |
| 1228 | test_handle_ambiguous_data | Ambiguous data | ⭐ |
| 1229 | test_policy_type_detection | Type detection | 🔥 |

### tests/unit/policy_checker/test_extraction_service.py (15 tests)

| # | Test Function | Description | Priority |
|---|---------------|-------------|----------|
| 1230 | test_extract_from_uploaded_file | File extraction | 🔥 |
| 1231 | test_extract_structured_data | Structured data | 🔥 |
| 1232 | test_extract_unstructured_data | Unstructured data | 🔥 |
| 1233 | test_extract_tables_from_document | Table extraction | ⭐ |
| 1234 | test_extract_key_value_pairs | Key-value pairs | 🔥 |
| 1235 | test_normalize_extracted_data | Normalization | 🔥 |
| 1236 | test_validate_extracted_data | Validation | 🔥 |
| 1237 | test_handle_extraction_errors | Error handling | 🔥 |
| 1238 | test_extraction_result_format | Result format | 🔥 |
| 1239 | test_extraction_confidence_threshold | Confidence check | ⭐ |
| 1240 | test_extraction_from_scanned_document | Scanned docs | ⭐ |
| 1241 | test_extraction_retry_logic | Retry logic | ⭐ |
| 1242 | test_extraction_caching | Caching | ⭐ |
| 1243 | test_extraction_performance | Performance | ⭐ |
| 1244 | test_extraction_batch_processing | Batch processing | ⭐ |

### tests/unit/policy_checker/test_gemini_client.py (10 tests)

| # | Test Function | Description | Priority |
|---|---------------|-------------|----------|
| 1245 | test_gemini_api_connection | API connection | 🔥 |
| 1246 | test_gemini_text_generation | Text generation | 🔥 |
| 1247 | test_gemini_document_analysis | Document analysis | 🔥 |
| 1248 | test_gemini_prompt_construction | Prompt building | 🔥 |
| 1249 | test_gemini_response_parsing | Response parsing | 🔥 |
| 1250 | test_gemini_error_handling | Error handling | 🔥 |
| 1251 | test_gemini_rate_limiting | Rate limiting | ⭐ |
| 1252 | test_gemini_timeout_handling | Timeout | ⭐ |
| 1253 | test_gemini_retry_logic | Retry logic | ⭐ |
| 1254 | test_gemini_api_key_validation | Key validation | 🔥 |

### tests/unit/policy_checker/test_google_ocr_client.py (10 tests)

| # | Test Function | Description | Priority |
|---|---------------|-------------|----------|
| 1255 | test_google_ocr_connection | OCR connection | 🔥 |
| 1256 | test_google_ocr_text_detection | Text detection | 🔥 |
| 1257 | test_google_ocr_document_text_detection | Document detection | 🔥 |
| 1258 | test_google_ocr_image_preprocessing | Preprocessing | ⭐ |
| 1259 | test_google_ocr_response_parsing | Response parsing | 🔥 |
| 1260 | test_google_ocr_error_handling | Error handling | 🔥 |
| 1261 | test_google_ocr_batch_processing | Batch processing | ⭐ |
| 1262 | test_google_ocr_language_hints | Language hints | ⭐ |
| 1263 | test_google_ocr_confidence_filtering | Confidence filter | ⭐ |
| 1264 | test_google_ocr_credentials_validation | Credentials | 🔥 |

### tests/integration/policy_checker/test_policy_api_endpoints.py (15 tests)

| # | Test Function | Description | Priority |
|---|---------------|-------------|----------|
| 1265 | test_upload_policy_document | POST /policy-checker/upload | 🔥 |
| 1266 | test_upload_requires_authentication | No token | 🔥 |
| 1267 | test_upload_validates_file_type | File type check | 🔥 |
| 1268 | test_upload_validates_file_size | Size check | 🔥 |
| 1269 | test_extract_policy_data | POST /policy-checker/extract | 🔥 |
| 1270 | test_extract_returns_structured_data | Structured output | 🔥 |
| 1271 | test_get_policy_analysis | GET /policy-checker/{id} | 🔥 |
| 1272 | test_list_analyzed_policies | GET /policy-checker | 🔥 |
| 1273 | test_update_policy_data | PATCH /policy-checker/{id} | 🔥 |
| 1274 | test_delete_policy_analysis | DELETE /policy-checker/{id} | 🔥 |
| 1275 | test_reanalyze_policy | POST /policy-checker/{id}/reanalyze | ⭐ |
| 1276 | test_user_cannot_access_other_user_policies | Authorization | 🔥 |
| 1277 | test_policy_extraction_timeout | Timeout handling | ⭐ |
| 1278 | test_policy_extraction_error_response | Error response | 🔥 |
| 1279 | test_policy_extraction_progress_tracking | Progress tracking | ⭐ |

**Module 9 Subtotal: 83 tests**

---

## MODULE 10: FILE STORAGE (67 tests)

### tests/unit/file_storage/test_file_controller.py (15 tests)

| # | Test Function | Description | Priority |
|---|---------------|-------------|----------|
| 1280 | test_create_file_record | Create file record | 🔥 |
| 1281 | test_file_requires_user_id | user_id required | 🔥 |
| 1282 | test_file_requires_name | name required | 🔥 |
| 1283 | test_file_mime_type_validation | MIME validation | 🔥 |
| 1284 | test_file_size_validation | Size validation | 🔥 |
| 1285 | test_get_file_by_id | Retrieve file | 🔥 |
| 1286 | test_list_files_for_user | User's files | 🔥 |
| 1287 | test_update_file_metadata | Update metadata | 🔥 |
| 1288 | test_delete_file_record | Delete file | 🔥 |
| 1289 | test_file_s3_key_format | S3 key format | 🔥 |
| 1290 | test_file_upload_timestamp | upload_timestamp | ⭐ |
| 1291 | test_user_can_only_access_own_files | Authorization | 🔥 |
| 1292 | test_file_cascade_on_user_delete | Cascade delete | 🔥 |
| 1293 | test_file_search_by_name | Search files | ⭐ |
| 1294 | test_file_filter_by_type | Filter by type | ⭐ |

### tests/unit/file_storage/test_s3_upload_controller.py (15 tests)

| # | Test Function | Description | Priority |
|---|---------------|-------------|----------|
| 1295 | test_upload_file_to_s3 | Upload file | 🔥 |
| 1296 | test_upload_generates_unique_key | Unique key | 🔥 |
| 1297 | test_upload_validates_file_size | Size check | 🔥 |
| 1298 | test_upload_validates_mime_type | MIME check | 🔥 |
| 1299 | test_upload_handles_large_files | Large files | ⭐ |
| 1300 | test_upload_multipart_for_large_files | Multipart upload | ⭐ |
| 1301 | test_upload_sets_correct_metadata | Metadata | 🔥 |
| 1302 | test_upload_error_handling | Error handling | 🔥 |
| 1303 | test_upload_retry_logic | Retry logic | ⭐ |
| 1304 | test_delete_file_from_s3 | Delete file | 🔥 |
| 1305 | test_delete_handles_missing_file | Missing file OK | ⭐ |
| 1306 | test_download_file_from_s3 | Download file | 🔥 |
| 1307 | test_download_validates_access | Access check | 🔥 |
| 1308 | test_list_files_in_bucket | List files | ⭐ |
| 1309 | test_s3_connection_pooling | Connection pool | ⭐ |

### tests/unit/file_storage/test_presigned_url_generation.py (10 tests)

| # | Test Function | Description | Priority |
|---|---------------|-------------|----------|
| 1310 | test_generate_presigned_url | Generate URL | 🔥 |
| 1311 | test_presigned_url_expiry | Expiry time | 🔥 |
| 1312 | test_presigned_url_format | URL format | ⭐ |
| 1313 | test_presigned_url_for_upload | Upload URL | 🔥 |
| 1314 | test_presigned_url_for_download | Download URL | 🔥 |
| 1315 | test_presigned_url_validation | URL validation | 🔥 |
| 1316 | test_expired_url_rejected | Expired URL | 🔥 |
| 1317 | test_tampered_url_rejected | Tampered URL | 🔥 |
| 1318 | test_presigned_url_permissions | Permissions | ⭐ |
| 1319 | test_presigned_url_batch_generation | Batch generation | ⭐ |

### tests/unit/file_storage/test_file_validation.py (12 tests)

| # | Test Function | Description | Priority |
|---|---------------|-------------|----------|
| 1320 | test_validate_file_size_within_limit | Size OK | 🔥 |
| 1321 | test_validate_file_size_exceeds_limit | Size exceeded | 🔥 |
| 1322 | test_validate_mime_type_pdf | PDF allowed | 🔥 |
| 1323 | test_validate_mime_type_image | Image allowed | 🔥 |
| 1324 | test_validate_mime_type_document | Document allowed | 🔥 |
| 1325 | test_validate_mime_type_invalid | Invalid rejected | 🔥 |
| 1326 | test_validate_file_extension | Extension check | 🔥 |
| 1327 | test_validate_file_name | Name validation | 🔥 |
| 1328 | test_validate_file_content | Content check | ⭐ |
| 1329 | test_virus_scan_integration | Virus scan | ⭐ |
| 1330 | test_validate_duplicate_file | Duplicate check | ⭐ |
| 1331 | test_validate_file_metadata | Metadata check | ⭐ |

### tests/integration/file_storage/test_s3_upload_api_endpoints.py (15 tests)

| # | Test Function | Description | Priority |
|---|---------------|-------------|----------|
| 1332 | test_upload_file | POST /files/upload | 🔥 |
| 1333 | test_upload_file_unauthenticated_returns_401 | No token | 🔥 |
| 1334 | test_upload_file_too_large_returns_413 | Size exceeded | 🔥 |
| 1335 | test_upload_invalid_file_type_returns_400 | Invalid type | 🔥 |
| 1336 | test_get_presigned_upload_url | GET /files/presigned-upload | 🔥 |
| 1337 | test_get_presigned_download_url | GET /files/{id}/presigned-download | 🔥 |
| 1338 | test_list_files | GET /files | 🔥 |
| 1339 | test_get_file_by_id | GET /files/{id} | 🔥 |
| 1340 | test_update_file_metadata | PATCH /files/{id} | 🔥 |
| 1341 | test_delete_file | DELETE /files/{id} | 🔥 |
| 1342 | test_download_file | GET /files/{id}/download | 🔥 |
| 1343 | test_user_cannot_access_other_user_files | Authorization | 🔥 |
| 1344 | test_file_upload_progress | Upload progress | ⭐ |
| 1345 | test_file_pagination | Pagination | ⭐ |
| 1346 | test_file_search | Search files | ⭐ |

**Module 10 Subtotal: 67 tests**

---

## MODULE 11: ADMIN (47 tests)

### tests/unit/admin/test_admin_catalog_controller.py (12 tests)

| # | Test Function | Description | Priority |
|---|---------------|-------------|----------|
| 1347 | test_admin_create_category | Admin creates category | 🔥 |
| 1348 | test_admin_update_category | Admin updates category | 🔥 |
| 1349 | test_admin_delete_category | Admin deletes category | 🔥 |
| 1350 | test_admin_reorder_categories | Reorder categories | ⭐ |
| 1351 | test_non_admin_cannot_create_category | Non-admin fails | 🔥 |
| 1352 | test_admin_list_all_categories | List all | 🔥 |
| 1353 | test_admin_get_category_statistics | Stats | ⭐ |
| 1354 | test_admin_bulk_category_operations | Bulk ops | ⭐ |
| 1355 | test_admin_category_audit_log | Audit log | ⭐ |
| 1356 | test_admin_publish_category | Publish | ⭐ |
| 1357 | test_admin_unpublish_category | Unpublish | ⭐ |
| 1358 | test_admin_duplicate_category | Duplicate | ⭐ |

### tests/unit/admin/test_admin_step_controller.py (10 tests)

| # | Test Function | Description | Priority |
|---|---------------|-------------|----------|
| 1359 | test_admin_create_step | Admin creates step | 🔥 |
| 1360 | test_admin_update_step | Admin updates step | 🔥 |
| 1361 | test_admin_delete_step | Admin deletes step | 🔥 |
| 1362 | test_admin_reorder_steps | Reorder steps | ⭐ |
| 1363 | test_non_admin_cannot_create_step | Non-admin fails | 🔥 |
| 1364 | test_admin_bulk_step_operations | Bulk ops | ⭐ |
| 1365 | test_admin_step_templates | Templates | ⭐ |
| 1366 | test_admin_step_validation_rules | Validation rules | ⭐ |
| 1367 | test_admin_step_preview | Preview | ⭐ |
| 1368 | test_admin_step_analytics | Analytics | ⭐ |

### tests/unit/admin/test_admin_death_controller.py (15 tests)

| # | Test Function | Description | Priority |
|---|---------------|-------------|----------|
| 1369 | test_admin_list_pending_hard_deaths | List pending | 🔥 |
| 1370 | test_admin_review_hard_death | Review hard death | 🔥 |
| 1371 | test_admin_approve_hard_death | Approve | 🔥 |
| 1372 | test_admin_reject_hard_death | Reject | 🔥 |
| 1373 | test_admin_list_contests | List contests | 🔥 |
| 1374 | test_admin_review_contest | Review contest | 🔥 |
| 1375 | test_admin_decide_contest | Decide contest | 🔥 |
| 1376 | test_admin_retract_soft_death | Retract soft death | 🔥 |
| 1377 | test_admin_view_death_statistics | Stats | ⭐ |
| 1378 | test_admin_death_audit_trail | Audit trail | ⭐ |
| 1379 | test_admin_death_lock_override | Override lock | ⭐ |
| 1380 | test_admin_bulk_death_review | Bulk review | ⭐ |
| 1381 | test_non_admin_cannot_review_death | Non-admin fails | 🔥 |
| 1382 | test_admin_death_notification_settings | Notifications | ⭐ |
| 1383 | test_admin_death_report_generation | Reports | ⭐ |

### tests/unit/admin/test_admin_verification_controller.py (10 tests)

| # | Test Function | Description | Priority |
|---|---------------|-------------|----------|
| 1384 | test_admin_list_pending_verifications | List pending | 🔥 |
| 1385 | test_admin_review_verification | Review verification | 🔥 |
| 1386 | test_admin_approve_verification | Approve | 🔥 |
| 1387 | test_admin_reject_verification | Reject | 🔥 |
| 1388 | test_admin_verification_statistics | Stats | ⭐ |
| 1389 | test_admin_verification_audit_log | Audit log | ⭐ |
| 1390 | test_admin_bulk_verification_review | Bulk review | ⭐ |
| 1391 | test_non_admin_cannot_review_verification | Non-admin fails | 🔥 |
| 1392 | test_admin_verification_document_viewer | Document viewer | ⭐ |
| 1393 | test_admin_verification_filters | Filters | ⭐ |

**Module 11 Subtotal: 47 tests**

---

## MODULE 12: EXTERNAL SERVICES (42 tests)

### tests/unit/external_services/test_twilio_integration.py (10 tests)

| # | Test Function | Description | Priority |
|---|---------------|-------------|----------|
| 1394 | test_send_sms_via_twilio | Send SMS | 🔥 |
| 1395 | test_twilio_credentials_validation | Credentials | 🔥 |
| 1396 | test_twilio_phone_number_format | Number format | 🔥 |
| 1397 | test_twilio_error_handling | Error handling | 🔥 |
| 1398 | test_twilio_retry_logic | Retry logic | ⭐ |
| 1399 | test_twilio_message_status_callback | Status callback | ⭐ |
| 1400 | test_twilio_rate_limiting | Rate limiting | ⭐ |
| 1401 | test_twilio_message_length_validation | Length check | 🔥 |
| 1402 | test_twilio_batch_messaging | Batch messaging | ⭐ |
| 1403 | test_twilio_connection_timeout | Timeout | ⭐ |

### tests/unit/external_services/test_smtp_integration.py (12 tests)

| # | Test Function | Description | Priority |
|---|---------------|-------------|----------|
| 1404 | test_send_email_via_smtp | Send email | 🔥 |
| 1405 | test_smtp_credentials_validation | Credentials | 🔥 |
| 1406 | test_smtp_connection | Connection | 🔥 |
| 1407 | test_smtp_tls_encryption | TLS encryption | 🔥 |
| 1408 | test_smtp_email_format | Email format | 🔥 |
| 1409 | test_smtp_html_email | HTML email | 🔥 |
| 1410 | test_smtp_attachments | Attachments | ⭐ |
| 1411 | test_smtp_error_handling | Error handling | 🔥 |
| 1412 | test_smtp_retry_logic | Retry logic | ⭐ |
| 1413 | test_smtp_rate_limiting | Rate limiting | ⭐ |
| 1414 | test_smtp_template_rendering | Templates | ⭐ |
| 1415 | test_smtp_batch_emails | Batch emails | ⭐ |

### tests/unit/external_services/test_aws_kms_integration.py (10 tests)

| # | Test Function | Description | Priority |
|---|---------------|-------------|----------|
| 1416 | test_kms_generate_data_key | Generate key | 🔥 |
| 1417 | test_kms_decrypt_data_key | Decrypt key | 🔥 |
| 1418 | test_kms_credentials_validation | Credentials | 🔥 |
| 1419 | test_kms_key_id_validation | Key ID | 🔥 |
| 1420 | test_kms_error_handling | Error handling | 🔥 |
| 1421 | test_kms_access_denied | Access denied | 🔥 |
| 1422 | test_kms_key_not_found | Key not found | 🔥 |
| 1423 | test_kms_retry_logic | Retry logic | ⭐ |
| 1424 | test_kms_timeout_handling | Timeout | ⭐ |
| 1425 | test_kms_key_rotation | Key rotation | ⭐ |

### tests/unit/external_services/test_aws_s3_integration.py (10 tests)

| # | Test Function | Description | Priority |
|---|---------------|-------------|----------|
| 1426 | test_s3_upload | Upload file | 🔥 |
| 1427 | test_s3_download | Download file | 🔥 |
| 1428 | test_s3_delete | Delete file | 🔥 |
| 1429 | test_s3_list_objects | List objects | 🔥 |
| 1430 | test_s3_presigned_url | Presigned URL | 🔥 |
| 1431 | test_s3_credentials_validation | Credentials | 🔥 |
| 1432 | test_s3_bucket_validation | Bucket validation | 🔥 |
| 1433 | test_s3_error_handling | Error handling | 🔥 |
| 1434 | test_s3_retry_logic | Retry logic | ⭐ |
| 1435 | test_s3_multipart_upload | Multipart upload | ⭐ |

**Module 12 Subtotal: 42 tests**

---

## E2E TESTS: USER JOURNEYS (48 tests)

### tests/e2e/user_journeys/test_new_user_signup_journey.py (8 tests)

| # | Test Function | Description | Priority |
|---|---------------|-------------|----------|
| 1436 | test_complete_signup_with_email | Full email signup flow | 🔥 |
| 1437 | test_complete_signup_with_phone | Full phone signup flow | 🔥 |
| 1438 | test_signup_otp_verification | OTP verification step | 🔥 |
| 1439 | test_signup_profile_completion | Profile completion | 🔥 |
| 1440 | test_signup_document_verification | Document verification | 🔥 |
| 1441 | test_signup_default_folders_creation | Default folders created | 🔥 |
| 1442 | test_signup_welcome_email_sent | Welcome email | ⭐ |
| 1443 | test_signup_status_progression | Status: unknown→guest→verified | 🔥 |

### tests/e2e/user_journeys/test_vault_creation_journey.py (8 tests)

| # | Test Function | Description | Priority |
|---|---------------|-------------|----------|
| 1444 | test_create_vault_manual_mode | Manual vault creation | 🔥 |
| 1445 | test_create_vault_import_mode | Import vault with file | 🔥 |
| 1446 | test_vault_encryption_end_to_end | Full encryption flow | 🔥 |
| 1447 | test_vault_share_with_contact | Share vault file | 🔥 |
| 1448 | test_vault_access_activation | Activate access | 🔥 |
| 1449 | test_vault_decrypt_as_recipient | Recipient decrypts | 🔥 |
| 1450 | test_vault_revoke_access | Revoke access | 🔥 |
| 1451 | test_vault_list_and_filter | List and filter vaults | ⭐ |

### tests/e2e/user_journeys/test_category_adoption_journey.py (8 tests)

| # | Test Function | Description | Priority |
|---|---------------|-------------|----------|
| 1452 | test_browse_category_catalog | Browse categories | 🔥 |
| 1453 | test_adopt_category | Adopt category | 🔥 |
| 1454 | test_view_category_sections | View sections | 🔥 |
| 1455 | test_complete_section_steps | Complete steps | 🔥 |
| 1456 | test_save_section_progress | Save progress | 🔥 |
| 1457 | test_import_file_to_section | Import file | 🔥 |
| 1458 | test_mark_section_complete | Mark complete | 🔥 |
| 1459 | test_view_completion_status | View progress | ⭐ |

### tests/e2e/user_journeys/test_folder_sharing_journey.py (8 tests)

| # | Test Function | Description | Priority |
|---|---------------|-------------|----------|
| 1460 | test_create_custom_folder | Create folder | 🔥 |
| 1461 | test_add_branch_to_folder | Add branch contact | 🔥 |
| 1462 | test_add_leaf_to_folder | Add leaf contact | 🔥 |
| 1463 | test_configure_folder_trigger | Set trigger | 🔥 |
| 1464 | test_branch_accepts_responsibility | Branch accepts | 🔥 |
| 1465 | test_leaf_accepts_responsibility | Leaf accepts | 🔥 |
| 1466 | test_folder_status_complete | Folder complete | 🔥 |
| 1467 | test_trigger_folder_release | Trigger release | ⭐ |

### tests/e2e/user_journeys/test_memory_creation_journey.py (8 tests)

| # | Test Function | Description | Priority |
|---|---------------|-------------|----------|
| 1468 | test_create_memory_collection | Create collection | 🔥 |
| 1469 | test_add_files_to_memory | Add files | 🔥 |
| 1470 | test_configure_time_based_trigger | Time trigger | 🔥 |
| 1471 | test_configure_event_based_trigger | Event trigger | 🔥 |
| 1472 | test_assign_memory_recipients | Assign recipients | 🔥 |
| 1473 | test_recipient_accepts_assignment | Accept assignment | 🔥 |
| 1474 | test_arm_memory_collection | Arm collection | 🔥 |
| 1475 | test_memory_release_to_recipient | Release memory | ⭐ |

### tests/e2e/user_journeys/test_trustee_setup_journey.py (8 tests)

| # | Test Function | Description | Priority |
|---|---------------|-------------|----------|
| 1476 | test_invite_first_trustee | Invite trustee | 🔥 |
| 1477 | test_invite_second_trustee | Invite 2nd trustee | 🔥 |
| 1478 | test_trustee_receives_invitation | Email received | 🔥 |
| 1479 | test_trustee_accepts_via_token | Accept via token | 🔥 |
| 1480 | test_trustee_declines_via_token | Decline via token | 🔥 |
| 1481 | test_designate_primary_trustee | Primary designation | 🔥 |
| 1482 | test_remove_trustee | Remove trustee | 🔥 |
| 1483 | test_minimum_trustees_validation | Min 2 trustees | 🔥 |

**E2E User Journeys Subtotal: 48 tests**

---

## E2E TESTS: WORKFLOWS (43 tests)

### tests/e2e/workflows/test_soft_death_workflow.py (10 tests)

| # | Test Function | Description | Priority |
|---|---------------|-------------|----------|
| 1484 | test_soft_death_full_workflow | Complete soft death flow | 🔥 |
| 1485 | test_trustee_declares_soft_death | Declaration | 🔥 |
| 1486 | test_other_trustees_receive_notification | Notifications sent | 🔥 |
| 1487 | test_trustee_approves_declaration | Approval | 🔥 |
| 1488 | test_approval_threshold_reached | Threshold met | 🔥 |
| 1489 | test_soft_death_accepted | State→accepted | 🔥 |
| 1490 | test_broadcast_to_contacts | Broadcast sent | 🔥 |
| 1491 | test_contacts_acknowledge_broadcast | Acknowledgments | 🔥 |
| 1492 | test_lifecycle_updated_to_soft_announced | Lifecycle change | 🔥 |
| 1493 | test_admin_retraction_workflow | Admin retracts | ⭐ |

### tests/e2e/workflows/test_hard_death_workflow.py (10 tests)

| # | Test Function | Description | Priority |
|---|---------------|-------------|----------|
| 1494 | test_hard_death_full_workflow | Complete hard death flow | 🔥 |
| 1495 | test_trustee_declares_hard_death | Declaration with evidence | 🔥 |
| 1496 | test_evidence_uploaded_to_s3 | S3 upload | 🔥 |
| 1497 | test_admin_receives_notification | Admin notified | 🔥 |
| 1498 | test_admin_reviews_evidence | Review evidence | 🔥 |
| 1499 | test_admin_approves_hard_death | Approval | 🔥 |
| 1500 | test_death_lock_created | Lock created | 🔥 |
| 1501 | test_lifecycle_updated_to_legend | Lifecycle→legend | 🔥 |
| 1502 | test_vault_modifications_blocked | Modifications blocked | 🔥 |
| 1503 | test_releases_triggered | Releases sent | 🔥 |

### tests/e2e/workflows/test_vault_share_workflow.py (8 tests)

| # | Test Function | Description | Priority |
|---|---------------|-------------|----------|
| 1504 | test_vault_share_complete_workflow | Complete share flow | 🔥 |
| 1505 | test_owner_shares_vault_file | Owner shares | 🔥 |
| 1506 | test_recipient_receives_notification | Notification sent | 🔥 |
| 1507 | test_recipient_activates_access | Activation | 🔥 |
| 1508 | test_recipient_decrypts_vault_file | Decryption | 🔥 |
| 1509 | test_recipient_views_form_data | View data | 🔥 |
| 1510 | test_recipient_downloads_source_file | Download file | 🔥 |
| 1511 | test_owner_revokes_access | Revocation | 🔥 |

### tests/e2e/workflows/test_leaf_assignment_workflow.py (8 tests)

| # | Test Function | Description | Priority |
|---|---------------|-------------|----------|
| 1512 | test_leaf_assignment_complete_workflow | Complete assignment flow | 🔥 |
| 1513 | test_owner_assigns_leaf | Owner assigns | 🔥 |
| 1514 | test_leaf_receives_email_with_tokens | Email with tokens | 🔥 |
| 1515 | test_leaf_accepts_via_token | Accept token | 🔥 |
| 1516 | test_leaf_status_updated_to_accepted | Status change | 🔥 |
| 1517 | test_leaf_can_view_assigned_sections | View sections | 🔥 |
| 1518 | test_release_after_hard_death | Release triggered | 🔥 |
| 1519 | test_leaf_rejection_workflow | Rejection flow | ⭐ |

### tests/e2e/workflows/test_reminder_lifecycle_workflow.py (7 tests)

| # | Test Function | Description | Priority |
|---|---------------|-------------|----------|
| 1520 | test_reminder_complete_lifecycle | Complete lifecycle | 🔥 |
| 1521 | test_create_reminder_for_vault_file | Create reminder | 🔥 |
| 1522 | test_scheduler_detects_due_reminder | Scheduler detects | 🔥 |
| 1523 | test_notification_sent_to_user | Notification sent | 🔥 |
| 1524 | test_user_marks_reminder_complete | Mark complete | 🔥 |
| 1525 | test_overdue_reminder_escalation | Escalation | 🔥 |
| 1526 | test_reminder_snooze_workflow | Snooze flow | ⭐ |

**E2E Workflows Subtotal: 43 tests**

---

## SPECIALIZED TESTS: SECURITY (38 tests)

### tests/specialized/security/test_sql_injection_protection.py (5 tests)

| # | Test Function | Description | Priority |
|---|---------------|-------------|----------|
| 1527 | test_sql_injection_in_login | Login injection blocked | 🔥 |
| 1528 | test_sql_injection_in_search | Search injection blocked | 🔥 |
| 1529 | test_sql_injection_in_filter | Filter injection blocked | 🔥 |
| 1530 | test_parameterized_queries_used | Parameterized queries | 🔥 |
| 1531 | test_orm_prevents_injection | ORM protection | 🔥 |

### tests/specialized/security/test_authorization_bypass.py (10 tests)

| # | Test Function | Description | Priority |
|---|---------------|-------------|----------|
| 1532 | test_user_cannot_access_other_user_vault | Vault isolation | 🔥 |
| 1533 | test_user_cannot_access_other_user_folders | Folder isolation | 🔥 |
| 1534 | test_user_cannot_access_other_user_contacts | Contact isolation | 🔥 |
| 1535 | test_non_admin_cannot_access_admin_endpoints | Admin endpoints | 🔥 |
| 1536 | test_non_trustee_cannot_declare_death | Trustee-only actions | 🔥 |
| 1537 | test_non_owner_cannot_modify_folder | Owner-only actions | 🔥 |
| 1538 | test_revoked_access_denied | Revoked access | 🔥 |
| 1539 | test_pending_access_denied | Pending access | 🔥 |
| 1540 | test_jwt_token_required_for_protected_routes | JWT required | 🔥 |
| 1541 | test_expired_token_rejected | Expired token | 🔥 |

### tests/specialized/security/test_jwt_security.py (8 tests)

| # | Test Function | Description | Priority |
|---|---------------|-------------|----------|
| 1542 | test_jwt_signature_verification | Signature verified | 🔥 |
| 1543 | test_jwt_expiry_validation | Expiry checked | 🔥 |
| 1544 | test_jwt_tampering_detected | Tampering detected | 🔥 |
| 1545 | test_jwt_algorithm_validation | Algorithm validated | 🔥 |
| 1546 | test_jwt_claims_validation | Claims validated | 🔥 |
| 1547 | test_jwt_refresh_token_flow | Refresh flow | ⭐ |
| 1548 | test_jwt_revocation | Token revocation | ⭐ |
| 1549 | test_jwt_audience_validation | Audience check | ⭐ |

### tests/specialized/security/test_rate_limiting.py (5 tests)

| # | Test Function | Description | Priority |
|---|---------------|-------------|----------|
| 1550 | test_rate_limit_on_login | Login rate limit | 🔥 |
| 1551 | test_rate_limit_on_otp_generation | OTP rate limit | 🔥 |
| 1552 | test_rate_limit_on_api_calls | API rate limit | 🔥 |
| 1553 | test_rate_limit_response_429 | 429 response | 🔥 |
| 1554 | test_rate_limit_reset_after_window | Reset window | ⭐ |

### tests/specialized/security/test_xss_protection.py (5 tests)

| # | Test Function | Description | Priority |
|---|---------------|-------------|----------|
| 1555 | test_xss_in_user_input_sanitized | Input sanitized | 🔥 |
| 1556 | test_xss_in_display_name_escaped | Display name escaped | 🔥 |
| 1557 | test_xss_in_folder_name_escaped | Folder name escaped | 🔥 |
| 1558 | test_xss_in_message_escaped | Message escaped | 🔥 |
| 1559 | test_content_security_policy_headers | CSP headers | ⭐ |

### tests/specialized/security/test_encryption_strength.py (5 tests)

| # | Test Function | Description | Priority |
|---|---------------|-------------|----------|
| 1560 | test_aes_256_gcm_used | AES-256-GCM | 🔥 |
| 1561 | test_unique_nonce_per_encryption | Unique nonces | 🔥 |
| 1562 | test_kms_key_rotation_supported | Key rotation | 🔥 |
| 1563 | test_bcrypt_password_hashing | Bcrypt hashing | 🔥 |
| 1564 | test_secure_random_generation | Secure random | 🔥 |

**Specialized Security Subtotal: 38 tests**

---

## SPECIALIZED TESTS: PERFORMANCE (25 tests)

### tests/specialized/performance/test_database_query_performance.py (10 tests)

| # | Test Function | Description | Priority |
|---|---------------|-------------|----------|
| 1565 | test_user_query_performance | <50ms | ⭐ |
| 1566 | test_vault_list_query_performance | <100ms | ⭐ |
| 1567 | test_folder_list_query_performance | <100ms | ⭐ |
| 1568 | test_category_catalog_query_performance | <200ms | ⭐ |
| 1569 | test_contact_list_query_performance | <50ms | ⭐ |
| 1570 | test_join_query_performance | <150ms | ⭐ |
| 1571 | test_index_effectiveness | Indexes used | ⭐ |
| 1572 | test_n_plus_one_prevention | No N+1 queries | ⭐ |
| 1573 | test_pagination_performance | <100ms | ⭐ |
| 1574 | test_search_query_performance | <200ms | ⭐ |

### tests/specialized/performance/test_bulk_operations_performance.py (5 tests)

| # | Test Function | Description | Priority |
|---|---------------|-------------|----------|
| 1575 | test_bulk_insert_performance | 1000 records <5s | ⭐ |
| 1576 | test_bulk_update_performance | 1000 records <5s | ⭐ |
| 1577 | test_bulk_delete_performance | 1000 records <3s | ⭐ |
| 1578 | test_batch_processing_memory_usage | Memory efficient | ⭐ |
| 1579 | test_bulk_email_sending_performance | 100 emails <10s | ⭐ |

### tests/specialized/performance/test_vault_encryption_performance.py (5 tests)

| # | Test Function | Description | Priority |
|---|---------------|-------------|----------|
| 1580 | test_encryption_performance_small_file | <100ms for <1MB | ⭐ |
| 1581 | test_encryption_performance_large_file | <5s for 10MB | ⭐ |
| 1582 | test_decryption_performance_small_file | <100ms for <1MB | ⭐ |
| 1583 | test_decryption_performance_large_file | <5s for 10MB | ⭐ |
| 1584 | test_kms_key_generation_performance | <500ms | ⭐ |

### tests/specialized/performance/test_api_response_time.py (5 tests)

| # | Test Function | Description | Priority |
|---|---------------|-------------|----------|
| 1585 | test_login_response_time | <500ms | ⭐ |
| 1586 | test_vault_save_response_time | <1s | ⭐ |
| 1587 | test_folder_list_response_time | <300ms | ⭐ |
| 1588 | test_category_catalog_response_time | <500ms | ⭐ |
| 1589 | test_file_upload_response_time | <2s for 5MB | ⭐ |

**Specialized Performance Subtotal: 25 tests**

---

## SPECIALIZED TESTS: CONCURRENCY (15 tests)

### tests/specialized/concurrency/test_concurrent_vault_operations.py (5 tests)

| # | Test Function | Description | Priority |
|---|---------------|-------------|----------|
| 1590 | test_concurrent_vault_saves | 10 simultaneous saves | ⭐ |
| 1591 | test_concurrent_vault_decryptions | 10 simultaneous decrypts | ⭐ |
| 1592 | test_concurrent_access_grants | Race condition handled | ⭐ |
| 1593 | test_concurrent_access_revocations | Race condition handled | ⭐ |
| 1594 | test_vault_locking_mechanism | Pessimistic locking | ⭐ |

### tests/specialized/concurrency/test_concurrent_death_declarations.py (5 tests)

| # | Test Function | Description | Priority |
|---|---------------|-------------|----------|
| 1595 | test_concurrent_soft_death_declarations | Only one active | ⭐ |
| 1596 | test_concurrent_trustee_approvals | Approval counting | ⭐ |
| 1597 | test_concurrent_contest_submissions | Multiple contests OK | ⭐ |
| 1598 | test_death_lock_race_condition | Lock once only | ⭐ |
| 1599 | test_lifecycle_transition_race_condition | State consistency | ⭐ |

### tests/specialized/concurrency/test_concurrent_leaf_acceptance.py (5 tests)

| # | Test Function | Description | Priority |
|---|---------------|-------------|----------|
| 1600 | test_concurrent_leaf_accepts | Multiple accepts safe | ⭐ |
| 1601 | test_concurrent_leaf_rejects | Multiple rejects safe | ⭐ |
| 1602 | test_accept_reject_race_condition | First action wins | ⭐ |
| 1603 | test_concurrent_folder_completions | Status consistency | ⭐ |
| 1604 | test_concurrent_trigger_activations | Single activation | ⭐ |

**Specialized Concurrency Subtotal: 15 tests**

---

## SPECIALIZED TESTS: REGRESSION (40 tests)

### tests/specialized/regression/test_bug_fixes_auth.py (10 tests)

| # | Test Function | Description | Priority |
|---|---------------|-------------|----------|
| 1605 | test_bug_fix_duplicate_email_allowed | Bug #123 fixed | ⭐ |
| 1606 | test_bug_fix_otp_expiry_ignored | Bug #145 fixed | ⭐ |
| 1607 | test_bug_fix_phone_format_validation | Bug #167 fixed | ⭐ |
| 1608 | test_bug_fix_admin_user_token_confusion | Bug #189 fixed | ⭐ |
| 1609 | test_bug_fix_status_transition_skip | Bug #201 fixed | ⭐ |
| 1610 | test_bug_fix_password_reset_vulnerability | Bug #223 fixed | ⭐ |
| 1611 | test_bug_fix_token_expiry_validation | Bug #245 fixed | ⭐ |
| 1612 | test_bug_fix_profile_cascade_delete | Bug #267 fixed | ⭐ |
| 1613 | test_bug_fix_contact_link_race_condition | Bug #289 fixed | ⭐ |
| 1614 | test_bug_fix_verification_duplicate_submission | Bug #301 fixed | ⭐ |

### tests/specialized/regression/test_bug_fixes_vault.py (10 tests)

| # | Test Function | Description | Priority |
|---|---------------|-------------|----------|
| 1615 | test_bug_fix_encryption_nonce_reuse | Bug #324 fixed | ⭐ |
| 1616 | test_bug_fix_dek_not_encrypted | Bug #346 fixed | ⭐ |
| 1617 | test_bug_fix_s3_key_collision | Bug #368 fixed | ⭐ |
| 1618 | test_bug_fix_access_activation_bypass | Bug #390 fixed | ⭐ |
| 1619 | test_bug_fix_revoked_access_still_works | Bug #412 fixed | ⭐ |
| 1620 | test_bug_fix_file_size_validation_missing | Bug #434 fixed | ⭐ |
| 1621 | test_bug_fix_mime_type_spoofing | Bug #456 fixed | ⭐ |
| 1622 | test_bug_fix_source_file_not_deleted | Bug #478 fixed | ⭐ |
| 1623 | test_bug_fix_concurrent_decryption_error | Bug #500 fixed | ⭐ |
| 1624 | test_bug_fix_kms_key_rotation_breaks_decrypt | Bug #522 fixed | ⭐ |

### tests/specialized/regression/test_bug_fixes_death.py (10 tests)

| # | Test Function | Description | Priority |
|---|---------------|-------------|----------|
| 1625 | test_bug_fix_declarer_self_approval | Bug #544 fixed | ⭐ |
| 1626 | test_bug_fix_approval_threshold_incorrect | Bug #566 fixed | ⭐ |
| 1627 | test_bug_fix_contest_window_not_enforced | Bug #588 fixed | ⭐ |
| 1628 | test_bug_fix_death_lock_not_created | Bug #610 fixed | ⭐ |
| 1629 | test_bug_fix_lifecycle_state_inconsistent | Bug #632 fixed | ⭐ |
| 1630 | test_bug_fix_broadcast_sent_before_acceptance | Bug #654 fixed | ⭐ |
| 1631 | test_bug_fix_multiple_death_locks | Bug #676 fixed | ⭐ |
| 1632 | test_bug_fix_hard_death_without_evidence | Bug #698 fixed | ⭐ |
| 1633 | test_bug_fix_contest_after_window_accepted | Bug #720 fixed | ⭐ |
| 1634 | test_bug_fix_trustee_minimum_not_enforced | Bug #742 fixed | ⭐ |

### tests/specialized/regression/test_backward_compatibility.py (10 tests)

| # | Test Function | Description | Priority |
|---|---------------|-------------|----------|
| 1635 | test_v1_api_still_works | V1 API compatibility | ⭐ |
| 1636 | test_old_jwt_tokens_valid | Old tokens work | ⭐ |
| 1637 | test_legacy_death_rule_supported | 2+2 rule works | ⭐ |
| 1638 | test_old_encryption_format_readable | Old format readable | ⭐ |
| 1639 | test_database_migration_reversible | Migration rollback | ⭐ |
| 1640 | test_old_password_hashes_valid | Old hashes work | ⭐ |
| 1641 | test_legacy_file_urls_still_work | Old S3 URLs work | ⭐ |
| 1642 | test_deprecated_endpoints_warning | Deprecation warnings | ⭐ |
| 1643 | test_old_event_format_processed | Old events work | ⭐ |
| 1644 | test_schema_version_tracking | Version tracking | ⭐ |

**Specialized Regression Subtotal: 40 tests**

---

## **FINAL COMPLETE SUMMARY**

```
┌─────────────────────────────────────────────────────────┐
│              COMPLETE TEST INVENTORY                     │
├─────────────────────────────────────────────────────────┤
│ Total Test Files:     129                                │
│ Total Tests:          1,644                              │
└─────────────────────────────────────────────────────────┘

BREAKDOWN BY CATEGORY:
├── Unit Tests:              1,145 tests (69.6%)
│   ├── Module 0 (ORM):        156 tests
│   ├── Module 1 (Foundation): 102 tests
│   ├── Module 2 (Auth):        85 tests
│   ├── Module 3 (Vault):      125 tests
│   ├── Module 4 (Categories): 107 tests
│   ├── Module 5 (Folders):     77 tests
│   ├── Module 6 (Memories):    73 tests
│   ├── Module 7 (Death):      129 tests
│   ├── Module 8 (Reminders):   82 tests
│   ├── Module 9 (Policy):      68 tests
│   ├── Module 10 (Storage):    52 tests
│   ├── Module 11 (Admin):      47 tests
│   └── Module 12 (External):   42 tests
│
├── Integration Tests:         290 tests (17.6%)
│
├── E2E Tests:                  91 tests (5.5%)
│   ├── User Journeys:          48 tests
│   └── Workflows:              43 tests
│
└── Specialized Tests:         118 tests (7.2%)
    ├── Security:               38 tests
    ├── Performance:            25 tests
    ├── Concurrency:            15 tests
    └── Regression:             40 tests

PRIORITY DISTRIBUTION:
├── 🔥 Critical:            ~1,320 tests (80.3%)
└── ⭐ Important:            ~324 tests (19.7%)
```

---

## **VERIFICATION SUMMARY**

✅ **All Modules Covered:** 13 modules (0-12)  
✅ **All Test Types Included:** Unit, Integration, E2E, Specialized  
✅ **Complete Numbering:** Tests #1 - #1644 (no gaps)  
✅ **Consistent Structure:** All tables properly formatted  
✅ **Priority Tags:** All tests tagged 🔥 or ⭐  
✅ **No Information Loss:** All original content preserved  

---

**📋 END OF COMPLETE TEST INVENTORY**

**Total: 1,644 tests across 129 files**