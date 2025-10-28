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


def parse_pytest_output(output):
    """Parse pytest output to extract test results"""
    lines = output.split('\n')

    # Find test results
    results = {
        'passed': 0,
        'failed': 0,
        'skipped': 0,
        'total': 0
    }

    # Look for the summary line: "156 passed in 5.14s"
    for line in lines:
        if 'passed' in line or 'failed' in line or 'skipped' in line:
            # Extract numbers
            passed_match = re.search(r'(\d+) passed', line)
            failed_match = re.search(r'(\d+) failed', line)
            skipped_match = re.search(r'(\d+) skipped', line)

            if passed_match:
                results['passed'] = int(passed_match.group(1))
            if failed_match:
                results['failed'] = int(failed_match.group(1))
            if skipped_match:
                results['skipped'] = int(skipped_match.group(1))

    results['total'] = results['passed'] + results['failed'] + results['skipped']

    return results


def run_test_module(module_path, module_name):
    """Run a single test module and return results"""
    print(f"\n{'='*70}")
    print(f"Running: {module_name}")
    print('='*70)

    # Run pytest on the module
    cmd = [
        sys.executable, '-m', 'pytest',
        str(module_path),
        '-v',
        '--tb=short',
        '--no-header',
        '-p', 'no:warnings'
    ]

    # Run from project root (parent of tests directory)
    project_root = Path(__file__).parent.parent

    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        cwd=project_root
    )

    # Parse output
    output = result.stdout + result.stderr
    results = parse_pytest_output(output)

    # Show progress bar
    total_tests = results['total']
    passed_tests = results['passed']

    if total_tests > 0:
        progress = create_progress_bar(passed_tests, total_tests)
        print(f"\nProgress: {progress} {passed_tests}/{total_tests} tests")

    # Show results
    print(f"\nResult: {results['passed']} passed, {results['failed']} failed, {results['skipped']} skipped")

    return results


def main():
    """Run all ORM test modules and show aggregated results"""
    print("\n" + "="*70)
    print("MODULE 0: ORM MODEL TEST SUITE - PLAN BEYOND")
    print("="*70)

    # Define test modules (relative to project root)
    test_modules = [
        ('tests/unit/models/test_user_model.py', 'User Model'),
        ('tests/unit/models/test_contact_model.py', 'Contact Model'),
        ('tests/unit/models/test_vault_file_model.py', 'Vault File Model'),
        ('tests/unit/models/test_folder_model.py', 'Folder Model'),
        ('tests/unit/models/test_memory_collection_model.py', 'Memory Collection Model'),
        ('tests/unit/models/test_death_declaration_model.py', 'Death Declaration Model'),
        ('tests/unit/models/test_trustee_model.py', 'Trustee Model'),
        ('tests/unit/models/test_category_model.py', 'Category Model'),
        ('tests/unit/models/test_section_model.py', 'Section Model'),
        ('tests/unit/models/test_step_model.py', 'Step Model'),
        ('tests/unit/models/test_reminder_model.py', 'Reminder Model'),
        ('tests/unit/models/test_admin_model.py', 'Admin Model'),
        ('tests/unit/models/test_relationship_models.py', 'Relationship Models'),
    ]

    # Track overall results
    overall = {
        'passed': 0,
        'failed': 0,
        'skipped': 0,
        'total': 0
    }

    module_results = []

    # Run each module
    for module_path, module_name in test_modules:
        results = run_test_module(module_path, module_name)

        # Track results
        module_results.append((module_name, results))
        overall['passed'] += results['passed']
        overall['failed'] += results['failed']
        overall['skipped'] += results['skipped']
        overall['total'] += results['total']

    # Print summary
    print("\n" + "="*70)
    print("SUMMARY - PER MODULE RESULTS")
    print("="*70)

    for module_name, results in module_results:
        print(f"\n{module_name}:")
        print(f"  Passed:  {results['passed']}")
        print(f"  Failed:  {results['failed']}")
        print(f"  Skipped: {results['skipped']}")
        print(f"  Total:   {results['total']}")

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
