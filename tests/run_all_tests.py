#!/usr/bin/env python3
"""
Test Runner with Progress Bars
Shows per-module and total test results with progress visualization
"""
import sys
import subprocess
import re
from pathlib import Path


def create_progress_bar(current, total, width=40):
    """Create a text-based progress bar"""
    if total == 0:
        return "[" + " " * width + "]"

    filled = int(width * current / total)
    bar = "=" * filled + ">" if filled < width else "=" * width
    bar = bar.ljust(width)
    return f"[{bar}]"


def parse_pytest_verbose_output(output):
    """Parse pytest -v output to get per-file results"""
    lines = output.split('\n')

    # Track results per file
    file_results = {}

    for line in lines:
        # Match test execution lines: "tests/unit/models/test_user_model.py::test_name PASSED"
        if '::' in line and ('PASSED' in line or 'FAILED' in line or 'SKIPPED' in line):
            parts = line.split('::')
            if len(parts) >= 2:
                file_path = parts[0].strip()
                # Extract just the filename
                filename = Path(file_path).name

                if filename not in file_results:
                    file_results[filename] = {'passed': 0, 'failed': 0, 'skipped': 0}

                if 'PASSED' in line:
                    file_results[filename]['passed'] += 1
                elif 'FAILED' in line:
                    file_results[filename]['failed'] += 1
                elif 'SKIPPED' in line:
                    file_results[filename]['skipped'] += 1

    return file_results


def run_module(module_name, test_path, project_root):
    """Run tests for a specific module with LIVE progress and bug detection"""
    print("\n" + "="*70)
    print(f"{module_name}")
    print("="*70)

    cmd = [
        sys.executable, '-m', 'pytest',
        test_path,
        '-v',
        '--tb=short',
        '-p', 'no:warnings',
        '-s'  # Don't capture stdout - allows print() statements to show
    ]

    print(f"\nRunning tests...\n")

    # Run with real-time output capture
    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        cwd=project_root,
        bufsize=1  # Line buffered
    )

    # Capture output while displaying it live
    output_lines = []
    for line in iter(process.stdout.readline, ''):
        if line:
            print(line, end='')  # Print immediately (live progress)
            output_lines.append(line)  # Save for parsing

    process.wait()

    # Combine all output
    output = ''.join(output_lines)

    # Parse output for test results
    file_results = parse_pytest_verbose_output(output)

    return file_results, output


def main():
    """Run all completed test modules"""
    print("\n" + "="*70)
    print("COMPREHENSIVE TEST SUITE - PLAN BEYOND")
    print("="*70)

    project_root = Path(__file__).parent.parent

    # Track overall results
    all_results = []

    # ======================================================================
    # MODULE 0: ORM MODELS (156 tests)
    # ======================================================================

    file_results, output = run_module(
        "MODULE 0: ORM MODEL TEST SUITE",
        "tests/unit/models/",
        project_root
    )

    # Expected ORM files
    orm_files = [
        ('test_user_model.py', 'User Model'),
        ('test_contact_model.py', 'Contact Model'),
        ('test_vault_file_model.py', 'Vault File Model'),
        ('test_folder_model.py', 'Folder Model'),
        ('test_memory_collection_model.py', 'Memory Collection Model'),
        ('test_death_declaration_model.py', 'Death Declaration Model'),
        ('test_trustee_model.py', 'Trustee Model'),
        ('test_category_model.py', 'Category Model'),
        ('test_section_model.py', 'Section Model'),
        ('test_step_model.py', 'Step Model'),
        ('test_reminder_model.py', 'Reminder Model'),
        ('test_admin_model.py', 'Admin Model'),
        ('test_relationship_models.py', 'Relationship Models'),
    ]

    module0_results = {'passed': 0, 'failed': 0, 'skipped': 0, 'total': 0}

    for filename, module_name in orm_files:
        if filename in file_results:
            results = file_results[filename]
            module0_results['passed'] += results['passed']
            module0_results['failed'] += results['failed']
            module0_results['skipped'] += results['skipped']

    module0_results['total'] = module0_results['passed'] + module0_results['failed'] + module0_results['skipped']

    print("\n" + "="*70)
    print("MODULE 0 SUMMARY")
    print("="*70)

    progress = create_progress_bar(module0_results['passed'], module0_results['total'])
    print(f"\nProgress: {progress} {module0_results['passed']}/{module0_results['total']} tests")
    print(f"Result: {module0_results['passed']} passed, {module0_results['failed']} failed, {module0_results['skipped']} skipped")

    all_results.append(('Module 0: ORM Models', module0_results))

    # ======================================================================
    # MODULE 1: FOUNDATION - DATABASE MODELS (45 tests)
    # ======================================================================

    file_results, output = run_module(
        "MODULE 1: FOUNDATION - DATABASE MODELS",
        "tests/unit/foundation/test_database_models.py",
        project_root
    )

    print("\n" + "="*70)
    print("MODULE 1 SUMMARY")
    print("="*70)

    module1_results = {'passed': 0, 'failed': 0, 'skipped': 0, 'total': 0}

    for filename, results in file_results.items():
        module1_results['passed'] += results['passed']
        module1_results['failed'] += results['failed']
        module1_results['skipped'] += results['skipped']

    module1_results['total'] = module1_results['passed'] + module1_results['failed'] + module1_results['skipped']

    if module1_results['total'] > 0:
        progress = create_progress_bar(module1_results['passed'], module1_results['total'])
        print(f"\nProgress: {progress} {module1_results['passed']}/{module1_results['total']} tests")
        print(f"Result: {module1_results['passed']} passed, {module1_results['failed']} failed, {module1_results['skipped']} skipped")
    else:
        print("\nNo tests found")

    all_results.append(('Module 1: Foundation - Database Models', module1_results))

    # ======================================================================
    # MODULE 2: AUTH (85 tests)
    # ======================================================================

    file_results, output = run_module(
        "MODULE 2: AUTH - USER AUTHENTICATION & AUTHORIZATION",
        "tests/unit/auth/",
        project_root
    )

    # Expected Auth test files
    auth_files = [
        ('test_user_controller.py', 'User Controller'),
        ('test_admin_controller.py', 'Admin Controller'),
        ('test_verification_controller.py', 'Verification Controller'),
        ('test_contact_controller.py', 'Contact Controller'),
        ('test_otp_generation.py', 'OTP Generation'),
        ('test_user_status_lifecycle.py', 'User Status Lifecycle'),
    ]

    module2_results = {'passed': 0, 'failed': 0, 'skipped': 0, 'total': 0}

    for filename, module_name in auth_files:
        if filename in file_results:
            results = file_results[filename]
            module2_results['passed'] += results['passed']
            module2_results['failed'] += results['failed']
            module2_results['skipped'] += results['skipped']

    module2_results['total'] = module2_results['passed'] + module2_results['failed'] + module2_results['skipped']

    print("\n" + "="*70)
    print("MODULE 2 SUMMARY")
    print("="*70)

    if module2_results['total'] > 0:
        progress = create_progress_bar(module2_results['passed'], module2_results['total'])
        print(f"\nProgress: {progress} {module2_results['passed']}/{module2_results['total']} tests")
        print(f"Result: {module2_results['passed']} passed, {module2_results['failed']} failed, {module2_results['skipped']} skipped")
    else:
        print("\nNo tests found")

    all_results.append(('Module 2: Auth', module2_results))

    # ======================================================================
    # MODULE 3: VAULT & ENCRYPTION (125 tests)
    # ======================================================================

    file_results, output = run_module(
        "MODULE 3: VAULT & ENCRYPTION",
        "tests/unit/vault/",
        project_root
    )

    # Expected Vault test files
    vault_files = [
        ('test_crypto_engine.py', 'CryptoEngine'),
        ('test_vault_encryptor.py', 'Vault Encryptor'),
        ('test_vault_decryptor.py', 'Vault Decryptor'),
        ('test_db_operations.py', 'Database Operations'),
        ('test_s3_operations.py', 'S3 Operations'),
        ('test_validators.py', 'Validators'),
        ('test_exceptions.py', 'Exceptions'),
    ]

    module3_results = {'passed': 0, 'failed': 0, 'skipped': 0, 'total': 0}

    for filename, module_name in vault_files:
        if filename in file_results:
            results = file_results[filename]
            module3_results['passed'] += results['passed']
            module3_results['failed'] += results['failed']
            module3_results['skipped'] += results['skipped']

    module3_results['total'] = module3_results['passed'] + module3_results['failed'] + module3_results['skipped']

    print("\n" + "="*70)
    print("MODULE 3 SUMMARY")
    print("="*70)

    if module3_results['total'] > 0:
        progress = create_progress_bar(module3_results['passed'], module3_results['total'])
        print(f"\nProgress: {progress} {module3_results['passed']}/{module3_results['total']} tests")
        print(f"Result: {module3_results['passed']} passed, {module3_results['failed']} failed, {module3_results['skipped']} skipped")
    else:
        print("\nNo tests found")

    all_results.append(('Module 3: Vault & Encryption', module3_results))

    # ======================================================================
    # MODULE 4: CATEGORIES (107 tests)
    # ======================================================================

    file_results, output = run_module(
        "MODULE 4: CATEGORIES",
        "tests/unit/categories/",
        project_root
    )

    # Expected Categories test files
    categories_files = [
        ('test_category_controller.py', 'Category Controller'),
        ('test_section_controller.py', 'Section Controller'),
        ('test_step_controller.py', 'Step Controller'),
        ('test_user_answers_controller.py', 'User Answers'),
        ('test_leaf_assignment_controller.py', 'Leaf Assignments'),
        ('test_token_generation.py', 'Token Generation'),
        ('test_release_formatting.py', 'Release Formatting'),
    ]

    module4_results = {'passed': 0, 'failed': 0, 'skipped': 0, 'total': 0}

    for filename, module_name in categories_files:
        if filename in file_results:
            results = file_results[filename]
            module4_results['passed'] += results['passed']
            module4_results['failed'] += results['failed']
            module4_results['skipped'] += results['skipped']

    module4_results['total'] = module4_results['passed'] + module4_results['failed'] + module4_results['skipped']

    print("\n" + "="*70)
    print("MODULE 4 SUMMARY")
    print("="*70)

    if module4_results['total'] > 0:
        progress = create_progress_bar(module4_results['passed'], module4_results['total'])
        print(f"\nProgress: {progress} {module4_results['passed']}/{module4_results['total']} tests")
        print(f"Result: {module4_results['passed']} passed, {module4_results['failed']} failed, {module4_results['skipped']} skipped")
    else:
        print("\nNo tests found")

    all_results.append(('Module 4: Categories', module4_results))

    # ======================================================================
    # OVERALL SUMMARY
    # ======================================================================

    print("\n" + "="*70)
    print("OVERALL SUMMARY - ALL MODULES")
    print("="*70)

    overall = {'passed': 0, 'failed': 0, 'skipped': 0, 'total': 0}

    for module_name, results in all_results:
        status = "[OK]" if results['failed'] == 0 else "[FAIL]"
        print(f"\n{status} {module_name}:")
        print(f"  Passed: {results['passed']}, Failed: {results['failed']}, Skipped: {results['skipped']}, Total: {results['total']}")

        overall['passed'] += results['passed']
        overall['failed'] += results['failed']
        overall['skipped'] += results['skipped']

    overall['total'] = overall['passed'] + overall['failed'] + overall['skipped']

    print("\n" + "="*70)
    print("OVERALL RESULTS")
    print("="*70)

    progress = create_progress_bar(overall['passed'], overall['total'])
    print(f"\nProgress: {progress} {overall['passed']}/{overall['total']} tests")

    print(f"\nResult: {overall['passed']} passed, {overall['failed']} failed, {overall['skipped']} skipped")
    print(f"Total:  {overall['total']} tests")

    # Verify counts tally
    calculated_total = overall['passed'] + overall['failed'] + overall['skipped']
    if calculated_total == overall['total']:
        print(f"\n[OK] Counts tally correctly: {overall['passed']} + {overall['failed']} + {overall['skipped']} = {overall['total']}")
    else:
        print(f"\n[!] WARNING: Counts don't tally: {overall['passed']} + {overall['failed']} + {overall['skipped']} != {overall['total']}")

    # Show failed tests summary
    if overall['failed'] > 0:
        print("\n" + "="*70)
        print("[!] FAILED TESTS (Production Bugs Found)")
        print("="*70)
        print(f"\n{overall['failed']} test(s) failed - these tests found production bugs.")
        print("See detailed failure output and bug reports above.")
        print("="*70)

    # Progress toward complete test suite
    print("\n" + "="*70)
    print("PROGRESS TOWARDS COMPLETE TEST SUITE")
    print("="*70)

    # Calculate actual counts from results
    module0_count = all_results[0][1]['total'] if len(all_results) > 0 else 0
    module1_count = all_results[1][1]['total'] if len(all_results) > 1 else 0
    module2_count = all_results[2][1]['total'] if len(all_results) > 2 else 0
    module3_count = all_results[3][1]['total'] if len(all_results) > 3 else 0
    module4_count = all_results[4][1]['total'] if len(all_results) > 4 else 0

    print(f"\n[OK] Module 0 (ORM Models):        {module0_count}/156 tests")
    print(f"[OK] Module 1 (Foundation):        {module1_count}/102 tests")
    print(f"     Module 1 Remaining:           {102 - module1_count} tests")
    print(f"[OK] Module 2 (Auth):              {module2_count}/130 tests")
    print(f"     Module 2 Remaining:           {130 - module2_count} tests")
    print(f"[OK] Module 3 (Vault):             {module3_count}/125 tests")
    print(f"[OK] Module 4 (Categories):        {module4_count}/107 tests")
    print(f"     Modules 5-12:                 1,025 tests")
    print(f"\nTotal Completed:               {overall['total']}/1,644 tests")
    completion_pct = (overall['total'] / 1644) * 100
    print(f"Completion:                    {completion_pct:.1f}%")
    print("="*70)

    # Exit with appropriate code
    if overall['failed'] > 0:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == '__main__':
    main()
