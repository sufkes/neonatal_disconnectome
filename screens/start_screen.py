import customtkinter as ctk
from tkinter import filedialog, messagebox

class StartRunForm(ctk.CTkFrame):
    def __init__(self, master, next_callback, app=None):
        super().__init__(master)
        self.next_callback = next_callback
        self.app = app  # store app reference

        runs_frame = ctk.CTkFrame(self, corner_radius=10, fg_color="#fff")
        runs_frame.pack(fill='x', pady=10, padx=10)

        runs_label = ctk.CTkLabel(runs_frame, text="Select a folder to which the run output will be saved:")
        runs_label.pack(anchor='w', pady=(10, 0), padx=10)

        runs_folder_frame = ctk.CTkFrame(runs_frame)
        runs_folder_frame.pack(fill='x', pady=10, padx=10)

        self.runs_folder_var = ctk.StringVar()
        self.runs_folder_entry = ctk.CTkEntry(runs_folder_frame, textvariable=self.runs_folder_var, state="readonly")
        self.runs_folder_entry.pack(side='left', fill='x', expand=True, padx=(0,10))

        browse_button = ctk.CTkButton(runs_folder_frame, text="Browse...", command=self.browse_folder)
        browse_button.pack(side='left')

        # Inline error message for runs folder
        self.runs_folder_error = ctk.StringVar()
        self.runs_folder_error_label = ctk.CTkLabel(runs_frame, textvariable=self.runs_folder_error, text_color="red")
        self.runs_folder_error_label.pack(anchor='w', padx=10)

        lesion_frame = ctk.CTkFrame(self, corner_radius=10, fg_color="#fff")
        lesion_frame.pack(fill='x', pady=10, padx=10)

        lesion_label = ctk.CTkLabel(lesion_frame, text="Is the input lesion mask already warped to a dHCP template image?")
        lesion_label.pack(anchor='w', pady=(10, 0), padx=10)

        self.lesion_var = ctk.StringVar(value="")

         # Inline error message for lesion radio selection
        self.lesion_error = ctk.StringVar()

        yes_radio = ctk.CTkRadioButton(lesion_frame, text="YES", variable=self.lesion_var, value="yes")
        yes_radio.pack(side='left', padx=20, pady=10)

        no_radio = ctk.CTkRadioButton(lesion_frame, text="NO", variable=self.lesion_var, value="no")
        no_radio.pack(side='left', padx=20, pady=10)

        self.lesion_error_label = ctk.CTkLabel(lesion_frame, textvariable=self.lesion_error, text_color="red")
        self.lesion_error_label.pack(anchor='w', padx=10)

        next_button = ctk.CTkButton(self, text="Next", command=self.on_next, fg_color="#ff4136", hover_color="#cc0000")
        next_button.pack(side='right', padx=20, pady=20)

    def browse_folder(self):
        folder_selected = filedialog.askdirectory()
        if folder_selected:
            self.runs_folder_var.set(folder_selected)
            self.runs_folder_error.set('')  # clear runs folder error on selection

    def clear_lesion_error(self):
        self.lesion_error.set('') # clear lesion radio error on selection change

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
              self.app.logger.error("Lesion mask warped option not selected in StartRunForm.")
        else:
            self.lesion_error.set("")

        if has_error:
          return

        if self.app:
          self.app.logger.info(f"StartRunForm input validated: runs_folder={folder}, lesion={lesion}")

        if lesion == "no":
          self.app.show_warp_form()
        else:
          messagebox.showinfo("Info", "Warped option selected; next screen not implemented.")

    def save_data(self, app_data):
        app_data['runs_folder'] = self.runs_folder_var.get()
        app_data['lesion_var'] = self.lesion_var.get()

    def load_data(self, app_data):
        self.runs_folder_var.set(app_data.get('runs_folder', ''))
        self.lesion_var.set(app_data.get('lesion_var', ''))
        self.runs_folder_error.set('')  # clear inline error on load
        self.lesion_error.set('')
