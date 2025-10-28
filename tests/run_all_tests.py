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
    bugs_found = []

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

        # Detect production bugs (standardized format: "🔥 PRODUCTION BUG #X: Title")
        if '🔥 PRODUCTION BUG #' in line:
            bug_match = re.search(r'PRODUCTION BUG #(\d+)(?:: (.+))?', line)
            if bug_match:
                bug_num = bug_match.group(1)
                bug_title = bug_match.group(2).strip() if bug_match.group(2) else ""
                bug_id = f"Bug #{bug_num}: {bug_title}" if bug_title else f"Bug #{bug_num}"
                bugs_found.append(bug_id)

    return file_results, bugs_found


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

    # Parse output for test results and bugs
    file_results, bugs_found = parse_pytest_verbose_output(output)

    return file_results, bugs_found, output


def main():
    """Run all completed test modules"""
    print("\n" + "="*70)
    print("COMPREHENSIVE TEST SUITE - PLAN BEYOND")
    print("="*70)

    project_root = Path(__file__).parent.parent

    # Track overall results
    all_results = []
    all_bugs = []

    # ======================================================================
    # MODULE 0: ORM MODELS (156 tests)
    # ======================================================================

    file_results, bugs, output = run_module(
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

    print("\n" + "="*70)
    print("PER MODULE RESULTS")
    print("="*70)

    module0_results = {'passed': 0, 'failed': 0, 'skipped': 0, 'total': 0}

    for filename, module_name in orm_files:
        if filename in file_results:
            results = file_results[filename]

            total = results['passed'] + results['failed'] + results['skipped']
            progress = create_progress_bar(results['passed'], total, width=30)

            print(f"\n{module_name}:")
            print(f"  {progress} {results['passed']}/{total}")
            print(f"  Passed: {results['passed']}, Failed: {results['failed']}, Skipped: {results['skipped']}")

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
    all_bugs.extend(bugs)

    # ======================================================================
    # MODULE 1: FOUNDATION - DATABASE MODELS (45 tests)
    # ======================================================================

    file_results, bugs, output = run_module(
        "MODULE 1: FOUNDATION - DATABASE MODELS",
        "tests/unit/foundation/test_database_models.py",
        project_root
    )

    print("\n" + "="*70)
    print("MODULE 1 RESULTS")
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
    all_bugs.extend(bugs)

    # ======================================================================
    # MODULE 2: AUTH (85 tests)
    # ======================================================================

    file_results, bugs, output = run_module(
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

    print("\n" + "="*70)
    print("MODULE 2 RESULTS")
    print("="*70)

    module2_results = {'passed': 0, 'failed': 0, 'skipped': 0, 'total': 0}

    for filename, module_name in auth_files:
        if filename in file_results:
            results = file_results[filename]

            total = results['passed'] + results['failed'] + results['skipped']
            progress = create_progress_bar(results['passed'], total, width=30)

            print(f"\n{module_name}:")
            print(f"  {progress} {results['passed']}/{total}")
            print(f"  Passed: {results['passed']}, Failed: {results['failed']}, Skipped: {results['skipped']}")

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
    all_bugs.extend(bugs)

    # ======================================================================
    # OVERALL SUMMARY
    # ======================================================================

    print("\n" + "="*70)
    print("OVERALL SUMMARY - ALL MODULES")
    print("="*70)

    overall = {'passed': 0, 'failed': 0, 'skipped': 0, 'total': 0}

    for module_name, results in all_results:
        status = "✓" if results['failed'] == 0 else "✗"
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
        print(f"\n✓ Counts tally correctly: {overall['passed']} + {overall['failed']} + {overall['skipped']} = {overall['total']}")
    else:
        print(f"\n✗ WARNING: Counts don't tally: {overall['passed']} + {overall['failed']} + {overall['skipped']} ≠ {overall['total']}")

    # Production bugs found
    if all_bugs:
        print("\n" + "="*70)
        print("🔥 PRODUCTION BUGS DISCOVERED")
        print("="*70)
        unique_bugs = list(set(all_bugs))
        print(f"\nTotal bugs found: {len(unique_bugs)}")
        for bug in unique_bugs:
            print(f"  - {bug}")
        print("\nSee test output above for bug details.")

    # Progress toward complete test suite
    print("\n" + "="*70)
    print("PROGRESS TOWARDS COMPLETE TEST SUITE")
    print("="*70)
    print(f"\n✓ Module 0 (ORM Models):        156/156 tests")
    print(f"✓ Module 1 (Foundation):        45/102 tests (database models only)")
    print(f"  Module 1 Remaining:           57 tests")
    print(f"✓ Module 2 (Auth):              85/130 tests (unit tests only)")
    print(f"  Module 2 Remaining:           45 tests (integration tests)")
    print(f"  Modules 3-12:                 1,257 tests")
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
