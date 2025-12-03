"""
Warped Lesion Form - For processing pre-warped lesion masks

This screen is shown when the user indicates their lesion mask is already
warped to a dHCP template. It only requires lesion mask, subject ID, and
gestational age.
"""

import customtkinter as ctk
from tkinter import filedialog
import threading

from .loading_overlay import LoadingOverlay


class WarpedLesionForm(ctk.CTkFrame):
    def __init__(self, master, go_back_callback=None, app=None):
        super().__init__(master)
        self.go_back_callback = go_back_callback
        self.app = app
        self.state_manager = app.state_manager if app else None

        self.grid_columnconfigure(0, weight=1)

        self.loading_overlay = LoadingOverlay(master=self)

        row_index = 0

        # Main form frame
        self.form_frame = ctk.CTkFrame(self, corner_radius=0)
        self.form_frame.grid(row=row_index, column=0, sticky="ew", padx=10, pady=10)
        self.form_frame.grid_columnconfigure(0, weight=1)

        row_index += 1

        # Header with info message
        self.header_label = ctk.CTkLabel(
            self.form_frame,
            text="Pre-Warped Lesion Processing",
            font=ctk.CTkFont(size=20, weight="bold"),
            padx=10,
            pady=10,
        )
        self.header_label.grid(
            row=row_index, column=0, sticky="w", padx=20, pady=(10, 5)
        )
        row_index += 1

        info_text = (
            "You indicated that your lesion mask is already warped to a dHCP template. "
            "Please provide the warped lesion mask and subject information below."
        )
        self.info_label = ctk.CTkLabel(
            self.form_frame,
            text=info_text,
            wraplength=580,
            justify="left",
            font=ctk.CTkFont(size=12),
        )
        self.info_label.grid(
            row=row_index, column=0, columnspan=2, sticky="w", padx=20, pady=(0, 20)
        )
        row_index += 1

        # Lesion Mask Section
        self.lesion_section_label = ctk.CTkLabel(
            self.form_frame,
            text="Lesion Data",
            font=ctk.CTkFont(size=16, weight="bold"),
        )
        self.lesion_section_label.grid(
            row=row_index, column=0, sticky="w", padx=20, pady=(10, 10)
        )
        row_index += 1

        # Lesion Mask Path
        self.lesion_mask_path = ctk.StringVar()
        self.lesion_mask_error = ctk.StringVar()

        self.lesion_label = ctk.CTkLabel(
            self.form_frame,
            text="Warped lesion mask in NIFTI format (.nii or .nii.gz):",
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

        # Template Age Info
        self.template_age_label = ctk.CTkLabel(
            self.form_frame,
            text="Age of dHCP template image to which lesion mask is warped, in weeks:",
        )
        self.template_age_label.grid(
            row=row_index, column=0, sticky="w", padx=20, pady=(10, 5)
        )
        row_index += 1

        self.template_age = ctk.StringVar()
        self.template_age_error = ctk.StringVar()

        self.template_age_entry = ctk.CTkEntry(
            self.form_frame,
            textvariable=self.template_age,
            placeholder_text="e.g., 32, 36, 40",
        )
        self.template_age_entry.grid(
            row=row_index, column=0, columnspan=2, sticky="ew", padx=20
        )
        row_index += 1

        self.template_age_error_label = ctk.CTkLabel(
            self.form_frame, textvariable=self.template_age_error, text_color="orange"
        )
        self.template_age_error_label.grid(
            row=row_index, column=0, columnspan=2, sticky="w", padx=20, pady=(5, 10)
        )
        row_index += 1

        # Brain Type
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

        # Subject Data Section
        self.subject_section_label = ctk.CTkLabel(
            self.form_frame,
            text="Subject Data",
            font=ctk.CTkFont(size=16, weight="bold"),
        )
        self.subject_section_label.grid(
            row=row_index, column=0, sticky="w", padx=20, pady=(15, 10)
        )
        row_index += 1

        # Subject ID
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

        # Additional Info
        self.note_label = ctk.CTkLabel(
            self.form_frame,
            text="Note: Since your lesion is pre-warped, we will skip the initial warping step and proceed directly to disconnectome generation.",
            wraplength=580,
            justify="left",
            font=ctk.CTkFont(size=11, slant="italic"),
            text_color="gray",
        )
        self.note_label.grid(
            row=row_index, column=0, columnspan=2, sticky="w", padx=20, pady=(20, 10)
        )
        row_index += 1

        # Buttons
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

        # Load existing state if available
        self._load_from_state()

    def _load_from_state(self):
        """Load form values from state manager"""
        if not self.state_manager:
            return

        processing = self.state_manager.get_processing()

        # Load values into form
        self.lesion_mask_path.set(processing.lesion_mask_path)
        self.brain_type.set(processing.brain_type)
        self.subject_id.set(processing.subject_id)
        self.template_age.set(processing.template_age)

    def browse_lesion_mask(self):
        """Browse for lesion mask file"""
        path = filedialog.askopenfilename(
            filetypes=[("NIFTI files", "*.nii"), ("NIFTI files", "*.nii.gz")]
        )

        if path:
            self.lesion_mask_path.set(path)
            self.lesion_mask_error.set("")

            # Update state manager
            if self.state_manager:
                self.state_manager.update_processing(lesion_mask_path=path)

    def validate_form(self) -> tuple[bool, dict[str, str]]:
        """
        Validate form inputs

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
                if "lesion mask" in error.lower():
                    error_dict["lesion_mask"] = error
                elif (
                    "brain type" in error.lower() or "brain image type" in error.lower()
                ):
                    error_dict["brain_type"] = error
                elif "subject id" in error.lower():
                    error_dict["subject_id"] = error
                elif "template age" in error.lower():
                    error_dict["template_age"] = error

            # Update UI with errors
            self.lesion_mask_error.set(error_dict.get("lesion_mask", ""))
            self.template_age_error.set(error_dict.get("template_age", ""))
            self.subject_id_error.set(error_dict.get("subject_id", ""))
            self.brain_type_error.set(error_dict.get("brain_type", ""))

            return is_valid, errors

        # Fallback to basic validation if no state manager
        return True, {}

    def _save_to_state(self):
        """Save current form values to state manager"""
        if not self.state_manager:
            return

        self.state_manager.update_processing(
            lesion_mask_path=self.lesion_mask_path.get(),
            subject_id=self.subject_id.get(),
            template_age=self.template_age.get(),
            lesion_already_warped=True,  # Mark that lesion is already warped
            brain_type=self.brain_type.get(),
        )

    def on_next(self):
        """Handle next button click"""
        is_valid, errors = self.validate_form()

        if not is_valid:
            if self.app:
                self.app.logger.warning(f"Form validation failed: {errors}")
            return

        # Proceed to processing
        if self.app:
            self.next_button.configure(state="disabled")
            self.back_button.configure(state="disabled")
            # Show loading with descriptive status
            self.loading_overlay.show(
                status="Generating Disconnectome",
                detail="This may take several minutes...",
            )

            processing = self.state_manager.get_processing()

            # Get values from form
            lesion_path = self.lesion_mask_path.get()
            subject_id = self.subject_id.get()
            template_age = self.template_age.get()
            image_type = processing.brain_type

            # Get runs folder from config
            config = self.state_manager.get_config()
            runs_dir = config.runs_folder

            if self.app:
                self.app.logger.info(
                    f"Starting Warped Lesion Processing:\n"
                    f"  runs_dir: {runs_dir}\n"
                    f"  subject: {subject_id}\n"
                    f"  image_type: {image_type}\n"
                    f"  lesion_mask: {lesion_path}\n"
                    f"  template_age: {template_age}\n"
                )

            # Run processing in background thread
            def run_warped_processing():
                try:
                    from backend.logic import process_warped_lesion_from_state

                    success = process_warped_lesion_from_state(
                        processing, config, self.state_manager
                    )

                    self.after(0, lambda: self.on_processing_complete(success))
                except Exception as e:
                    if self.app:
                        self.app.logger.error(
                            f"Warped lesion processing failed: {e}", exc_info=True
                        )
                    self.after(0, lambda: self.on_processing_complete(False))

            threading.Thread(target=run_warped_processing, daemon=True).start()
            # start polling for state changes
            self.app.poll_processing_state()
            # Also poll loading overlay updates
            self.poll_loading_updates()

    def poll_loading_updates(self):
        """Update loading overlay with processing details"""
        processing = self.state_manager.get_processing()

        if processing.current_step == "step2_running":
            self.loading_overlay.update_status(
                detail=processing.current_step_details or "Processing...",
                progress=processing.step2_progress,
            )
            # Continue polling
            self.after(500, self.poll_loading_updates)
        elif processing.current_step in ["step2_complete", "step2_failed"]:
            # Final update
            if processing.current_step == "step2_complete":
                self.loading_overlay.update_status(
                    status="Complete!", detail="", progress=1.0
                )

    def on_processing_complete(self, success):
        """Handle completion of processing"""
        self.loading_overlay.hide()
        self.next_button.configure(state="normal")
        self.back_button.configure(state="normal")

        if success:
            # Update state to mark processing as completed
            if self.state_manager:
                self.state_manager.update_processing(
                    step1_completed=True,  # Skip step 1 since lesion is warped
                    step2_completed=True,  # Processing complete
                )

            # Navigate to final results
            if self.app and hasattr(self.app, "show_final_result"):
                self.app.show_final_result()
        else:
            if self.app:
                self.app.logger.error(
                    "Warped lesion processing failed. Please check logs."
                )

    def go_back(self):
        """Handle back button click"""
        self._save_to_state()
        if self.go_back_callback:
            self.go_back_callback()

    def update_theme(self):
        """Update theme for all widgets"""
        theme = ctk.ThemeManager.theme

        self.configure(fg_color=theme["CTkFrame"]["fg_color"])
        self.form_frame.configure(fg_color=theme["CTkFrame"]["fg_color"])

        # Update labels
        label_fg = theme["CTkLabel"]["text_color"]
        for lbl in [
            self.header_label,
            self.info_label,
            self.lesion_section_label,
            self.lesion_label,
            self.template_age_label,
            self.subject_section_label,
            self.subject_id_label,
            self.note_label,
        ]:
            if lbl.winfo_exists():
                lbl.configure(text_color=label_fg)

        # Update entries
        entry_theme = theme["CTkEntry"]
        for entry in [
            self.lesion_mask_entry,
            self.template_age_entry,
            self.subject_id_entry,
        ]:
            entry.configure(
                fg_color=entry_theme["fg_color"],
                text_color=entry_theme["text_color"],
                border_color=entry_theme["border_color"],
            )

        # Update buttons
        button_theme = theme["CTkButton"]
        for btn in [self.back_button, self.next_button, self.lesion_browse_button]:
            if btn.winfo_exists():
                btn.configure(
                    fg_color=button_theme["fg_color"],
                    hover_color=button_theme["hover_color"],
                    text_color=button_theme["text_color"],
                )
