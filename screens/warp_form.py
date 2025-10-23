import customtkinter as ctk
from tkinter import filedialog
from PIL import Image
import re
import os
import threading

from makeThumbnails import plotThreeView
from constants import THUMBNAILS_DIR
from .loading_overlay import LoadingOverlay

from backend.logging_utils import run_step1_with_logging


class WarpForm(ctk.CTkFrame):
    def __init__(self, master, go_back_callback=None, app=None):
        super().__init__(master)
        self.go_back_callback = go_back_callback
        self.app = app
        self.grid_columnconfigure(0, weight=1)

        self.loading_overlay = LoadingOverlay(master=self)

        row_index = 0

        self.form_frame = ctk.CTkFrame(self, corner_radius=0)
        self.form_frame.grid(row=row_index, column=0, sticky="ew", padx=10, pady=10)
        self.form_frame.grid_columnconfigure(0, weight=1)

        row_index += 1

        # Store references to widgets to update later
        self.image_data_label = ctk.CTkLabel(
            self.form_frame,
            text="Image Data",
            font=ctk.CTkFont(size=16, weight="bold"),
            padx=10,
            pady=10,
        )
        self.image_data_label.grid(
            row=row_index, column=0, sticky="w", padx=20, pady=(0, 10)
        )

        row_index += 1

        self.brain_image_path = ctk.StringVar()
        self.brain_image_error = ctk.StringVar()

        self.brain_label = ctk.CTkLabel(
            self.form_frame,
            text="Subject brain image in NIFTI format (.nii or .nii.gz):",
        )
        self.brain_label.grid(row=row_index, column=0, sticky="w", padx=20, pady=(0, 5))

        row_index += 1

        self.brain_image_entry = ctk.CTkEntry(
            self.form_frame, textvariable=self.brain_image_path, state="readonly"
        )
        self.brain_image_entry.grid(
            row=row_index, column=0, sticky="ew", padx=(20, 110)
        )

        self.brain_browse_button = ctk.CTkButton(
            self.form_frame, text="Browse...", command=self.browse_brain_image
        )
        self.brain_browse_button.grid(row=row_index, column=1, sticky="w", padx=(0, 20))

        row_index += 1

        self.brain_image_error_label = ctk.CTkLabel(
            self.form_frame, textvariable=self.brain_image_error, text_color="red"
        )
        self.brain_image_error_label.grid(
            row=row_index, column=0, columnspan=2, sticky="w", padx=20, pady=(5, 10)
        )

        row_index += 1

        self.thumbnail_img = None
        self.thumbnail_label = ctk.CTkLabel(self.form_frame, text="")
        self.thumbnail_label.grid(
            row=row_index, column=0, columnspan=2, sticky="ew", padx=20, pady=(10, 20)
        )
        print(row_index)
        row_index += 3

        caption_text = (
            "Preview of subject brain image in sagittal, coronal, and axial planes"
        )
        self.caption_label = ctk.CTkLabel(
            self.form_frame,
            text=caption_text,
            font=ctk.CTkFont(size=11, slant="italic"),
            justify="center",
            anchor="center",
        )

        self.lesion_mask_path = ctk.StringVar()
        self.lesion_mask_error = ctk.StringVar()

        self.lesion_label = ctk.CTkLabel(
            self.form_frame,
            text="Subject brain lesion mask in NIFTI format (.nii or .nii.gz):",
        )
        self.lesion_label.grid(
            row=row_index, column=0, sticky="w", padx=20, pady=(0, 5)
        )

        row_index += 1

        self.lesion_mask_entry = ctk.CTkEntry(
            self.form_frame, textvariable=self.lesion_mask_path, state="readonly"
        )
        self.lesion_mask_entry.grid(
            row=row_index, column=0, sticky="ew", padx=(20, 110)
        )

        self.lesion_browse_button = ctk.CTkButton(
            self.form_frame, text="Browse...", command=self.browse_lesion_mask
        )
        self.lesion_browse_button.grid(
            row=row_index, column=1, sticky="w", padx=(0, 20)
        )

        row_index += 1

        self.lesion_mask_error_label = ctk.CTkLabel(
            self.form_frame, textvariable=self.lesion_mask_error, text_color="red"
        )
        self.lesion_mask_error_label.grid(
            row=row_index, column=0, columnspan=2, sticky="w", padx=20, pady=(5, 10)
        )

        row_index += 1

        self.brain_type = ctk.StringVar()
        self.brain_type_error = ctk.StringVar()

        self.type_label = ctk.CTkLabel(self.form_frame, text="Type of brain image:")
        self.type_label.grid(
            row=row_index, column=0, columnspan=2, sticky="w", padx=20, pady=(10, 0)
        )

        row_index += 1

        self.t1_radio_button = ctk.CTkRadioButton(
            self.form_frame, text="T1w", variable=self.brain_type, value="T1w"
        )
        self.t2_radio_button = ctk.CTkRadioButton(
            self.form_frame, text="T2w", variable=self.brain_type, value="T2w"
        )

        self.t1_radio_button.grid(row=row_index, column=0, padx=30, pady=2, sticky="w")
        row_index += 1
        self.t2_radio_button.grid(row=row_index, column=0, padx=30, pady=2, sticky="w")
        row_index += 1

        self.brain_type_error_label = ctk.CTkLabel(
            self.form_frame, textvariable=self.brain_type_error, text_color="red"
        )
        self.brain_type_error_label.grid(
            row=row_index, column=0, columnspan=2, sticky="w", padx=20
        )
        row_index += 1

        self.subject_label = ctk.CTkLabel(
            self.form_frame,
            text="Subject data",
            font=ctk.CTkFont(size=16, weight="bold"),
        )
        self.subject_label.grid(
            row=row_index, column=0, sticky="w", padx=20, pady=(15, 10)
        )
        row_index += 1

        self.subject_id = ctk.StringVar()
        self.subject_id_error = ctk.StringVar()

        self.subject_id_label = ctk.CTkLabel(
            self.form_frame,
            text="Subject ID (letters, numbers, underscore, dash only):",
        )
        self.subject_id_label.grid(
            row=row_index, column=0, sticky="w", padx=20, pady=(0, 5)
        )
        row_index += 1

        self.subject_id_entry = ctk.CTkEntry(
            self.form_frame, textvariable=self.subject_id
        )
        self.subject_id_entry.grid(
            row=row_index, column=0, columnspan=2, sticky="ew", padx=20
        )
        row_index += 1

        self.subject_id_error_label = ctk.CTkLabel(
            self.form_frame, textvariable=self.subject_id_error, text_color="red"
        )
        self.subject_id_error_label.grid(
            row=row_index, column=0, columnspan=2, sticky="w", padx=20
        )
        row_index += 1

        self.gest_age = ctk.StringVar()
        self.gest_age_error = ctk.StringVar()

        self.gest_label = ctk.CTkLabel(
            self.form_frame, text="Subject's gestational age at scan time (weeks):"
        )
        self.gest_label.grid(row=row_index, column=0, sticky="w", padx=20, pady=(10, 5))
        row_index += 1

        self.gest_entry = ctk.CTkEntry(self.form_frame, textvariable=self.gest_age)
        self.gest_entry.grid(
            row=row_index, column=0, columnspan=2, sticky="ew", padx=20
        )
        row_index += 1

        self.gest_age_error_label = ctk.CTkLabel(
            self.form_frame, textvariable=self.gest_age_error, text_color="orange"
        )
        self.gest_age_error_label.grid(
            row=row_index, column=0, columnspan=2, sticky="w", padx=20
        )
        row_index += 1

        self.button_frame = ctk.CTkFrame(self.form_frame)
        self.button_frame.grid(
            row=row_index, column=0, columnspan=2, sticky="ew", padx=20, pady=20
        )
        row_index += 1

        self.button_frame.grid_columnconfigure(0, weight=1)
        self.button_frame.grid_columnconfigure(1, weight=1)

        self.back_button = ctk.CTkButton(
            self.button_frame, text="Back", command=self.go_back
        )
        self.back_button.grid(row=0, column=0, sticky="w")

        self.next_button = ctk.CTkButton(
            self.button_frame, text="Next", command=self.on_next
        )
        self.next_button.grid(row=0, column=1, sticky="e")

    def update_theme(self):
        theme = ctk.ThemeManager.theme

        # Update Frame background
        self.configure(fg_color=theme["CTkFrame"]["fg_color"])

        # Labels text color
        label_fg = theme["CTkLabel"]["text_color"]
        for lbl in [
            self.image_data_label,
            self.brain_label,
            self.lesion_label,
            self.type_label,
            self.subject_label,
            self.subject_id_label,
            self.gest_label,
            self.caption_label,
        ]:
            lbl.configure(text_color=label_fg)

        # Error labels keep their color but update fg_color property
        for err_lbl in [
            self.brain_image_error_label,
            self.lesion_mask_error_label,
            self.brain_type_error_label,
            self.subject_id_error_label,
            self.gest_age_error_label,
        ]:
            err_lbl.configure(fg_color=theme["CTkFrame"]["fg_color"])  # match frame bg

        # Entries styling
        entry_theme = theme["CTkEntry"]
        for entry in [
            self.brain_image_entry,
            self.lesion_mask_entry,
            self.subject_id_entry,
            self.gest_entry,
        ]:
            entry.configure(
                fg_color=entry_theme["fg_color"],
                text_color=entry_theme["text_color"],
                border_color=entry_theme["border_color"],
            )

        # Buttons style
        self.button_frame.configure(fg_color=theme["CTkFrame"]["fg_color"])
        button_theme = theme["CTkButton"]
        for btn in [
            self.back_button,
            self.next_button,
            self.brain_browse_button,
            self.lesion_browse_button,
        ]:
            if btn.winfo_exists():
                btn.configure(
                    fg_color=button_theme["fg_color"],
                    hover_color=button_theme["hover_color"],
                    text_color=button_theme["text_color"],
                )

        # Radio buttons text color
        radio_theme = theme["CTkRadioButton"]
        for rb in [self.t1_radio_button, self.t2_radio_button]:
            rb.configure(text_color=radio_theme["text_color"])

        # Update caption label fg_color to match label color
        self.caption_label.configure(text_color=label_fg)

        # Update thumbnail label background (optional)
        if self.thumbnail_label.winfo_exists():
            self.thumbnail_label.configure(fg_color=theme["CTkFrame"]["fg_color"])

    def browse_brain_image(self):
        path = filedialog.askopenfilename(filetypes=[("NIFTI files", "*.nii *.nii.gz")])
        if path:
            self.brain_image_path.set(path)
            self.brain_image_error.set("")

            # Call your backend function to generate Pillow thumbnail image
            # (Assuming you have imported or passed 'backend' somewhere)
            outpath = os.path.join(THUMBNAILS_DIR, "brain_image_thumbnail.png")
            plotThreeView(path, outpath)  # your backend function

            thumbnail_pil = Image.open(outpath)

            # Convert Pillow image to CTkImage for CustomTkinter
            self.thumbnail_img = ctk.CTkImage(
                light_image=thumbnail_pil,
                dark_image=thumbnail_pil,
                size=thumbnail_pil.size,
            )

            # Update the label to show the thumbnail and make it visible
            self.thumbnail_label.configure(image=self.thumbnail_img, text="")

            # Show caption label if not visible
            if not self.caption_label.winfo_ismapped():
                self.caption_label.grid(row=7, column=0, pady=(2, 15))
                self.form_frame.grid_columnconfigure(0, weight=1)

    def set_thumbnail(self):
        outpath = os.path.join(THUMBNAILS_DIR, "brain_image_thumbnail.png")
        if outpath:
            thumbnail_pil = Image.open(outpath)

            # Convert Pillow image to CTkImage for CustomTkinter
            self.thumbnail_img = ctk.CTkImage(
                light_image=thumbnail_pil,
                dark_image=thumbnail_pil,
                size=thumbnail_pil.size,
            )

            # Update the label to show the thumbnail and make it visible
            self.thumbnail_label.configure(image=self.thumbnail_img, text="")

            # Show caption label if not visible
            if not self.caption_label.winfo_ismapped():
                self.caption_label.grid(
                    row=6, column=0, columnspan=2, sticky="ew", padx=10, pady=(2, 15)
                )
                self.form_frame.grid_columnconfigure(0, weight=1)
                self.form_frame.grid_rowconfigure(6, weight=1)

    def browse_lesion_mask(self):
        path = filedialog.askopenfilename(filetypes=[("NIFTI files", "*.nii *.nii.gz")])
        if path:
            self.lesion_mask_path.set(path)
            self.lesion_mask_error.set("")

    def validate_form(self):
        valid = True

        if not self.brain_image_path.get():
            self.brain_image_error.set("Please enter a valid brain image")
            valid = False
        else:
            self.brain_image_error.set("")

        if not self.lesion_mask_path.get():
            self.lesion_mask_error.set("Please enter a valid lesion mask")
            valid = False
        else:
            self.lesion_mask_error.set("")

        if self.brain_type.get() not in ["T1w", "T2w"]:
            self.brain_type_error.set("Please select the brain type")
            valid = False
        else:
            self.brain_type_error.set("")

        pattern = r"^[\w-]+$"
        if not re.match(pattern, self.subject_id.get()):
            self.subject_id_error.set(
                "Please enter a valid subject id. Only letters, numbers, underscore and dashes allowed. No special characters and no spaces"
            )
            valid = False
        else:
            self.subject_id_error.set("")

        try:
            age = float(self.gest_age.get())
            self.gest_age_error.set("")
            if age < 28 or age > 44:
                self.gest_age_error.set(
                    "Warning: Age is outside of 28-44 weeks. Registration may be poor."
                )
        except ValueError:
            self.gest_age_error.set(
                "Please enter a valid numeric value for gestational age"
            )
            valid = False

        return valid

    def on_next(self):
        if self.validate_form():
            self.save_data(self.app.app_data)
            if hasattr(self.app, "show_disconnectome_form"):
                self.next_button.configure(state="disabled")
                self.back_button.configure(state="disabled")

                self.loading_overlay.show()

                # Retrieve values
                runs_dir = self.app.app_data.get("runs_folder", "")
                subject = self.subject_id.get()
                image_type = self.brain_type.get()
                moving_image = self.brain_image_path.get()
                lesion_image = self.lesion_mask_path.get()
                age = self.gest_age.get()

                self.app.logger.info(
                    f"runs_dir: {runs_dir}\nsubject: {subject}\nimage_type: {image_type}\nmoving_image: {moving_image}\nlesion_image: {lesion_image}\nage: {age}"
                )

                # Run step1 in a background thread
                def run_step1():
                    success = run_step1_with_logging(
                        runs_dir, subject, image_type, moving_image, lesion_image, age
                    )
                    # Schedule UI update on main thread:
                    self.after(0, lambda: self.on_step1_complete(success))

                threading.Thread(target=run_step1, daemon=True).start()

    def on_step1_complete(self, success):
        # Hide loading overlay and re-enable button
        self.loading_overlay.hide()
        self.next_button.configure(state="normal")
        self.back_button.configure(state="normal")

        if success:
            # Navigate to next screen
            if self.app:
                self.app.show_disconnectome_form()
        else:
            # Error notification; you can customize this popup/dialog
            self.app.logger.error("Step1 failed. Please check logs and try again.")

    def go_back(self):
        if self.go_back_callback:
            self.save_data(self.app.app_data)
            self.go_back_callback()

    def save_data(self, app_data):
        app_data["brain_image_path"] = self.brain_image_path.get()
        app_data["lesion_mask_path"] = self.lesion_mask_path.get()
        app_data["brain_type"] = self.brain_type.get()
        app_data["subject_id"] = self.subject_id.get()
        app_data["gest_age"] = self.gest_age.get()

    def load_data(self, app_data):
        self.brain_image_path.set(app_data.get("brain_image_path", ""))
        self.lesion_mask_path.set(app_data.get("lesion_mask_path", ""))
        self.brain_type.set(app_data.get("brain_type", ""))
        self.subject_id.set(app_data.get("subject_id", ""))
        self.gest_age.set(app_data.get("gest_age", ""))
        if app_data.get("brain_image_path", ""):
            self.set_thumbnail()
