#!/usr/bin/env python3
"""
Unit tests for version module in dejavu2-cli.

This module tests the version information to ensure it's properly defined,
follows semantic versioning conventions, and can be imported correctly.
"""

import os
import re
import sys

import pytest

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import version


class TestVersion:
  """Test the version module and __version__ attribute."""

  def test_version_module_exists(self):
    """Test that the version module can be imported."""
    assert version is not None

  def test_version_attribute_exists(self):
    """Test that __version__ attribute exists in the module."""
    assert hasattr(version, "__version__")

  def test_version_is_string(self):
    """Test that __version__ is a string."""
    assert isinstance(version.__version__, str)

  def test_version_not_empty(self):
    """Test that __version__ is not empty."""
    assert version.__version__
    assert len(version.__version__) > 0

  def test_version_follows_semantic_versioning(self):
    """Test that __version__ follows semantic versioning format (major.minor.patch)."""
    # Semantic versioning pattern: MAJOR.MINOR.PATCH (all must be numbers)
    semver_pattern = r"^\d+\.\d+\.\d+$"
    assert re.match(semver_pattern, version.__version__), f"Version '{version.__version__}' doesn't follow semantic versioning"

  def test_version_parts_are_numeric(self):
    """Test that all parts of the version are numeric."""
    parts = version.__version__.split(".")
    assert len(parts) == 3, "Version should have exactly 3 parts (major.minor.patch)"
    for part in parts:
      assert part.isdigit(), f"Version part '{part}' is not numeric"

  def test_version_can_be_imported_directly(self):
    """Test that __version__ can be imported directly from the module."""
    from version import __version__

    assert __version__ is not None
    assert isinstance(__version__, str)

  def test_version_matches_module_attribute(self):
    """Test that directly imported __version__ matches module attribute."""
    from version import __version__

    assert __version__ == version.__version__


if __name__ == "__main__":
  pytest.main([__file__])

# fin
