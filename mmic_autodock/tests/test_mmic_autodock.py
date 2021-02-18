"""
Unit and regression test for the mmic_autodock package.
"""

# Import package, test suite, and other packages as needed
import mmic_autodock
import pytest
import sys


def test_mmic_autodock_imported():
    """Sample test, will always pass so long as import statement worked"""
    assert "mmic_autodock" in sys.modules
