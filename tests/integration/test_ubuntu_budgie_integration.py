"""
Integration tests for Ubuntu Budgie plugin with plugin manager.

Tests the integration between the UbuntuBudgiePlugin and PluginManager
to ensure proper discovery, loading, and functionality.
"""

import unittest
from unittest.mock import Mock, patch

from src.nightswitch.plugins.manager import PluginManager
from src.nightswitch.plugins.ubuntu_budgie import UbuntuBudgiePlugin


class TestUbuntuBudgieIntegration(unittest.TestCase):
    """Integration tests for Ubuntu Budgie plugin."""

    def setUp(self):
        """Set up test fixtures."""
        self.plugin_manager = PluginManager()

    def tearDown(self):
        """Clean up after tests."""
        self.plugin_manager.cleanup_all()

    def test_plugin_discovery(self):
        """Test that Ubuntu Budgie plugin can be discovered by plugin manager."""
        discovered_plugins = self.plugin_manager.discover_plugins()

        # Check that UbuntuBudgiePlugin was discovered
        self.assertIn("UbuntuBudgiePlugin", discovered_plugins)

        # Verify plugin is registered
        registered_plugins = self.plugin_manager.get_registered_plugins()
        self.assertIn("UbuntuBudgiePlugin", registered_plugins)
        self.assertEqual(registered_plugins["UbuntuBudgiePlugin"], UbuntuBudgiePlugin)

    def test_plugin_info_retrieval(self):
        """Test retrieving plugin information through plugin manager."""
        self.plugin_manager.discover_plugins()

        plugin_info = self.plugin_manager.get_plugin_info("UbuntuBudgiePlugin")

        self.assertIsNotNone(plugin_info)
        self.assertEqual(plugin_info.name, "ubuntu_budgie")
        self.assertEqual(plugin_info.version, "1.0.0")
        self.assertEqual(plugin_info.priority, 90)
        self.assertIn("budgie", plugin_info.desktop_environments)

    @patch.object(UbuntuBudgiePlugin, "detect_compatibility")
    def test_compatibility_check_through_manager(self, mock_detect):
        """Test compatibility checking through plugin manager."""
        mock_detect.return_value = True
        self.plugin_manager.discover_plugins()

        is_compatible = self.plugin_manager.check_plugin_compatibility(
            "UbuntuBudgiePlugin"
        )

        self.assertTrue(is_compatible)
        mock_detect.assert_called_once()

    @patch.object(UbuntuBudgiePlugin, "detect_compatibility")
    def test_get_compatible_plugins_includes_ubuntu_budgie(self, mock_detect):
        """Test that Ubuntu Budgie plugin appears in compatible plugins list."""
        mock_detect.return_value = True
        self.plugin_manager.discover_plugins()

        compatible_plugins = self.plugin_manager.get_compatible_plugins()

        self.assertIn("UbuntuBudgiePlugin", compatible_plugins)
        # Should be first due to high priority (90)
        self.assertEqual(compatible_plugins[0], "UbuntuBudgiePlugin")

    @patch.object(UbuntuBudgiePlugin, "detect_compatibility")
    @patch.object(UbuntuBudgiePlugin, "initialize")
    def test_plugin_loading_through_manager(self, mock_initialize, mock_detect):
        """Test loading Ubuntu Budgie plugin through plugin manager."""
        mock_detect.return_value = True
        mock_initialize.return_value = True
        self.plugin_manager.discover_plugins()

        success = self.plugin_manager.load_plugin("UbuntuBudgiePlugin")

        self.assertTrue(success)
        self.assertIn("UbuntuBudgiePlugin", self.plugin_manager.get_loaded_plugins())
        mock_detect.assert_called_once()
        mock_initialize.assert_called_once()

    @patch.object(UbuntuBudgiePlugin, "detect_compatibility")
    @patch.object(UbuntuBudgiePlugin, "initialize")
    def test_auto_select_ubuntu_budgie_plugin(self, mock_initialize, mock_detect):
        """Test auto-selection of Ubuntu Budgie plugin when compatible."""
        mock_detect.return_value = True
        mock_initialize.return_value = True
        self.plugin_manager.discover_plugins()

        selected_plugin = self.plugin_manager.auto_select_plugin()

        self.assertEqual(selected_plugin, "UbuntuBudgiePlugin")
        self.assertEqual(
            self.plugin_manager.get_active_plugin_name(), "UbuntuBudgiePlugin"
        )

        # Verify the active plugin is an instance of UbuntuBudgiePlugin
        active_plugin = self.plugin_manager.get_active_plugin()
        self.assertIsInstance(active_plugin, UbuntuBudgiePlugin)

    @patch.object(UbuntuBudgiePlugin, "detect_compatibility")
    @patch.object(UbuntuBudgiePlugin, "initialize")
    @patch.object(UbuntuBudgiePlugin, "apply_dark_theme")
    @patch.object(UbuntuBudgiePlugin, "apply_light_theme")
    @patch.object(UbuntuBudgiePlugin, "get_current_theme")
    def test_theme_operations_through_manager(
        self, mock_get_theme, mock_light, mock_dark, mock_initialize, mock_detect
    ):
        """Test theme operations through plugin manager."""
        mock_detect.return_value = True
        mock_initialize.return_value = True
        mock_dark.return_value = True
        mock_light.return_value = True
        mock_get_theme.return_value = "light"

        self.plugin_manager.discover_plugins()
        self.plugin_manager.auto_select_plugin()

        active_plugin = self.plugin_manager.get_active_plugin()

        # Test theme operations
        self.assertTrue(active_plugin.apply_dark_theme())
        self.assertTrue(active_plugin.apply_light_theme())
        self.assertEqual(active_plugin.get_current_theme(), "light")

        mock_dark.assert_called_once()
        mock_light.assert_called_once()
        mock_get_theme.assert_called_once()

    @patch.object(UbuntuBudgiePlugin, "detect_compatibility")
    def test_incompatible_plugin_not_selected(self, mock_detect):
        """Test that incompatible Ubuntu Budgie plugin is not auto-selected."""
        mock_detect.return_value = False
        self.plugin_manager.discover_plugins()

        compatible_plugins = self.plugin_manager.get_compatible_plugins()
        selected_plugin = self.plugin_manager.auto_select_plugin()

        self.assertNotIn("UbuntuBudgiePlugin", compatible_plugins)
        self.assertIsNone(selected_plugin)

    def test_plugin_config_management(self):
        """Test plugin configuration management through plugin manager."""
        self.plugin_manager.discover_plugins()

        test_config = {
            "gsettings_schema": "custom.schema",
            "gsettings_key": "custom-key",
        }

        self.plugin_manager.set_plugin_config("UbuntuBudgiePlugin", test_config)
        retrieved_config = self.plugin_manager.get_plugin_config("UbuntuBudgiePlugin")

        self.assertEqual(retrieved_config, test_config)


if __name__ == "__main__":
    unittest.main()
