#!/usr/bin/env python3
"""
Unit tests for version_updater module in dejavu2-cli.

This module tests the version update functionality to ensure it correctly
increments version numbers according to semantic versioning rules.
"""

import os
import re
import sys
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


class TestVersionUpdater:
  """Test the update_version function."""

  def test_update_patch_version(self):
    """Test incrementing the patch version (default behavior)."""
    # Import here to avoid import-time side effects
    import version_updater

    # Create a temporary version.py file
    with tempfile.TemporaryDirectory() as tmpdir:
      version_file = Path(tmpdir) / "version.py"
      version_file.write_text('__version__ = "1.2.3"\n')

      # Patch __file__ to point to our temp directory
      with patch.object(version_updater, "__file__", str(version_file.parent / "version_updater.py")):
        result = version_updater.update_version("patch")

      # Verify the result
      assert result is True
      content = version_file.read_text()
      assert '__version__ = "1.2.4"' in content

  def test_update_minor_version_resets_patch(self):
    """Test incrementing the minor version resets patch to 0."""
    import version_updater

    with tempfile.TemporaryDirectory() as tmpdir:
      version_file = Path(tmpdir) / "version.py"
      version_file.write_text('__version__ = "1.2.3"\n')

      with patch.object(version_updater, "__file__", str(version_file.parent / "version_updater.py")):
        result = version_updater.update_version("minor")

      assert result is True
      content = version_file.read_text()
      assert '__version__ = "1.3.0"' in content

  def test_update_major_version_resets_minor_and_patch(self):
    """Test incrementing the major version resets minor and patch to 0."""
    import version_updater

    with tempfile.TemporaryDirectory() as tmpdir:
      version_file = Path(tmpdir) / "version.py"
      version_file.write_text('__version__ = "1.2.3"\n')

      with patch.object(version_updater, "__file__", str(version_file.parent / "version_updater.py")):
        result = version_updater.update_version("major")

      assert result is True
      content = version_file.read_text()
      assert '__version__ = "2.0.0"' in content

  def test_missing_version_file_returns_false(self):
    """Test that update_version returns False when version.py is missing."""
    import version_updater

    with tempfile.TemporaryDirectory() as tmpdir:
      # Don't create version.py file
      with patch.object(version_updater, "__file__", str(Path(tmpdir) / "version_updater.py")):
        result = version_updater.update_version("patch")

      assert result is False

  def test_malformed_version_string_returns_false(self):
    """Test that update_version returns False for malformed version strings."""
    import version_updater

    with tempfile.TemporaryDirectory() as tmpdir:
      version_file = Path(tmpdir) / "version.py"
      version_file.write_text('__version__ = "1.2.3.4"\n')  # Invalid: too many parts

      with patch.object(version_updater, "__file__", str(version_file.parent / "version_updater.py")):
        result = version_updater.update_version("patch")

      assert result is False

  def test_missing_version_variable_returns_false(self):
    """Test that update_version returns False when __version__ is not found."""
    import version_updater

    with tempfile.TemporaryDirectory() as tmpdir:
      version_file = Path(tmpdir) / "version.py"
      version_file.write_text("# No version variable here\n")

      with patch.object(version_updater, "__file__", str(version_file.parent / "version_updater.py")):
        result = version_updater.update_version("patch")

      assert result is False

  def test_non_numeric_version_parts_returns_false(self):
    """Test that update_version returns False for non-numeric version parts."""
    import version_updater

    with tempfile.TemporaryDirectory() as tmpdir:
      version_file = Path(tmpdir) / "version.py"
      version_file.write_text('__version__ = "1.2.beta"\n')  # Invalid: non-numeric

      with patch.object(version_updater, "__file__", str(version_file.parent / "version_updater.py")):
        result = version_updater.update_version("patch")

      assert result is False

  def test_default_increment_type_is_patch(self):
    """Test that default increment type is patch when no argument provided."""
    import version_updater

    with tempfile.TemporaryDirectory() as tmpdir:
      version_file = Path(tmpdir) / "version.py"
      version_file.write_text('__version__ = "1.0.0"\n')

      with patch.object(version_updater, "__file__", str(version_file.parent / "version_updater.py")):
        # Call without argument (should default to 'patch')
        result = version_updater.update_version()

      assert result is True
      content = version_file.read_text()
      assert '__version__ = "1.0.1"' in content

  def test_version_string_format_preserved(self):
    """Test that the version string format is preserved (quotes and spacing)."""
    import version_updater

    with tempfile.TemporaryDirectory() as tmpdir:
      version_file = Path(tmpdir) / "version.py"
      original_content = '#!/usr/bin/env python3\n\n__version__ = "1.2.3"\n\n# Comment\n'
      version_file.write_text(original_content)

      with patch.object(version_updater, "__file__", str(version_file.parent / "version_updater.py")):
        result = version_updater.update_version("patch")

      assert result is True
      content = version_file.read_text()
      # Verify only the version number changed, format preserved
      assert '__version__ = "1.2.4"' in content
      assert "# Comment" in content
      assert "#!/usr/bin/env python3" in content

  def test_handles_zero_versions(self):
    """Test that update_version handles versions starting with 0."""
    import version_updater

    with tempfile.TemporaryDirectory() as tmpdir:
      version_file = Path(tmpdir) / "version.py"
      version_file.write_text('__version__ = "0.0.1"\n')

      with patch.object(version_updater, "__file__", str(version_file.parent / "version_updater.py")):
        result = version_updater.update_version("minor")

      assert result is True
      content = version_file.read_text()
      assert '__version__ = "0.1.0"' in content

  def test_handles_large_version_numbers(self):
    """Test that update_version handles large version numbers correctly."""
    import version_updater

    with tempfile.TemporaryDirectory() as tmpdir:
      version_file = Path(tmpdir) / "version.py"
      version_file.write_text('__version__ = "99.99.99"\n')

      with patch.object(version_updater, "__file__", str(version_file.parent / "version_updater.py")):
        result = version_updater.update_version("patch")

      assert result is True
      content = version_file.read_text()
      assert '__version__ = "99.99.100"' in content

  def test_major_increment_from_large_minor_patch(self):
    """Test major increment correctly resets large minor and patch values."""
    import version_updater

    with tempfile.TemporaryDirectory() as tmpdir:
      version_file = Path(tmpdir) / "version.py"
      version_file.write_text('__version__ = "5.99.999"\n')

      with patch.object(version_updater, "__file__", str(version_file.parent / "version_updater.py")):
        result = version_updater.update_version("major")

      assert result is True
      content = version_file.read_text()
      assert '__version__ = "6.0.0"' in content


if __name__ == "__main__":
  pytest.main([__file__])

# fin
