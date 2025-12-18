import customtkinter as ctk
from pathlib import Path
from tkinter import messagebox


# Create a new utility function for command display
def create_command_display(parent, command, row_start=0):
    """
    Create a clean, compact command display with copy button

    Args:
        parent: Parent widget
        command: Command string to display
        row_start: Starting row in parent grid

    Returns:
        Last row index used
    """
    # Instruction label
    instruction_label = ctk.CTkLabel(
        parent,
        text="Click the button to copy the following command and paste into your terminal to open in FSLeyes:",
        font=ctk.CTkFont(size=12, weight="bold"),
        anchor="w",
    )
    instruction_label.grid(row=row_start, column=0, sticky="w", padx=5, pady=(5, 2))

    # Command display frame with border
    command_outer_frame = ctk.CTkFrame(parent, border_width=1, corner_radius=6)
    command_outer_frame.grid(
        row=row_start + 1, column=0, sticky="ew", padx=5, pady=(0, 5)
    )
    command_outer_frame.grid_columnconfigure(0, weight=1)

    # Inner scrollable frame for command
    command_scroll = ctk.CTkScrollableFrame(
        command_outer_frame,
        orientation="horizontal",
        height=35,
        corner_radius=0,
        fg_color="transparent",
    )
    command_scroll.grid(row=0, column=0, sticky="ew", padx=2, pady=2)

    # Parse and display command parts
    parts = command.split()
    base_command = parts[0] if parts else ""

    # Base command label
    base_label = ctk.CTkLabel(
        command_scroll,
        text=base_command + " ",
        font=ctk.CTkFont(family="Verdana", size=12),
        anchor="w",
    )
    base_label.grid(row=0, column=0, sticky="w", padx=(5, 0))

    # Add clickable path labels
    col = 1
    for i, part in enumerate(parts[1:]):
        if Path(part).exists():
            # Clickable file path
            path_label = ctk.CTkLabel(
                command_scroll,
                text=part + " ",
                font=ctk.CTkFont(family="Verdana", size=12),
                text_color="#0074d9",
                cursor="hand2",
                anchor="w",
            )
            path_label.grid(row=0, column=col, sticky="w", padx=(0, 2))

            # Add hover effects
            def on_enter(e, lbl=path_label):
                lbl.configure(text_color="#0052a3")

            def on_leave(e, lbl=path_label):
                lbl.configure(text_color="#0074d9")

            path_label.bind("<Enter>", on_enter)
            path_label.bind("<Leave>", on_leave)
            path_label.bind("<Button-1>", lambda e, p=part: open_in_file_browser(p))

        else:
            # Non-clickable flag or text
            flag_label = ctk.CTkLabel(
                command_scroll,
                text=part + " ",
                font=ctk.CTkFont(family="Verdana", size=12),
                anchor="w",
            )
            flag_label.grid(row=0, column=col, sticky="w", padx=(0, 2))

        col += 1

    # Copy button (fixed width, outside scroll area)
    copy_button = ctk.CTkButton(
        command_outer_frame,
        text="📋",
        width=40,
        height=35,
        corner_radius=0,
        font=ctk.CTkFont(size=12),
        command=lambda: copy_to_clipboard(parent, command),
    )
    copy_button.grid(row=0, column=1, sticky="ns")

    return row_start + 2


def copy_to_clipboard(widget, text):
    """Copy text to clipboard with user feedback"""
    try:
        widget.clipboard_clear()
        widget.clipboard_append(text)
        widget.update()

        messagebox.showinfo("Copied", "Command copied to clipboard!", parent=widget)

    except Exception as e:
        messagebox.showerror("Error", f"Failed to copy: {e}", parent=widget)


def open_in_file_browser(path):
    """Open file in system file browser"""
    from lib.utils import open_in_file_browser as open_fb

    open_fb(path)


def update_widgets_theme(widgets, widget_type: str = None):
    """
    Enhanced utility function to update theme for multiple widgets

    Args:
        widgets: List of widgets, single widget, or parent widget to traverse
        widget_type: Type name like "CTkLabel", "CTkButton", "auto", or None
                    - If "auto": automatically detect widget types
                    - If None: traverse all children recursively
                    - If specific type: only update widgets of that type

    Examples:
        # Update specific widgets of same type
        update_widgets_theme([label1, label2, label3], "CTkLabel")

        # Auto-detect and update mixed widget types
        update_widgets_theme([label, button, entry], "auto")

        # Recursively update all widgets in a container
        update_widgets_theme(parent_frame, None)
    """
    theme = ctk.ThemeManager.theme
    appearance_mode = ctk.get_appearance_mode()
    is_dark = appearance_mode == "Dark"

    # Helper to get theme color
    def get_color(widget_type_name, property_name, default_light, default_dark):
        try:
            if widget_type_name in theme and property_name in theme[widget_type_name]:
                value = theme[widget_type_name][property_name]
                if isinstance(value, (list, tuple)) and len(value) >= 2:
                    return value[1] if is_dark else value[0]
                return value
        except:
            pass
        return default_dark if is_dark else default_light

    # Convert single widget to list
    if not isinstance(widgets, list):
        widgets = [widgets]

    # If widget_type is None, recursively update all children
    if widget_type is None:
        for widget in widgets:
            _update_widget_recursive(widget, theme, is_dark, get_color)
        return

    # Process each widget
    for widget in widgets:
        if not widget or not widget.winfo_exists():
            continue

        # Auto-detect widget type
        if widget_type == "auto":
            actual_type = widget.__class__.__name__
        else:
            actual_type = widget_type

        try:
            _update_widget_by_type(widget, actual_type, theme, is_dark, get_color)
        except Exception as e:
            # Silently continue if update fails
            pass


def _update_widget_by_type(widget, widget_type, theme, is_dark, get_color):
    """Update a single widget based on its type"""

    if not widget.winfo_exists():
        return

    # Get theme for this widget type
    widget_theme = theme.get(widget_type, {})

    # Common properties that most widgets support
    if "fg_color" in widget_theme:
        try:
            widget.configure(fg_color=widget_theme["fg_color"])
        except:
            pass

    if "text_color" in widget_theme:
        try:
            # Special check: don't update clickable paths (they stay blue)
            if hasattr(widget, "cget"):
                cursor = widget.cget("cursor")
                if cursor == "hand2":  # Skip clickable paths
                    return
            widget.configure(text_color=widget_theme["text_color"])
        except:
            pass

    if "border_color" in widget_theme:
        try:
            widget.configure(border_color=widget_theme["border_color"])
        except:
            pass

    # Button-specific
    if widget_type == "CTkButton":
        if "hover_color" in widget_theme:
            try:
                widget.configure(hover_color=widget_theme["hover_color"])
            except:
                pass

    # Entry-specific
    if widget_type == "CTkEntry":
        if "placeholder_text_color" in widget_theme:
            try:
                widget.configure(
                    placeholder_text_color=widget_theme["placeholder_text_color"]
                )
            except:
                pass

    # TabView-specific
    if widget_type == "CTkTabview":
        try:
            widget.configure(
                fg_color=get_color("CTkFrame", "fg_color", "#FFFFFF", "#2B2B2B"),
                border_color=get_color(
                    "CTkFrame", "border_color", "#E0E0E0", "#3A3A3A"
                ),
                segmented_button_fg_color=get_color(
                    "CTkSegmentedButton", "fg_color", "#E5E5EA", "#2C2C2E"
                ),
                segmented_button_selected_color=get_color(
                    "CTkSegmentedButton", "selected_color", "#007AFF", "#0A84FF"
                ),
                segmented_button_selected_hover_color=get_color(
                    "CTkSegmentedButton", "selected_hover_color", "#0051D5", "#409CFF"
                ),
                segmented_button_unselected_color=get_color(
                    "CTkSegmentedButton", "unselected_color", "#E5E5EA", "#2C2C2E"
                ),
                segmented_button_unselected_hover_color=get_color(
                    "CTkSegmentedButton", "unselected_hover_color", "#D1D1D6", "#3A3A3C"
                ),
                text_color=get_color("CTkLabel", "text_color", "#000000", "#FFFFFF"),
            )
        except:
            pass

    # RadioButton-specific
    if widget_type == "CTkRadioButton":
        if "hover_color" in widget_theme:
            try:
                widget.configure(hover_color=widget_theme["hover_color"])
            except:
                pass


def _update_widget_recursive(widget, theme, is_dark, get_color):
    """Recursively update a widget and all its children"""

    if not widget or not widget.winfo_exists():
        return

    # Determine widget type
    widget_class = widget.__class__.__name__

    # Update this widget
    try:
        _update_widget_by_type(widget, widget_class, theme, is_dark, get_color)
    except:
        pass

    # Recurse to children
    try:
        for child in widget.winfo_children():
            _update_widget_recursive(child, theme, is_dark, get_color)
    except:
        pass
