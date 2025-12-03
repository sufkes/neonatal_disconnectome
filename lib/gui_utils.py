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
        text="Open in FSLeyes:",
        font=ctk.CTkFont(size=11, weight="bold"),
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
        font=ctk.CTkFont(family="Courier", size=10),
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
                font=ctk.CTkFont(family="Courier", size=10),
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
                font=ctk.CTkFont(family="Courier", size=10),
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
