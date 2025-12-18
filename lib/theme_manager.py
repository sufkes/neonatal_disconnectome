# ===================================================================
# PART 1: Create lib/theme_manager.py - Centralized Theme Management
# ===================================================================

"""
Centralized theme management system for Disconnectome application
Handles theme loading, switching, and application across all UI components
"""

import sys
import customtkinter as ctk
import json
import os
from pathlib import Path
from typing import Optional, Callable
import logging


logger = logging.getLogger("disconnectome")


class ThemeManager:
    """
    Centralized theme manager that handles theme loading and application
    across all screens and components
    """

    def __init__(self, themes_folder: str = "themes"):
        self.themes_folder = themes_folder
        self.current_theme_name: str = "macos_light"
        self.current_theme_data: dict = {}
        self.observers: list[Callable] = []

        # Ensure themes folder exists
        Path(themes_folder).mkdir(exist_ok=True)

    def get_available_themes(self) -> list[str]:
        """Get list of available theme names"""
        if getattr(sys, "frozen", False):
            base_path = sys._MEIPASS
        else:
            from lib.constants import PROJECT_ROOT

            base_path = PROJECT_ROOT

        themes_path = os.path.join(base_path, self.themes_folder)

        if not os.path.exists(themes_path):
            logger.warning(f"Themes folder not found: {themes_path}")
            return []

        themes = []
        for f in os.listdir(themes_path):
            if f.endswith(".json"):
                themes.append(f[:-5])  # Remove .json extension

        return sorted(themes)

    def load_theme(self, theme_name: str) -> bool:
        """
        Load a theme and apply it to CustomTkinter

        Args:
            theme_name: Name of theme file (without .json)

        Returns:
            True if successful, False otherwise
        """
        theme_path = os.path.join(self.themes_folder, f"{theme_name}.json")

        # PyInstaller-aware path resolution
        if getattr(sys, "frozen", False):
            base_path = sys._MEIPASS
        else:
            from lib.constants import PROJECT_ROOT

            base_path = PROJECT_ROOT

        full_theme_path = os.path.join(base_path, theme_path)

        if not os.path.exists(full_theme_path):
            logger.error(f"Theme file not found: {full_theme_path}")
            return False

        try:
            # Load theme data
            with open(full_theme_path, "r") as f:
                self.current_theme_data = json.load(f)

            # Apply to CustomTkinter
            ctk.set_default_color_theme(full_theme_path)

            self.current_theme_name = theme_name
            logger.info(f"Loaded theme: {theme_name}")

            # Notify observers
            self._notify_observers()

            return True

        except Exception as e:
            logger.error(f"Failed to load theme {theme_name}: {e}")
            return False

    def get_color(
        self, widget_type: str, property_name: str, default: str = "#000000"
    ) -> str:
        """
        Get a color value from current theme

        Args:
            widget_type: Type of widget (e.g., "CTkFrame", "CTkButton")
            property_name: Property name (e.g., "fg_color", "text_color")
            default: Default color if not found

        Returns:
            Color value as string
        """
        try:
            theme = ctk.ThemeManager.theme
            if widget_type in theme and property_name in theme[widget_type]:
                value = theme[widget_type][property_name]
                # Handle tuple values (light, dark)
                if isinstance(value, (list, tuple)):
                    return value[0]  # Return light mode color
                return value
        except Exception as e:
            logger.warning(f"Failed to get color {widget_type}.{property_name}: {e}")

        return default

    def subscribe(self, callback: Callable) -> None:
        """Subscribe to theme change events"""
        if callback not in self.observers:
            self.observers.append(callback)

    def unsubscribe(self, callback: Callable) -> None:
        """Unsubscribe from theme change events"""
        if callback in self.observers:
            self.observers.remove(callback)

    def _notify_observers(self) -> None:
        """Notify all observers of theme change"""
        for callback in self.observers:
            try:
                callback(self.current_theme_name)
            except Exception as e:
                logger.error(f"Error notifying theme observer: {e}")


# ===================================================================
# PART 2: Create Themeable Base Classes
# ===================================================================


class ThemeableFrame(ctk.CTkFrame):
    """Base frame class that automatically updates with theme changes"""

    def __init__(self, master, theme_manager: Optional[ThemeManager] = None, **kwargs):
        super().__init__(master, **kwargs)
        self.theme_manager = theme_manager

        if theme_manager:
            theme_manager.subscribe(self._on_theme_changed)

    def _on_theme_changed(self, theme_name: str):
        """Called when theme changes"""
        self.update_theme()

    def update_theme(self):
        """Override this method in subclasses to update theme-specific styling"""
        theme = ctk.ThemeManager.theme

        # Update frame colors
        if "CTkFrame" in theme:
            self.configure(
                fg_color=theme["CTkFrame"].get("fg_color"),
                border_color=theme["CTkFrame"].get("border_color"),
            )

    def destroy(self):
        """Clean up theme subscription when destroyed"""
        if self.theme_manager:
            self.theme_manager.unsubscribe(self._on_theme_changed)
        super().destroy()
