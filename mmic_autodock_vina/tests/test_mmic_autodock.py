"""
Unit and regression test for the mmic_autodock_vina package.
"""

# Import package, test suite, and other packages as needed
import mmic_autodock_vina
import pytest
import sys


def test_mmic_autodock_vina_imported():
    """Sample test, will always pass so long as import statement worked"""
    assert "mmic_autodock_vina" in sys.modules
