import os
from tkinter import filedialog, messagebox

import customtkinter as ctk
from utils import load_settings, update_settings


class StartRunForm(ctk.CTkFrame):
    def __init__(self, master, next_callback, app=None):
        super().__init__(master)
        self.next_callback = next_callback
        self.app = app  # store app reference

        # Main layout configuration
        self.grid_columnconfigure(0, weight=1)  # Make the main layout responsive

        self.runs_frame = ctk.CTkFrame(self, corner_radius=0)
        self.runs_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=10)
        self.runs_frame.grid_columnconfigure(0, weight=1)

        self.runs_label = ctk.CTkLabel(
            self.runs_frame,
            text="Select a folder to which the run output will be saved:",
        )
        self.runs_label.grid(row=1, column=0, sticky="w", padx=10, pady=(10, 0))

        self.runs_folder_var = ctk.StringVar()
        self.runs_folder_entry = ctk.CTkEntry(
            self.runs_frame, textvariable=self.runs_folder_var, state="readonly"
        )
        self.runs_folder_entry.grid(row=2, column=0, sticky="ew", padx=(10, 10))

        self.browse_button = ctk.CTkButton(
            self.runs_frame, text="Browse...", command=self.browse_folder
        )
        self.browse_button.grid(row=2, column=1, padx=(0, 10))

        # Inline error message for runs folder
        self.runs_folder_error = ctk.StringVar()
        self.runs_folder_error_label = ctk.CTkLabel(
            self.runs_frame, textvariable=self.runs_folder_error, text_color="red"
        )
        self.runs_folder_error_label.grid(row=3, column=0, sticky="w", padx=10)

        self.lesion_label = ctk.CTkLabel(
            self.runs_frame,
            text="Is the input lesion mask already warped to a dHCP template image?",
        )
        self.lesion_label.grid(row=4, column=0, sticky="w", padx=10, pady=(10, 0))

        self.lesion_var = ctk.StringVar(value="")

        # Inline error message for lesion radio selection
        self.lesion_error = ctk.StringVar()

        self.yes_radio = ctk.CTkRadioButton(
            self.runs_frame, text="YES", variable=self.lesion_var, value="yes"
        )
        self.yes_radio.grid(row=5, column=0, sticky="w", padx=20, pady=10)

        self.no_radio = ctk.CTkRadioButton(
            self.runs_frame, text="NO", variable=self.lesion_var, value="no"
        )
        self.no_radio.grid(row=6, column=0, sticky="w", padx=20, pady=10)

        self.lesion_error_label = ctk.CTkLabel(
            self.runs_frame, textvariable=self.lesion_error, text_color="red"
        )
        self.lesion_error_label.grid(row=7, column=0, sticky="w", padx=10)

        self.next_button = ctk.CTkButton(self, text="Next", command=self.on_next)
        self.next_button.grid(row=2, column=0, sticky="e", padx=20, pady=20)

        self.after(0, self.set_runs_folder)

    def update_theme(self):
        theme = ctk.ThemeManager.theme

        # Update Frame background
        self.configure(fg_color=theme["CTkFrame"]["fg_color"])
        self.runs_frame.configure(
            fg_color=ctk.ThemeManager.theme["CTkFrame"]["fg_color"],
            border_color=ctk.ThemeManager.theme["CTkFrame"]["border_color"],
        )

        # Update labels text color
        label_color = ctk.ThemeManager.theme["CTkLabel"]["text_color"]
        self.runs_label.configure(text_color=label_color)
        self.lesion_label.configure(text_color=label_color)
        self.runs_folder_error_label.configure(text_color="red")
        self.lesion_error_label.configure(text_color="red")

        # Update entries and buttons
        entry_theme = ctk.ThemeManager.theme["CTkEntry"]
        self.runs_folder_entry.configure(
            fg_color=entry_theme["fg_color"],
            text_color=entry_theme["text_color"],
            border_color=entry_theme["border_color"],
        )

        button_theme = ctk.ThemeManager.theme["CTkButton"]
        self.browse_button.configure(
            fg_color=button_theme["fg_color"],
            hover_color=button_theme["hover_color"],
            text_color=button_theme["text_color"],
        )

        # Update radio buttons
        radio_theme = ctk.ThemeManager.theme["CTkRadioButton"]
        self.yes_radio.configure(text_color=radio_theme["text_color"])
        self.no_radio.configure(text_color=radio_theme["text_color"])

        # Update next button
        self.next_button.configure(
            fg_color=button_theme["fg_color"],
            hover_color=button_theme["hover_color"],
            text_color=button_theme["text_color"],
        )

    def set_runs_folder(self):
        settings = load_settings()
        print(settings)
        if settings:
            runs_folder_path = settings.get("runs_folder", "")
        print(runs_folder_path)
        print(os.path.isdir(runs_folder_path))
        if os.path.isdir(runs_folder_path):
            # Set runs_folder_var in your UI to runs_folder_path to pre-fill
            self.runs_folder_var.set(runs_folder_path)

    def browse_folder(self):
        folder_selected = filedialog.askdirectory()
        if folder_selected:
            self.runs_folder_var.set(folder_selected)
            update_settings(runs_folder=folder_selected)
            self.runs_folder_error.set("")  # clear runs folder error on selection

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

        if self.app:
            self.app.logger.info(
                f"StartRunForm input validated: runs_folder={folder}, lesion={lesion}"
            )

        if lesion == "no":
            self.app.show_warp_form()
        else:
            messagebox.showinfo(
                "Info", "Warped option selected; next screen not implemented."
            )

    def save_data(self, app_data):
        app_data["runs_folder"] = self.runs_folder_var.get()
        app_data["lesion_var"] = self.lesion_var.get()

    def load_data(self, app_data):
        self.runs_folder_var.set(app_data.get("runs_folder", ""))
        self.lesion_var.set(app_data.get("lesion_var", ""))
        self.runs_folder_error.set("")  # clear inline error on load
        self.lesion_error.set("")
