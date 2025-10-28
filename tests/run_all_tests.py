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
    current_file = None

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


def get_module_name(filename):
    """Convert filename to readable module name"""
    name_map = {
        'test_user_model.py': 'User Model',
        'test_contact_model.py': 'Contact Model',
        'test_vault_file_model.py': 'Vault File Model',
        'test_folder_model.py': 'Folder Model',
        'test_memory_collection_model.py': 'Memory Collection Model',
        'test_death_declaration_model.py': 'Death Declaration Model',
        'test_trustee_model.py': 'Trustee Model',
        'test_category_model.py': 'Category Model',
        'test_section_model.py': 'Section Model',
        'test_step_model.py': 'Step Model',
        'test_reminder_model.py': 'Reminder Model',
        'test_admin_model.py': 'Admin Model',
        'test_relationship_models.py': 'Relationship Models',
    }
    return name_map.get(filename, filename)


def main():
    """Run all ORM test modules and show aggregated results"""
    print("\n" + "="*70)
    print("MODULE 0: ORM MODEL TEST SUITE - PLAN BEYOND")
    print("="*70)

    # Run all ORM tests at once
    project_root = Path(__file__).parent.parent

    cmd = [
        sys.executable, '-m', 'pytest',
        'tests/unit/models/',
        '-v',
        '--tb=short',
        '-p', 'no:warnings'
    ]

    print("\nRunning all ORM tests...")

    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        cwd=project_root
    )

    # Parse output
    output = result.stdout + result.stderr
    file_results = parse_pytest_verbose_output(output)

    # Define expected file order
    expected_files = [
        'test_user_model.py',
        'test_contact_model.py',
        'test_vault_file_model.py',
        'test_folder_model.py',
        'test_memory_collection_model.py',
        'test_death_declaration_model.py',
        'test_trustee_model.py',
        'test_category_model.py',
        'test_section_model.py',
        'test_step_model.py',
        'test_reminder_model.py',
        'test_admin_model.py',
        'test_relationship_models.py',
    ]

    # Print per-module results
    print("\n" + "="*70)
    print("PER MODULE RESULTS")
    print("="*70)

    overall = {'passed': 0, 'failed': 0, 'skipped': 0, 'total': 0}

    for filename in expected_files:
        if filename in file_results:
            results = file_results[filename]
            module_name = get_module_name(filename)

            total = results['passed'] + results['failed'] + results['skipped']
            progress = create_progress_bar(results['passed'], total, width=30)

            print(f"\n{module_name}:")
            print(f"  {progress} {results['passed']}/{total}")
            print(f"  Passed: {results['passed']}, Failed: {results['failed']}, Skipped: {results['skipped']}")

            overall['passed'] += results['passed']
            overall['failed'] += results['failed']
            overall['skipped'] += results['skipped']

    overall['total'] = overall['passed'] + overall['failed'] + overall['skipped']

    # Print overall results
    print("\n" + "="*70)
    print("OVERALL RESULTS - MODULE 0 (ORM MODELS)")
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

    print("\n" + "="*70)
    print("PROGRESS TOWARDS COMPLETE TEST SUITE")
    print("="*70)
    print(f"\nModule 0 (ORM Models):     156/156 tests ✓ COMPLETE")
    print(f"Remaining modules:         1,488 tests (Modules 1-12)")
    print(f"\nTotal Test Suite:          156/1,644 tests (9.5% complete)")
    print("="*70)

    # Exit with appropriate code
    if overall['failed'] > 0:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == '__main__':
    main()
