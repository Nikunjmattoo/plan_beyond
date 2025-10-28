"""Minimal conftest for ORM tests - doesn't load full app"""
import os
import sys
import pytest

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, project_root)

# Create 'app' module alias
import types
app_module = types.ModuleType('app')
sys.modules['app'] = app_module
app_module.__path__ = [project_root]

@pytest.fixture(scope="session")
def db_session():
    """Dummy fixture - ORM tests only inspect classes"""
    return None
