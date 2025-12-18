import os
from tkinter import filedialog

import customtkinter as ctk

from lib.gui_utils import update_widgets_theme
from lib.theme_manager import ThemeableFrame


class StartRunForm(ThemeableFrame):
    def __init__(self, master, next_callback, app=None):
        # Initialize with theme manager
        super().__init__(master, theme_manager=app.theme_manager if app else None)
        self.next_callback = next_callback
        self.app = app  # store app reference
        self.state_manager = app.state_manager if app else None

        # Main layout configuration
        self.grid_columnconfigure(0, weight=1)  # Make the main layout responsive

        runs_frame = ctk.CTkFrame(self, corner_radius=0)
        runs_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=10)
        runs_frame.grid_columnconfigure(0, weight=1)

        runs_label = ctk.CTkLabel(
            runs_frame,
            text="Select a folder to which the run output will be saved:",
        )
        runs_label.grid(row=1, column=0, sticky="w", padx=10, pady=(10, 0))

        self.runs_folder_var = ctk.StringVar()
        runs_folder_entry = ctk.CTkEntry(
            runs_frame, textvariable=self.runs_folder_var, state="readonly"
        )
        runs_folder_entry.grid(row=2, column=0, sticky="ew", padx=(10, 10))

        browse_button = ctk.CTkButton(
            runs_frame, text="Browse...", command=self.browse_folder
        )
        browse_button.grid(row=2, column=1, padx=(0, 10))

        # Inline error message for runs folder
        self.runs_folder_error = ctk.StringVar()
        runs_folder_error_label = ctk.CTkLabel(
            runs_frame, textvariable=self.runs_folder_error, text_color="red"
        )
        runs_folder_error_label.grid(row=3, column=0, sticky="w", padx=10)

        lesion_label = ctk.CTkLabel(
            runs_frame,
            text="Is the input lesion mask already warped to a dHCP template image?",
        )
        lesion_label.grid(row=4, column=0, sticky="w", padx=10, pady=(10, 0))

        self.lesion_var = ctk.StringVar(value="")

        # Inline error message for lesion radio selection
        self.lesion_error = ctk.StringVar()

        yes_radio = ctk.CTkRadioButton(
            runs_frame, text="YES", variable=self.lesion_var, value="yes"
        )
        yes_radio.grid(row=5, column=0, sticky="w", padx=20, pady=10)

        no_radio = ctk.CTkRadioButton(
            runs_frame, text="NO", variable=self.lesion_var, value="no"
        )
        no_radio.grid(row=6, column=0, sticky="w", padx=20, pady=10)

        lesion_error_label = ctk.CTkLabel(
            runs_frame, textvariable=self.lesion_error, text_color="red"
        )
        lesion_error_label.grid(row=7, column=0, sticky="w", padx=10)

        self.next_button = ctk.CTkButton(self, text="Next", command=self.on_next)
        self.next_button.grid(row=2, column=0, sticky="e", padx=20, pady=20)

        self.after(0, self.set_runs_folder)

    def update_theme(self):
        """Update theme for all widgets in this form"""
        super().update_theme()  # Update frame colors

        update_widgets_theme(self, None)

    def set_runs_folder(self):
        if self.state_manager:
            config = self.state_manager.get_config()
            runs_dir = config.runs_folder
            if os.path.isdir(runs_dir):
                # Set runs_folder_var in your UI to runs_folder_path to pre-fill
                self.runs_folder_var.set(runs_dir)

    def browse_folder(self):
        folder_selected = filedialog.askdirectory()
        if folder_selected:
            self.runs_folder_var.set(folder_selected)
            self.runs_folder_error.set("")  # clear runs folder error on selection
            # Update state manager
            if self.state_manager:
                self.state_manager.update_config(runs_folder=folder_selected)

    def clear_lesion_error(self):
        self.lesion_error.set("")  # clear lesion radio error on selection change

    def on_next(self):
        folder = self.runs_folder_var.get()
        lesion = self.lesion_var.get()

        has_error = False

        # Validate runs folder inline error
        if not folder:
            self.runs_folder_error.set("Please enter a valid runs folder")
            has_error = True
            if self.app:
                self.app.logger.error("Runs folder not selected in StartRunForm.")
        else:
            self.runs_folder_error.set("")

        if lesion not in ("yes", "no"):
            self.lesion_error.set("Please select an option for lesion mask warped")
            has_error = True
            if self.app:
                self.app.logger.error(
                    "Lesion mask warped option not selected in StartRunForm."
                )
        else:
            self.lesion_error.set("")

        if has_error:
            return

        # Update state manager
        if self.state_manager:
            self.state_manager.update_processing(
                lesion_already_warped=(lesion == "yes")
            )

        if self.app:
            self.app.logger.info(
                f"StartRunForm input validated: runs_folder={folder}, lesion={lesion}"
            )

        if lesion == "no":
            # Go to warp form (original workflow)
            if self.app and hasattr(self.app, "show_warp_form"):
                self.app.show_warp_form()
        else:
            # Go to warped lesion form (new workflow)
            if self.app and hasattr(self.app, "show_warped_lesion_form"):
                self.app.show_warped_lesion_form()
