"""
Updated WarpForm using StateManager instead of dict-based state
"""

import customtkinter as ctk
from tkinter import filedialog
from PIL import Image
import os
import threading

from lib.gui_utils import update_widgets_theme
from lib.makeThumbnails import plotThreeView
from lib.constants import THUMBNAIL_BRAIN_IMAGE, THUMBNAILS_DIR
from .loading_overlay import LoadingOverlay
from lib.theme_manager import ThemeableFrame


class WarpForm(ThemeableFrame):
    def __init__(self, master, go_back_callback=None, app=None):
        # Initialize with theme manager
        super().__init__(master, theme_manager=app.theme_manager if app else None)
        self.go_back_callback = go_back_callback
        self.app = app
        self.state_manager = app.state_manager if app else None

        self.grid_columnconfigure(0, weight=1)

        self.loading_overlay = LoadingOverlay(master=self)

        row_index = 0

        self.form_frame = ctk.CTkFrame(self, corner_radius=0)
        self.form_frame.grid(row=row_index, column=0, sticky="ew", padx=10, pady=10)
        self.form_frame.grid_columnconfigure(0, weight=1)

        row_index += 1

        # Image Data Section
        image_data_label = ctk.CTkLabel(
            self.form_frame,
            text="Image Data",
            font=ctk.CTkFont(size=16, weight="bold"),
            padx=10,
            pady=10,
        )
        image_data_label.grid(
            row=row_index, column=0, sticky="w", padx=20, pady=(0, 10)
        )
        row_index += 1

        # Brain Image
        self.brain_image_path = ctk.StringVar()
        self.brain_image_error = ctk.StringVar()

        brain_label = ctk.CTkLabel(
            self.form_frame,
            text="Subject brain image in NIFTI format (.nii or .nii.gz):",
        )
        brain_label.grid(row=row_index, column=0, sticky="w", padx=20, pady=(0, 5))
        row_index += 1

        brain_image_entry = ctk.CTkEntry(
            self.form_frame, textvariable=self.brain_image_path, state="readonly"
        )
        brain_image_entry.grid(row=row_index, column=0, sticky="ew", padx=(20, 110))

        brain_browse_button = ctk.CTkButton(
            self.form_frame, text="Browse...", command=self.browse_brain_image
        )
        brain_browse_button.grid(row=row_index, column=1, sticky="w", padx=(0, 20))
        row_index += 1

        brain_image_error_label = ctk.CTkLabel(
            self.form_frame, textvariable=self.brain_image_error, text_color="red"
        )
        brain_image_error_label.grid(
            row=row_index, column=0, columnspan=2, sticky="w", padx=20, pady=(5, 10)
        )
        row_index += 1

        # Thumbnail
        self.thumbnail_img = None
        self.thumbnail_label = ctk.CTkLabel(self.form_frame, text="")
        self.thumbnail_label.grid(
            row=row_index, column=0, columnspan=2, sticky="ew", padx=20, pady=(10, 20)
        )
        row_index += 3

        caption_text = (
            "Preview of subject brain image in sagittal, coronal, and axial planes"
        )
        self.caption_label = ctk.CTkLabel(
            self.form_frame,
            text=caption_text,
            font=ctk.CTkFont(size=11),
            justify="center",
            anchor="center",
        )
        # Caption will be shown after image is loaded

        # Lesion Mask
        self.lesion_mask_path = ctk.StringVar()
        self.lesion_mask_error = ctk.StringVar()

        lesion_label = ctk.CTkLabel(
            self.form_frame,
            text="Subject brain lesion mask in NIFTI format (.nii or .nii.gz):",
        )
        lesion_label.grid(row=row_index, column=0, sticky="w", padx=20, pady=(0, 5))
        row_index += 1

        lesion_mask_entry = ctk.CTkEntry(
            self.form_frame, textvariable=self.lesion_mask_path, state="readonly"
        )
        lesion_mask_entry.grid(row=row_index, column=0, sticky="ew", padx=(20, 110))

        lesion_browse_button = ctk.CTkButton(
            self.form_frame, text="Browse...", command=self.browse_lesion_mask
        )
        lesion_browse_button.grid(row=row_index, column=1, sticky="w", padx=(0, 20))
        row_index += 1

        lesion_mask_error_label = ctk.CTkLabel(
            self.form_frame, textvariable=self.lesion_mask_error, text_color="red"
        )
        lesion_mask_error_label.grid(
            row=row_index, column=0, columnspan=2, sticky="w", padx=20, pady=(5, 10)
        )
        row_index += 1

        # Brain Type
        self.brain_type = ctk.StringVar()
        self.brain_type_error = ctk.StringVar()

        type_label = ctk.CTkLabel(self.form_frame, text="Type of brain image:")
        type_label.grid(
            row=row_index, column=0, columnspan=2, sticky="w", padx=20, pady=(10, 0)
        )
        row_index += 1

        t1_radio_button = ctk.CTkRadioButton(
            self.form_frame, text="T1w", variable=self.brain_type, value="T1w"
        )
        t2_radio_button = ctk.CTkRadioButton(
            self.form_frame, text="T2w", variable=self.brain_type, value="T2w"
        )

        t1_radio_button.grid(row=row_index, column=0, padx=30, pady=2, sticky="w")
        row_index += 1
        t2_radio_button.grid(row=row_index, column=0, padx=30, pady=2, sticky="w")
        row_index += 1

        brain_type_error_label = ctk.CTkLabel(
            self.form_frame, textvariable=self.brain_type_error, text_color="red"
        )
        brain_type_error_label.grid(
            row=row_index, column=0, columnspan=2, sticky="w", padx=20
        )
        row_index += 1

        # Subject Data Section
        subject_label = ctk.CTkLabel(
            self.form_frame,
            text="Subject data",
            font=ctk.CTkFont(size=16, weight="bold"),
        )
        subject_label.grid(row=row_index, column=0, sticky="w", padx=20, pady=(15, 10))
        row_index += 1

        # Subject ID
        self.subject_id = ctk.StringVar()
        self.subject_id_error = ctk.StringVar()

        subject_id_label = ctk.CTkLabel(
            self.form_frame,
            text="Subject ID (letters, numbers, underscore, dash only):",
        )
        subject_id_label.grid(row=row_index, column=0, sticky="w", padx=20, pady=(0, 5))
        row_index += 1

        subject_id_entry = ctk.CTkEntry(self.form_frame, textvariable=self.subject_id)
        subject_id_entry.grid(
            row=row_index, column=0, columnspan=2, sticky="ew", padx=20
        )
        row_index += 1

        subject_id_error_label = ctk.CTkLabel(
            self.form_frame, textvariable=self.subject_id_error, text_color="red"
        )
        subject_id_error_label.grid(
            row=row_index, column=0, columnspan=2, sticky="w", padx=20
        )
        row_index += 1

        # Gestational Age
        self.gest_age = ctk.StringVar()
        self.gest_age_error = ctk.StringVar()

        gest_label = ctk.CTkLabel(
            self.form_frame, text="Subject's gestational age at scan time (weeks):"
        )
        gest_label.grid(row=row_index, column=0, sticky="w", padx=20, pady=(10, 5))
        row_index += 1

        gest_entry = ctk.CTkEntry(self.form_frame, textvariable=self.gest_age)
        gest_entry.grid(row=row_index, column=0, columnspan=2, sticky="ew", padx=20)
        row_index += 1

        gest_age_error_label = ctk.CTkLabel(
            self.form_frame, textvariable=self.gest_age_error, text_color="orange"
        )
        gest_age_error_label.grid(
            row=row_index, column=0, columnspan=2, sticky="w", padx=20
        )
        row_index += 1

        # Buttons
        button_frame = ctk.CTkFrame(self.form_frame)
        button_frame.grid(
            row=row_index, column=0, columnspan=2, sticky="ew", padx=20, pady=20
        )
        row_index += 1

        button_frame.grid_columnconfigure(0, weight=1)
        button_frame.grid_columnconfigure(1, weight=1)

        self.back_button = ctk.CTkButton(
            button_frame, text="Back", command=self.go_back
        )
        self.back_button.grid(row=0, column=0, sticky="w")

        self.next_button = ctk.CTkButton(
            button_frame, text="Next", command=self.on_next
        )
        self.next_button.grid(row=0, column=1, sticky="e")

        # Load existing state if available
        self._load_from_state()

    def _load_from_state(self):
        """Load form values from state manager"""
        if not self.state_manager:
            return

        processing = self.state_manager.get_processing()

        # Load values into form
        self.brain_image_path.set(processing.brain_image_path)
        self.lesion_mask_path.set(processing.lesion_mask_path)
        self.brain_type.set(processing.brain_type)
        self.subject_id.set(processing.subject_id)
        self.gest_age.set(processing.gestational_age)

        # Load thumbnail if brain image exists
        if processing.brain_image_path and os.path.exists(processing.brain_image_path):
            self._load_thumbnail_if_exists()

    def _load_thumbnail_if_exists(self):
        """Load thumbnail preview if it exists"""
        outpath = os.path.join(THUMBNAILS_DIR, THUMBNAIL_BRAIN_IMAGE)
        if os.path.exists(outpath):
            try:
                thumbnail_pil = Image.open(outpath)
                self.thumbnail_img = ctk.CTkImage(
                    light_image=thumbnail_pil,
                    dark_image=thumbnail_pil,
                    size=thumbnail_pil.size,
                )
                self.thumbnail_label.configure(image=self.thumbnail_img, text="")

                if not self.caption_label.winfo_ismapped():
                    self.caption_label.grid(row=7, column=0, pady=(2, 15))
                    self.form_frame.grid_columnconfigure(0, weight=1)
            except Exception as e:
                if self.app:
                    self.app.logger.error(f"Failed to load thumbnail: {e}")

    def browse_brain_image(self):
        """Browse for brain image file"""
        path = filedialog.askopenfilename(
            # filetypes=[("NIFTI files", "*.nii"), ("NIFTI files", "*.nii.gz")]
        )

        if path:
            self.brain_image_path.set(path)
            self.brain_image_error.set("")

            # Update state manager
            if self.state_manager:
                self.state_manager.update_processing(brain_image_path=path)

            # Generate thumbnail asynchronously
            def generate_thumbnail():
                try:
                    outpath = os.path.join(THUMBNAILS_DIR, THUMBNAIL_BRAIN_IMAGE)
                    plotThreeView(path, outpath)
                    self.after(0, self._load_thumbnail_if_exists)
                except Exception as e:
                    if self.app:
                        self.app.logger.error(f"Thumbnail generation failed: {e}")

            threading.Thread(target=generate_thumbnail, daemon=True).start()

    def browse_lesion_mask(self):
        """Browse for lesion mask file"""
        path = filedialog.askopenfilename(
            # filetypes=[("NIFTI files", "*.nii"), ("NIFTI files", "*.nii.gz")]
        )

        if path:
            self.lesion_mask_path.set(path)
            self.lesion_mask_error.set("")

            # Update state manager
            if self.state_manager:
                self.state_manager.update_processing(lesion_mask_path=path)

    def validate_form(self) -> tuple[bool, dict[str, str]]:
        """
        Validate form inputs using state manager validation

        Returns:
            Tuple of (is_valid, error_dict)
        """
        # First, save current form values to state
        self._save_to_state()

        # Use state manager validation
        if self.state_manager:
            is_valid, errors = self.state_manager.validate_processing_state()

            # Map errors to form fields
            error_dict = {}
            for error in errors:
                if "brain image" in error.lower():
                    error_dict["brain_image"] = error
                elif "lesion mask" in error.lower():
                    error_dict["lesion_mask"] = error
                elif (
                    "brain type" in error.lower() or "brain image type" in error.lower()
                ):
                    error_dict["brain_type"] = error
                elif "subject id" in error.lower():
                    error_dict["subject_id"] = error
                elif "gestational age" in error.lower():
                    error_dict["gest_age"] = error

            # Update UI with errors
            self.brain_image_error.set(error_dict.get("brain_image", ""))
            self.lesion_mask_error.set(error_dict.get("lesion_mask", ""))
            self.brain_type_error.set(error_dict.get("brain_type", ""))
            self.subject_id_error.set(error_dict.get("subject_id", ""))
            self.gest_age_error.set(error_dict.get("gest_age", ""))

            return is_valid, error_dict

        # Fallback to basic validation if no state manager
        return True, {}

    def _save_to_state(self):
        """Save current form values to state manager"""
        if not self.state_manager:
            return

        self.state_manager.update_processing(
            brain_image_path=self.brain_image_path.get(),
            lesion_mask_path=self.lesion_mask_path.get(),
            brain_type=self.brain_type.get(),
            subject_id=self.subject_id.get(),
            gestational_age=self.gest_age.get(),
        )

    def on_next(self):
        """Handle next button click"""
        is_valid, errors = self.validate_form()

        if not is_valid:
            if self.app:
                self.app.logger.warning(f"Form validation failed: {errors}")
            return

        # Proceed to next step
        if hasattr(self.app, "show_disconnectome_form"):
            self.next_button.configure(state="disabled")
            self.back_button.configure(state="disabled")

            # Show loading with descriptive status
            self.loading_overlay.show(
                status="Warping to Age-Matched Template",
                detail="This may take several minutes...",
            )

            # Get values from state manager
            processing = self.state_manager.get_processing()
            config = self.state_manager.get_config()

            runs_dir = config.runs_folder
            subject = processing.subject_id
            image_type = processing.brain_type
            moving_image = processing.brain_image_path
            lesion_image = processing.lesion_mask_path
            age = processing.gestational_age

            if self.app:
                self.app.logger.info(
                    f"Starting Step 1:\n"
                    f"  runs_dir: {runs_dir}\n"
                    f"  subject: {subject}\n"
                    f"  image_type: {image_type}\n"
                    f"  moving_image: {moving_image}\n"
                    f"  lesion_image: {lesion_image}\n"
                    f"  age: {age}"
                )

            # Run step1 in background thread
            def run_step1():
                try:
                    # Option 1: Use state-based function directly
                    from backend.logic import step1_from_state

                    success = step1_from_state(processing, config, self.state_manager)

                    self.after(0, lambda: self.on_step1_complete(success))
                except Exception as e:
                    if self.app:
                        self.app.logger.error(f"Step1 failed: {e}", exc_info=True)
                    self.after(0, lambda: self.on_step1_complete(False))

            threading.Thread(target=run_step1, daemon=True).start()
            # start polling for state changes
            self.app.poll_processing_state()
            # Also poll loading overlay updates
            self.poll_loading_updates()

    def poll_loading_updates(self):
        """Update loading overlay with processing details"""
        processing = self.state_manager.get_processing()

        if processing.current_step == "step1_running":
            self.loading_overlay.update_status(
                detail=processing.current_step_details or "Processing...",
                progress=processing.step1_progress,
            )
            # Continue polling
            self.after(500, self.poll_loading_updates)
        elif processing.current_step in ["step1_complete", "step1_failed"]:
            # Final update
            if processing.current_step == "step1_complete":
                self.loading_overlay.update_status(
                    status="Complete!", detail="", progress=1.0
                )

    def on_step1_complete(self, success):
        """Handle completion of step1"""
        self.loading_overlay.hide()
        self.next_button.configure(state="normal")
        self.back_button.configure(state="normal")

        if success:
            # Update state to mark step1 as completed
            if self.state_manager:
                self.state_manager.update_processing(step1_completed=True)

            # Navigate to next screen
            if self.app:
                self.app.show_disconnectome_form()
        else:
            if self.app:
                self.app.logger.error("Step1 failed. Please check logs and try again.")

    def go_back(self):
        """Handle back button click"""
        self._save_to_state()
        if self.go_back_callback:
            self.go_back_callback()

    # DEPRECATED: Keep for backward compatibility
    def save_data(self, app_data):
        """DEPRECATED: Use state_manager instead"""
        self._save_to_state()

    def load_data(self, app_data):
        """DEPRECATED: Use state_manager instead"""
        self._load_from_state()

    def update_theme(self):
        """Update theme for all widgets in this form"""
        super().update_theme()  # Update frame colors

        update_widgets_theme(self, None)

        # Update loading overlay
        if hasattr(self, "loading_overlay"):
            self.loading_overlay.update_theme()
