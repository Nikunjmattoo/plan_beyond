"""
Standardized bug reporting for test suite.

All production bugs should be reported using these helpers to ensure
consistent formatting and easy parsing by the test runner.
"""


def report_production_bug(
    bug_number: int,
    title: str,
    issue: str,
    impact: str,
    fix: str,
    location: str = None
):
    """
    Report a production bug discovered during testing.

    Args:
        bug_number: Bug number (1, 2, 3, etc.)
        title: Short title (e.g., "Email Case Sensitivity")
        issue: Clear description of the issue
        impact: Business/security impact
        fix: How to fix it
        location: Optional file:line or function name

    Example:
        report_production_bug(
            bug_number=1,
            title="Email Case Sensitivity",
            issue="Database allows duplicate emails with different cases",
            impact="Users can create duplicate accounts",
            fix="Use CITEXT column or lowercase emails before saving",
            location="models/user.py:15"
        )
    """
    separator = "=" * 70

    print(f"\n{separator}")
    print(f"[!] PRODUCTION BUG #{bug_number}: {title}")
    print(separator)
    print(f"Issue:    {issue}")
    print(f"Impact:   {impact}")
    print(f"Fix:      {fix}")
    if location:
        print(f"Location: {location}")
    print(separator)


def report_test_bug(title: str, issue: str, fix: str):
    """
    Report a bug in the test itself (not production code).

    Args:
        title: Short title
        issue: What's wrong with the test
        fix: How to fix the test

    Example:
        report_test_bug(
            title="Invalid Field Name",
            issue="Test uses 'bio' field which doesn't exist in UserProfile",
            fix="Use real fields: first_name, last_name, city, country"
        )
    """
    separator = "=" * 70

    print(f"\n{separator}")
    print(f"[!] TEST BUG: {title}")
    print(separator)
    print(f"Issue: {issue}")
    print(f"Fix:   {fix}")
    print(separator)


def document_expected_behavior(
    feature: str,
    current_behavior: str,
    expected_behavior: str,
    note: str = None
):
    """
    Document expected behavior that may not be implemented yet.

    Args:
        feature: Feature name
        current_behavior: What currently happens
        expected_behavior: What should happen
        note: Optional additional notes

    Example:
        document_expected_behavior(
            feature="Status History Tracking",
            current_behavior="No history entry created on status change",
            expected_behavior="Create UserStatusHistory entry for audit trail",
            note="This is not a critical bug but should be implemented"
        )
    """
    separator = "=" * 70

    print(f"\n{separator}")
    print(f"[i] EXPECTED BEHAVIOR: {feature}")
    print(separator)
    print(f"Current:  {current_behavior}")
    print(f"Expected: {expected_behavior}")
    if note:
        print(f"Note:     {note}")
    print(separator)


# Export all functions
__all__ = [
    'report_production_bug',
    'report_test_bug',
    'document_expected_behavior',
]
