
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
        self.app = app  # store app reference
        self.grid_columnconfigure(0, weight=1)  # make column 0 expandable

        # Loading overlay
        self.loading_overlay = LoadingOverlay(master=self)

        # Image Data section
        image_data_label = ctk.CTkLabel(self, text="Image Data", font=ctk.CTkFont(size=16, weight="bold"))
        image_data_label.grid(row=2, column=0, sticky="w", padx=20, pady=(0, 10))

        self.brain_image_path = ctk.StringVar()
        self.brain_image_error = ctk.StringVar()

        brain_label = ctk.CTkLabel(self, text="Subject brain image in NIFTI format (.nii or .nii.gz):")
        brain_label.grid(row=3, column=0, sticky="w", padx=20, pady=(0, 5))

        brain_entry = ctk.CTkEntry(self, textvariable=self.brain_image_path, state="readonly")
        brain_entry.grid(row=4, column=0, sticky="ew", padx=(20, 110))  # leave room for button

        brain_browse = ctk.CTkButton(self, text="Browse...", command=self.browse_brain_image)
        brain_browse.grid(row=4, column=1, sticky="w", padx=(0, 20))

        brain_error_label = ctk.CTkLabel(self, textvariable=self.brain_image_error, text_color="red")
        brain_error_label.grid(row=5, column=0, columnspan=2, sticky="w", padx=20, pady=(5, 10))

        # Add a label for the thumbnail preview below the brain image selector
        self.thumbnail_img = None  # will hold CTkImage to prevent garbage collection
        self.thumbnail_label = ctk.CTkLabel(self, text="")
        self.thumbnail_label.grid(row=6, column=0, columnspan=2, sticky="w", padx=20, pady=(10, 20))

        # Create a separate label for the caption text
        caption_text = "Preview of subject brain image in sagittal, coronal, and axial planes"
        self.caption_label = ctk.CTkLabel(self, text=caption_text, font=ctk.CTkFont(size=11, slant="italic"))


        self.lesion_mask_path = ctk.StringVar()
        self.lesion_mask_error = ctk.StringVar()


        lesion_label = ctk.CTkLabel(self, text="Subject brain lesion mask in NIFTI format (.nii or .nii.gz):")
        lesion_label.grid(row=8, column=0, sticky="w", padx=20, pady=(0, 5))

        lesion_entry = ctk.CTkEntry(self, textvariable=self.lesion_mask_path, state="readonly")
        lesion_entry.grid(row=9, column=0, sticky="ew", padx=(20, 110))

        lesion_browse = ctk.CTkButton(self, text="Browse...", command=self.browse_lesion_mask)
        lesion_browse.grid(row=9, column=1, sticky="w", padx=(0, 20))

        lesion_error_label = ctk.CTkLabel(self, textvariable=self.lesion_mask_error, text_color="red")
        lesion_error_label.grid(row=10, column=0, columnspan=2, sticky="w", padx=20, pady=(5, 10))

        self.brain_type = ctk.StringVar()
        self.brain_type_error = ctk.StringVar()

        type_label = ctk.CTkLabel(self, text="Type of brain image:")
        type_label.grid(row=11, column=0, columnspan=2, sticky="w", padx=20, pady=(10, 0))

        # Radio buttons for T1w and T2w
        t1_radio = ctk.CTkRadioButton(self, text="T1w", variable=self.brain_type, value="T1w")
        t2_radio = ctk.CTkRadioButton(self, text="T2w", variable=self.brain_type, value="T2w")

        t1_radio.grid(row=12, column=0, padx=30, pady=2, sticky="w")
        t2_radio.grid(row=13, column=0, padx=30, pady=2, sticky="w")

        type_error_label = ctk.CTkLabel(self, textvariable=self.brain_type_error, text_color="red")
        type_error_label.grid(row=14, column=0, columnspan=2, sticky="w", padx=20)

        subject_label = ctk.CTkLabel(self, text="Subject data", font=ctk.CTkFont(size=16, weight="bold"))
        subject_label.grid(row=15, column=0, sticky="w", padx=20, pady=(15, 10))

        self.subject_id = ctk.StringVar()
        self.subject_id_error = ctk.StringVar()

        subject_id_label = ctk.CTkLabel(self, text="Subject ID (letters, numbers, underscore, dash only):")
        subject_id_label.grid(row=16, column=0, sticky="w", padx=20, pady=(0, 5))

        subject_entry = ctk.CTkEntry(self, textvariable=self.subject_id)
        subject_entry.grid(row=17, column=0, columnspan=2, sticky="ew", padx=20)

        subject_error_label = ctk.CTkLabel(self, textvariable=self.subject_id_error, text_color="red")
        subject_error_label.grid(row=18, column=0, columnspan=2, sticky="w", padx=20)

        self.gest_age = ctk.StringVar()
        self.gest_age_error = ctk.StringVar()

        gest_label = ctk.CTkLabel(self, text="Subject's gestational age at scan time (weeks):")
        gest_label.grid(row=19, column=0, sticky="w", padx=20, pady=(10, 5))

        gest_entry = ctk.CTkEntry(self, textvariable=self.gest_age)
        gest_entry.grid(row=20, column=0, columnspan=2, sticky="ew", padx=20)

        gest_error_label = ctk.CTkLabel(self, textvariable=self.gest_age_error, text_color="orange")
        gest_error_label.grid(row=21, column=0, columnspan=2, sticky="w", padx=20)

        # Buttons frame
        button_frame = ctk.CTkFrame(self)
        button_frame.grid(row=22, column=0, columnspan=2, sticky="ew", padx=20, pady=20)
        button_frame.grid_columnconfigure(0, weight=1)
        button_frame.grid_columnconfigure(1, weight=1)

        self.back_button = ctk.CTkButton(button_frame, text="Back", command=self.go_back)
        self.back_button.grid(row=0, column=0, sticky="w")

        self.next_button = ctk.CTkButton(button_frame, text="Next", command=self.on_next)
        self.next_button.grid(row=0, column=1, sticky="e")

    def browse_brain_image(self):
      path = filedialog.askopenfilename(filetypes=[("NIFTI files", "*.nii *.nii.gz")])
      if path:
        self.brain_image_path.set(path)
        self.brain_image_error.set('')

        # Call your backend function to generate Pillow thumbnail image
        # (Assuming you have imported or passed 'backend' somewhere)
        outpath = os.path.join(THUMBNAILS_DIR,'brain_image_thumbnail.png')
        plotThreeView(path, outpath)  # your backend function

        thumbnail_pil = Image.open(outpath)

        # Convert Pillow image to CTkImage for CustomTkinter
        self.thumbnail_img = ctk.CTkImage(light_image=thumbnail_pil, dark_image=thumbnail_pil, size=thumbnail_pil.size)

        # Update the label to show the thumbnail and make it visible
        self.thumbnail_label.configure(image=self.thumbnail_img, text="")

        # Show caption label if not visible
        if not self.caption_label.winfo_ismapped():
          self.caption_label.grid(row=7, column=0, pady=(2, 15))

    def browse_lesion_mask(self):
        path = filedialog.askopenfilename(filetypes=[("NIFTI files", "*.nii *.nii.gz")])
        if path:
            self.lesion_mask_path.set(path)
            self.lesion_mask_error.set('')

    def validate_form(self):
        valid = True

        if not self.brain_image_path.get():
            self.brain_image_error.set("Please enter a valid brain image")
            valid = False
        else:
            self.brain_image_error.set('')

        if not self.lesion_mask_path.get():
            self.lesion_mask_error.set("Please enter a valid lesion mask")
            valid = False
        else:
            self.lesion_mask_error.set('')

        if self.brain_type.get() not in ["T1w", "T2w"]:
            self.brain_type_error.set("Please select the brain type")
            valid = False
        else:
            self.brain_type_error.set('')

        pattern = r'^[\w-]+$'
        if not re.match(pattern, self.subject_id.get()):
            self.subject_id_error.set("Please enter a valid subject id. Only letters, numbers, underscore and dashes allowed. No special characters and no spaces")
            valid = False
        else:
            self.subject_id_error.set('')

        try:
            age = float(self.gest_age.get())
            self.gest_age_error.set('')
            if age < 28 or age > 44:
                self.gest_age_error.set("Warning: Age is outside of 28-44 weeks. Registration may be poor.")
        except ValueError:
            self.gest_age_error.set("Please enter a valid numeric value for gestational age")
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
          runs_dir = self.app.app_data.get('runs_folder', '')
          subject = self.subject_id.get()
          image_type = self.brain_type.get()
          moving_image = self.brain_image_path.get()
          lesion_image = self.lesion_mask_path.get()
          age = self.gest_age.get()

          self.app.logger.info(f"runs_dir: {runs_dir}\nsubject: {subject}\nimage_type: {image_type}\nmoving_image: {moving_image}\nlesion_image: {lesion_image}\nage: {age}")

          # Run step1 in a background thread
          def run_step1():
              success = run_step1_with_logging(runs_dir, subject, image_type, moving_image, lesion_image, age)
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
        app_data['brain_image_path'] = self.brain_image_path.get()
        app_data['lesion_mask_path'] = self.lesion_mask_path.get()
        app_data['brain_type'] = self.brain_type.get()
        app_data['subject_id'] = self.subject_id.get()
        app_data['gest_age'] = self.gest_age.get()

    def load_data(self, app_data):
        self.brain_image_path.set(app_data.get('brain_image_path', ''))
        self.lesion_mask_path.set(app_data.get('lesion_mask_path', ''))
        self.brain_type.set(app_data.get('brain_type', ''))
        self.subject_id.set(app_data.get('subject_id', ''))
        self.gest_age.set(app_data.get('gest_age', ''))
