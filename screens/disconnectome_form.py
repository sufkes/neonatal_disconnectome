import os
import customtkinter as ctk
from PIL import Image

from lib.constants import TEMPLATE_DIR, THUMBNAILS
from lib.gui_utils import update_widgets_theme
from lib.threading_utils import TaskResult, TaskStatus
from lib.utils import getRoundedAge
from lib.theme_manager import ThemeableFrame
from .loading_overlay import LoadingOverlay


class DisconnectomeForm(ThemeableFrame):
    def __init__(self, master, go_back_callback=None, app=None):
        # Initialize with theme manager
        super().__init__(master, theme_manager=app.theme_manager if app else None)
        self.go_back_callback = go_back_callback
        self.app = app  # store app reference
        self.state_manager = app.state_manager if app else None

        # Get task manager from app
        self.task_manager = app.task_manager if app else None
        self.gui_executor = app.gui_executor if app else None

        # Configure grid layout for this frame
        self.grid_rowconfigure(2, weight=1)  # Tabview expands vertically
        self.grid_columnconfigure(0, weight=1)  # Make single column expandable

        # Loading overlay
        self.loading_overlay = LoadingOverlay(master=self)

        # Header
        header_frame = ctk.CTkFrame(self)
        header_frame.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        header_frame.grid_columnconfigure(0, weight=1)
        header_frame.grid_columnconfigure(1, weight=0)

        header_label = ctk.CTkLabel(
            header_frame,
            text="Subject warped to age matched template ",
            font=ctk.CTkFont(size=20, weight="bold"),
            padx=10,
            pady=10,
        )
        header_label.grid(row=0, column=0, sticky="w", padx=(10, 5), pady=5)

        success_label = ctk.CTkLabel(
            header_frame,
            text="Success",
            text_color="green",
            font=ctk.CTkFont(weight="bold"),
            padx=10,
            pady=10,
        )
        success_label.grid(row=0, column=1, sticky="w", padx=(5, 10), pady=5)

        # Aside text
        aside_text = (
            "In the previous step, the subject’s brain image and lesion mask were aligned with an age-matched template. "
            "Please inspect the aligned image and lesion mask to ensure that alignment was successful before proceeding "
            "to the next step. To best assess alignment, inspect the images in an external 3D image viewer (e.g. FSLeyes)."
        )
        aside_label = ctk.CTkLabel(
            self, text=aside_text, wraplength=550, justify="left"
        )
        aside_label.grid(row=1, column=0, sticky="ew", pady=(0, 20))

        # Tabview with 3 tabs
        self.tabview = ctk.CTkTabview(self, width=600, height=400)
        self.tabview.grid(row=2, column=0, sticky="nsew")

        self.tabview.add("Aligned image pair")
        self.tabview.add("Lesion mask on original subject brain image")
        self.tabview.add("Lesion mask on age-matched template")

        # Buttons frame
        button_frame = ctk.CTkFrame(self)
        button_frame.grid(row=3, column=0, columnspan=2, sticky="ew", padx=20, pady=20)
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

        self.images = {}

        # Load existing state if available
        self._load_from_state()

    def _load_from_state(self):
        """Load values from state manager"""
        if not self.state_manager:
            return

        processing = self.state_manager.get_processing()
        config = self.state_manager.get_config()

        # Load thumbnails
        if processing.subject_id and config.runs_folder:
            self._load_placeholder_images_if_exists()

        # Load values into tabs
        self._load_tab_content()

    def _load_placeholder_images_if_exists(self):
        config = self.state_manager.get_config()
        processing = self.state_manager.get_processing()
        runs_folder = config.runs_folder
        subject = processing.subject_id
        # Creates simple gray placeholder images; replace by actual PIL.Image.open(filepath) for real images
        for key in [
            "plot_aligned_image_pair",
            "lesion_on_original",
            "lesion_on_age_matched_template_clusters",
        ]:
            outpath = os.path.join(runs_folder, subject, THUMBNAILS, key + ".png")
            if os.path.exists(outpath):
                try:
                    thumbnail_pil = Image.open(outpath)
                    self.images[key] = ctk.CTkImage(
                        light_image=thumbnail_pil,
                        dark_image=thumbnail_pil,
                        size=thumbnail_pil.size,
                    )
                except Exception as e:
                    if self.app:
                        self.app.logger.error(f"Failed to load thumbnail: {e}")

    def _load_tab_content(self):
        processing = self.state_manager.get_processing()
        config = self.state_manager.get_config()
        brain_image = processing.brain_image_path
        lesion_mask = processing.lesion_mask_path
        runs_folder = config.runs_folder
        subject = processing.subject_id
        age = processing.gestational_age
        brain_type = processing.brain_type
        roundedAge = getRoundedAge(age)

        templateSpacePrefix = os.path.join(
            runs_folder, subject, "template_space", roundedAge + "W"
        )
        templateSpaceSuffix = f"{roundedAge}-week-template-space-warped.nii.gz"

        # Tab 1
        tab1 = self.tabview.tab("Aligned image pair")
        pathToWarpedSubjectBrainImage = os.path.join(
            templateSpacePrefix, "brain_img_" + templateSpaceSuffix
        )

        pathToAgeMatchedDHCPTemplate = os.path.join(
            TEMPLATE_DIR, "templates", f"week{roundedAge}_{brain_type}.nii.gz"
        )
        command = (
            f"fsleyes {pathToAgeMatchedDHCPTemplate} {pathToWarpedSubjectBrainImage}"
        )
        self.create_preview_section(
            tab1,
            image_key="plot_aligned_image_pair",
            caption="Subject brain image (top) warped to age-matched template (bottom).",
            copy_command=command,
        )

        # Tab 2
        tab2 = self.tabview.tab("Lesion mask on original subject brain image")
        command = f"fsleyes {brain_image} {lesion_mask} -cm blue-lightblue"
        self.create_preview_section(
            tab2,
            image_key="lesion_on_original",
            caption="Lesion mask (cyan) overlaid on original subject brain image. Each row shows the image centered on each distinct lesion cluster.",
            copy_command=command,
        )

        # Tab 3
        tab3 = self.tabview.tab("Lesion mask on age-matched template")
        pathToLegionMaskInAgeMatchedTemplateSpace = os.path.join(
            templateSpacePrefix, "lesion_mask_" + templateSpaceSuffix
        )

        command = f"fsleyes {pathToAgeMatchedDHCPTemplate} {pathToLegionMaskInAgeMatchedTemplateSpace} -cm blue-lightblue"
        self.create_preview_section(
            tab3,
            image_key="lesion_on_age_matched_template_clusters",
            caption="Warped lesion mask (cyan) overlaid on age-matched template. Each row shows the image centered on each distinct lesion cluster.",
            copy_command=command,
        )

    def create_preview_section(self, parent, image_key, caption, copy_command):
        """Create preview section with image, caption, and clean command display"""
        # Configure parent grid
        parent.grid_rowconfigure(2, weight=1)  # Caption can expand
        parent.grid_columnconfigure(0, weight=1)

        current_row = 0

        # Image
        if image_key in self.images:
            image_label = ctk.CTkLabel(parent, image=self.images[image_key], text="")
            image_label.grid(row=current_row, column=0, pady=(10, 5))
            current_row += 1

        # Caption
        caption_label = ctk.CTkLabel(
            parent,
            text=caption,
            wraplength=500,  # Slightly narrower
            justify="center",
            font=ctk.CTkFont(size=12),  # Smaller font
        )
        caption_label.grid(
            row=current_row, column=0, pady=(0, 10), sticky="ew", padx=10
        )
        current_row += 1

        # Command display using utility function
        from lib.gui_utils import create_command_display  # Create this new file

        create_command_display(parent, copy_command, row_start=current_row)

    def on_next(self):
        # Show loading
        self.loading_overlay.show(
            status="Generating Disconnectome", detail="This may take several minutes..."
        )
        self.set_buttons_enabled(False)

        # Get state
        processing = self.state_manager.get_processing()
        config = self.state_manager.get_config()

        # Define worker function
        def worker(cancel_event, progress_callback):
            """Worker function with cancellation and progress support"""

            # Check for cancellation
            if cancel_event.is_set():
                return False

            progress_callback(0.1, "Starting step 2...")

            # Import here to avoid circular imports
            from backend.logic import step2_from_state

            # Run processing
            success = step2_from_state(
                processing,
                config,
                self.state_manager,
                cancel_event=cancel_event,
                progress_callback=progress_callback,
            )

            return success

            # Define completion callback

        def on_complete(result: TaskResult):
            """Completion callback (runs on GUI thread)"""
            self.loading_overlay.hide()
            self.set_buttons_enabled(True)

            if result.status == TaskStatus.COMPLETED and result.result:
                # Update state
                self.state_manager.update_processing(step2_completed=True)

                # Navigate to next screen
                if self.app:
                    self.app.show_final_result()

            elif result.status == TaskStatus.CANCELLED:
                self.app.logger.info("Processing was cancelled by user")

            else:
                # Handle error
                error_msg = result.error_message or "Unknown error"
                self.app.logger.error(f"Step2 failed: {error_msg}")

                # Show error dialog
                from tkinter import messagebox

                messagebox.showerror(
                    "Processing Failed",
                    f"Step 2 failed: {error_msg}\n\nCheck logs for details.",
                    parent=self,
                )

        # Define progress callback
        def on_progress(progress: float, message: str):
            """Progress callback (runs on GUI thread)"""
            self.loading_overlay.update_status(detail=message, progress=progress)

        # Create and start task
        try:
            task = self.task_manager.create_task(
                task_id="step2",
                worker_func=worker,
                on_progress=on_progress,
                on_complete=on_complete,
            )

            self.task_manager.start_task("step2")

        except Exception as e:
            self.loading_overlay.hide()
            self.set_buttons_enabled(True)
            self.app.logger.error(f"Failed to start task: {e}", exc_info=True)

    def set_buttons_enabled(self, enabled: bool):
        """Enable/disable navigation buttons"""
        state = "normal" if enabled else "disabled"
        self.back_button.configure(state=state)
        self.next_button.configure(state=state)

    def go_back(self):
        if self.go_back_callback:
            self.go_back_callback()

    def update_theme(self):
        """Update theme for all widgets in this form"""
        super().update_theme()  # Update frame colors

        update_widgets_theme(self, None)

        # Update loading overlay
        if hasattr(self, "loading_overlay"):
            self.loading_overlay.update_theme()
