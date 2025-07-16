"""
Unit tests for Ubuntu Budgie theme plugin.

Tests the UbuntuBudgiePlugin class functionality including desktop environment
detection, gsettings integration, and theme switching operations.
"""

import os
import subprocess
import unittest
from unittest.mock import MagicMock, Mock, patch

import pytest

from src.nightswitch.plugins.base import PluginInfo, PluginOperationError
from src.nightswitch.plugins.ubuntu_budgie import UbuntuBudgiePlugin


class TestUbuntuBudgiePlugin(unittest.TestCase):
    """Test cases for UbuntuBudgiePlugin."""

    def setUp(self):
        """Set up test fixtures."""
        self.plugin = UbuntuBudgiePlugin()

    def tearDown(self):
        """Clean up after tests."""
        self.plugin.cleanup()

    def test_get_info(self):
        """Test plugin info retrieval."""
        info = self.plugin.get_info()

        self.assertIsInstance(info, PluginInfo)
        self.assertEqual(info.name, "ubuntu_budgie")
        self.assertEqual(info.version, "1.0.0")
        self.assertIn("budgie", info.desktop_environments)
        self.assertIn("ubuntu:budgie", info.desktop_environments)
        self.assertEqual(info.priority, 90)
        self.assertIn("gsettings", info.requires_packages)
        self.assertIn("budgie-desktop", info.requires_packages)

    @patch("shutil.which")
    @patch.object(UbuntuBudgiePlugin, "_is_budgie_desktop")
    @patch.object(UbuntuBudgiePlugin, "_check_gsettings_schema")
    def test_detect_compatibility_success(
        self, mock_check_schema, mock_is_budgie, mock_which
    ):
        """Test successful compatibility detection."""
        mock_which.return_value = "/usr/bin/gsettings"
        mock_is_budgie.return_value = True
        mock_check_schema.return_value = True

        result = self.plugin.detect_compatibility()

        self.assertTrue(result)
        mock_which.assert_called_once_with("gsettings")
        mock_is_budgie.assert_called_once()
        mock_check_schema.assert_called_once()

    @patch("shutil.which")
    def test_detect_compatibility_no_gsettings(self, mock_which):
        """Test compatibility detection when gsettings is not available."""
        mock_which.return_value = None

        result = self.plugin.detect_compatibility()

        self.assertFalse(result)
        mock_which.assert_called_once_with("gsettings")

    @patch("shutil.which")
    @patch.object(UbuntuBudgiePlugin, "_is_budgie_desktop")
    def test_detect_compatibility_not_budgie(self, mock_is_budgie, mock_which):
        """Test compatibility detection when not running Budgie desktop."""
        mock_which.return_value = "/usr/bin/gsettings"
        mock_is_budgie.return_value = False

        result = self.plugin.detect_compatibility()

        self.assertFalse(result)
        mock_is_budgie.assert_called_once()

    @patch("shutil.which")
    @patch.object(UbuntuBudgiePlugin, "_is_budgie_desktop")
    @patch.object(UbuntuBudgiePlugin, "_check_gsettings_schema")
    def test_detect_compatibility_no_schema(
        self, mock_check_schema, mock_is_budgie, mock_which
    ):
        """Test compatibility detection when GSettings schema is not available."""
        mock_which.return_value = "/usr/bin/gsettings"
        mock_is_budgie.return_value = True
        mock_check_schema.return_value = False

        result = self.plugin.detect_compatibility()

        self.assertFalse(result)
        mock_check_schema.assert_called_once()

    @patch("shutil.which")
    @patch.object(UbuntuBudgiePlugin, "_check_gsettings_schema")
    def test_initialize_success(self, mock_check_schema, mock_which):
        """Test successful plugin initialization."""
        mock_which.return_value = "/usr/bin/gsettings"
        mock_check_schema.return_value = True

        result = self.plugin.initialize()

        self.assertTrue(result)
        self.assertTrue(self.plugin.is_initialized())
        self.assertTrue(self.plugin._gsettings_available)
        self.assertTrue(self.plugin._schema_available)

    @patch("shutil.which")
    def test_initialize_no_gsettings(self, mock_which):
        """Test initialization failure when gsettings is not available."""
        mock_which.return_value = None

        result = self.plugin.initialize()

        self.assertFalse(result)
        self.assertFalse(self.plugin.is_initialized())

    @patch("shutil.which")
    @patch.object(UbuntuBudgiePlugin, "_check_gsettings_schema")
    def test_initialize_no_schema(self, mock_check_schema, mock_which):
        """Test initialization failure when schema is not available."""
        mock_which.return_value = "/usr/bin/gsettings"
        mock_check_schema.return_value = False

        result = self.plugin.initialize()

        self.assertFalse(result)
        self.assertFalse(self.plugin.is_initialized())

    def test_cleanup(self):
        """Test plugin cleanup."""
        # Initialize first
        self.plugin._gsettings_available = True
        self.plugin._schema_available = True
        self.plugin.set_initialized(True)

        self.plugin.cleanup()

        self.assertFalse(self.plugin._gsettings_available)
        self.assertFalse(self.plugin._schema_available)
        self.assertFalse(self.plugin.is_initialized())

    @patch.object(UbuntuBudgiePlugin, "_set_gsettings_value")
    def test_apply_dark_theme_success(self, mock_set_value):
        """Test successful dark theme application."""
        self.plugin.set_initialized(True)
        mock_set_value.return_value = True

        result = self.plugin.apply_dark_theme()

        self.assertTrue(result)
        mock_set_value.assert_called_once_with("prefer-dark")

    @patch.object(UbuntuBudgiePlugin, "_set_gsettings_value")
    def test_apply_dark_theme_failure(self, mock_set_value):
        """Test dark theme application failure."""
        self.plugin.set_initialized(True)
        mock_set_value.return_value = False

        result = self.plugin.apply_dark_theme()

        self.assertFalse(result)
        mock_set_value.assert_called_once_with("prefer-dark")

    def test_apply_dark_theme_not_initialized(self):
        """Test dark theme application when plugin not initialized."""
        result = self.plugin.apply_dark_theme()

        self.assertFalse(result)

    @patch.object(UbuntuBudgiePlugin, "_set_gsettings_value")
    def test_apply_light_theme_success(self, mock_set_value):
        """Test successful light theme application."""
        self.plugin.set_initialized(True)
        mock_set_value.return_value = True

        result = self.plugin.apply_light_theme()

        self.assertTrue(result)
        mock_set_value.assert_called_once_with("default")

    @patch.object(UbuntuBudgiePlugin, "_set_gsettings_value")
    def test_apply_light_theme_failure(self, mock_set_value):
        """Test light theme application failure."""
        self.plugin.set_initialized(True)
        mock_set_value.return_value = False

        result = self.plugin.apply_light_theme()

        self.assertFalse(result)
        mock_set_value.assert_called_once_with("default")

    def test_apply_light_theme_not_initialized(self):
        """Test light theme application when plugin not initialized."""
        result = self.plugin.apply_light_theme()

        self.assertFalse(result)

    @patch.object(UbuntuBudgiePlugin, "_get_gsettings_value")
    def test_get_current_theme_dark(self, mock_get_value):
        """Test getting current theme when dark theme is active."""
        self.plugin.set_initialized(True)
        mock_get_value.return_value = "prefer-dark"

        result = self.plugin.get_current_theme()

        self.assertEqual(result, "dark")
        mock_get_value.assert_called_once()

    @patch.object(UbuntuBudgiePlugin, "_get_gsettings_value")
    def test_get_current_theme_light(self, mock_get_value):
        """Test getting current theme when light theme is active."""
        self.plugin.set_initialized(True)
        mock_get_value.return_value = "default"

        result = self.plugin.get_current_theme()

        self.assertEqual(result, "light")
        mock_get_value.assert_called_once()

    @patch.object(UbuntuBudgiePlugin, "_get_gsettings_value")
    def test_get_current_theme_unknown(self, mock_get_value):
        """Test getting current theme with unknown value."""
        self.plugin.set_initialized(True)
        mock_get_value.return_value = "unknown-value"

        result = self.plugin.get_current_theme()

        self.assertIsNone(result)
        mock_get_value.assert_called_once()

    @patch.object(UbuntuBudgiePlugin, "_get_gsettings_value")
    def test_get_current_theme_none(self, mock_get_value):
        """Test getting current theme when gsettings returns None."""
        self.plugin.set_initialized(True)
        mock_get_value.return_value = None

        result = self.plugin.get_current_theme()

        self.assertIsNone(result)
        mock_get_value.assert_called_once()

    def test_get_current_theme_not_initialized(self):
        """Test getting current theme when plugin not initialized."""
        result = self.plugin.get_current_theme()

        self.assertIsNone(result)

    @patch.dict(os.environ, {"XDG_CURRENT_DESKTOP": "budgie"})
    def test_is_budgie_desktop_xdg_current_desktop(self):
        """Test Budgie desktop detection via XDG_CURRENT_DESKTOP."""
        result = self.plugin._is_budgie_desktop()

        self.assertTrue(result)

    @patch.dict(os.environ, {"DESKTOP_SESSION": "ubuntu:budgie"})
    def test_is_budgie_desktop_desktop_session(self):
        """Test Budgie desktop detection via DESKTOP_SESSION."""
        result = self.plugin._is_budgie_desktop()

        self.assertTrue(result)

    @patch.dict(os.environ, {"XDG_SESSION_DESKTOP": "budgie-desktop"})
    def test_is_budgie_desktop_xdg_session_desktop(self):
        """Test Budgie desktop detection via XDG_SESSION_DESKTOP."""
        result = self.plugin._is_budgie_desktop()

        self.assertTrue(result)

    @patch("subprocess.run")
    def test_is_budgie_desktop_process_check(self, mock_run):
        """Test Budgie desktop detection via process check."""
        # Clear environment variables
        with patch.dict(os.environ, {}, clear=True):
            mock_run.return_value = Mock(returncode=0)

            result = self.plugin._is_budgie_desktop()

            self.assertTrue(result)
            mock_run.assert_called_once_with(
                ["pgrep", "-f", "budgie-panel"],
                capture_output=True,
                text=True,
                timeout=5,
            )

    @patch("subprocess.run")
    def test_is_budgie_desktop_not_found(self, mock_run):
        """Test Budgie desktop detection when not found."""
        # Clear environment variables
        with patch.dict(os.environ, {}, clear=True):
            mock_run.return_value = Mock(returncode=1)

            result = self.plugin._is_budgie_desktop()

            self.assertFalse(result)

    @patch("subprocess.run")
    def test_check_gsettings_schema_available(self, mock_run):
        """Test GSettings schema availability check when schema is available."""
        mock_run.return_value = Mock(
            returncode=0, stdout="org.gnome.desktop.interface\nother.schema\n"
        )

        result = self.plugin._check_gsettings_schema()

        self.assertTrue(result)
        mock_run.assert_called_once_with(
            ["gsettings", "list-schemas"], capture_output=True, text=True, timeout=10
        )

    @patch("subprocess.run")
    def test_check_gsettings_schema_not_available(self, mock_run):
        """Test GSettings schema availability check when schema is not available."""
        mock_run.return_value = Mock(
            returncode=0, stdout="other.schema\nanother.schema\n"
        )

        result = self.plugin._check_gsettings_schema()

        self.assertFalse(result)

    @patch("subprocess.run")
    def test_check_gsettings_schema_command_failed(self, mock_run):
        """Test GSettings schema check when command fails."""
        mock_run.return_value = Mock(returncode=1)

        result = self.plugin._check_gsettings_schema()

        self.assertFalse(result)

    @patch("subprocess.run")
    def test_set_gsettings_value_success(self, mock_run):
        """Test successful gsettings value setting."""
        mock_run.return_value = Mock(returncode=0)

        result = self.plugin._set_gsettings_value("prefer-dark")

        self.assertTrue(result)
        mock_run.assert_called_once_with(
            [
                "gsettings",
                "set",
                "org.gnome.desktop.interface",
                "color-scheme",
                "prefer-dark",
            ],
            capture_output=True,
            text=True,
            timeout=10,
        )

    @patch("subprocess.run")
    def test_set_gsettings_value_failure(self, mock_run):
        """Test gsettings value setting failure."""
        mock_run.return_value = Mock(returncode=1, stderr="Error message")

        result = self.plugin._set_gsettings_value("prefer-dark")

        self.assertFalse(result)

    @patch("subprocess.run")
    def test_get_gsettings_value_success(self, mock_run):
        """Test successful gsettings value retrieval."""
        mock_run.return_value = Mock(returncode=0, stdout="'prefer-dark'\n")

        result = self.plugin._get_gsettings_value()

        self.assertEqual(result, "prefer-dark")
        mock_run.assert_called_once_with(
            ["gsettings", "get", "org.gnome.desktop.interface", "color-scheme"],
            capture_output=True,
            text=True,
            timeout=10,
        )

    @patch("subprocess.run")
    def test_get_gsettings_value_with_quotes(self, mock_run):
        """Test gsettings value retrieval with quotes stripped."""
        mock_run.return_value = Mock(returncode=0, stdout='"default"\n')

        result = self.plugin._get_gsettings_value()

        self.assertEqual(result, "default")

    @patch("subprocess.run")
    def test_get_gsettings_value_failure(self, mock_run):
        """Test gsettings value retrieval failure."""
        mock_run.return_value = Mock(returncode=1, stderr="Error message")

        result = self.plugin._get_gsettings_value()

        self.assertIsNone(result)

    @patch("subprocess.run")
    def test_subprocess_timeout_handling(self, mock_run):
        """Test handling of subprocess timeout exceptions."""
        mock_run.side_effect = subprocess.TimeoutExpired("gsettings", 10)

        result = self.plugin._get_gsettings_value()

        self.assertIsNone(result)

    @patch("subprocess.run")
    def test_subprocess_file_not_found_handling(self, mock_run):
        """Test handling of FileNotFoundError exceptions."""
        mock_run.side_effect = FileNotFoundError("gsettings not found")

        result = self.plugin._get_gsettings_value()

        self.assertIsNone(result)


if __name__ == "__main__":
    unittest.main()
