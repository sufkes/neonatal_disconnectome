import os
import customtkinter as ctk
from PIL import Image

from lib.constants import THUMBNAIL_DISCONNECTOME, THUMBNAILS, TEMPLATE_DIR
from lib.gui_utils import create_command_display, update_widgets_theme

from lib.theme_manager import ThemeableFrame
from lib.utils import _quote_path


class FinalResult(ThemeableFrame):
    def __init__(self, master, go_back_callback=None, app=None):
        # Initialize with theme manager
        super().__init__(master, theme_manager=app.theme_manager if app else None)
        self.go_back_callback = go_back_callback
        self.app = app  # store app reference
        self.state_manager = app.state_manager if app else None

        # Configure grid weights for responsiveness
        self.grid_columnconfigure(0, weight=1)

        # Title with success label
        title_frame = ctk.CTkFrame(self)
        title_frame.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        title_frame.grid_columnconfigure(0, weight=1)
        title_frame.grid_columnconfigure(1, weight=0)

        title_label = ctk.CTkLabel(
            title_frame,
            text="Generated Disconnectome ",
            font=ctk.CTkFont(size=20, weight="bold"),
            padx=10,
            pady=10,
        )
        title_label.grid(row=0, column=0, sticky="w", padx=(10, 5), pady=5)

        success_label = ctk.CTkLabel(
            title_frame,
            text="Success",
            text_color="green",
            font=ctk.CTkFont(weight="bold"),
            padx=10,
            pady=10,
        )
        success_label.grid(row=0, column=1, sticky="w", padx=(5, 10), pady=5)

        # Figure with image and caption
        figure_frame = ctk.CTkFrame(self)
        figure_frame.grid(row=1, column=0, padx=20, pady=(0, 10), sticky="ew")
        figure_frame.grid_columnconfigure(0, weight=1)

        self.image_label = ctk.CTkLabel(figure_frame, text="Loading image...")
        self.image_label.grid(row=0, column=0, sticky="nsew")

        caption_label = ctk.CTkLabel(
            figure_frame,
            text="Image showing Disconnectome map overlaid on the 40w template, and the lesion map warped to the 40w template",
            wraplength=500,
            justify="center",
            font=ctk.CTkFont(size=12),
        )
        caption_label.grid(row=1, column=0, pady=(0, 10), sticky="ew", padx=10)

        # Load existing state if available
        self._load_from_state()

    def _load_from_state(self):
        """Load values from state manager"""
        if not self.state_manager:
            if self.app:
                self.app.logger.error("No state manager available")
            return

        processing = self.state_manager.get_processing()
        config = self.state_manager.get_config()

        if self.app:
            self.app.logger.debug(
                f"Loading result screen - subject: {processing.subject_id}, "
                f"runs_folder: {config.runs_folder}"
            )

        # Load thumbnails and build command if we have required data
        if processing.subject_id and config.runs_folder:
            try:
                # Build command similar to DisconnectomeForm logic
                command = self.build_command()
                # Display the command parts dynamically with clickable paths
                create_command_display(self, command, row_start=2)
                # Display the disconnectome image
                self.set_image()
            except Exception as e:
                if self.app:
                    self.app.logger.error(
                        f"Error loading result screen data: {e}", exc_info=True
                    )
                self.image_label.configure(text="Error loading results")
        else:
            if self.app:
                self.app.logger.warning(
                    "Missing required data - "
                    f"subject_id: {processing.subject_id}, "
                    f"runs_folder: {config.runs_folder}"
                )
            self.image_label.configure(text="Missing required data")

    def build_command(self):
        config = self.state_manager.get_config()
        processing = self.state_manager.get_processing()
        runs_folder = config.runs_folder
        subject = processing.subject_id
        # Default to T2w if brain_type not set (e.g., in warped lesion workflow)
        brain_type = processing.brain_type if processing.brain_type else "T2w"

        if self.app:
            self.app.logger.debug(
                f"Building command - brain_type: {brain_type}, subject: {subject}"
            )

        pathTo40WeekTemplateImage = os.path.join(
            TEMPLATE_DIR, "templates", f"week40_{brain_type}.nii.gz"
        )
        pathToDisconnectomeMap = os.path.join(
            runs_folder, subject, "disconnectome", "disconnectome-threshold_0.nii.gz"
        )
        pathToLegionMaskIn40WeekTemplateSpace = os.path.join(
            runs_folder,
            subject,
            "disconnectome",
            "lesion_mask_40-week-template-space-warped.nii.gz",
        )

        command = f"fsleyes {_quote_path(pathTo40WeekTemplateImage)} {_quote_path(pathToDisconnectomeMap)} -cm red-yellow {_quote_path(pathToLegionMaskIn40WeekTemplateSpace)} -cm blue-lightblue"

        return command

    def set_image(self):
        """Load and display the disconnectome thumbnail"""
        config = self.state_manager.get_config()
        processing = self.state_manager.get_processing()
        runs_folder = config.runs_folder
        subject = processing.subject_id

        outpath = os.path.join(
            runs_folder,
            subject,
            THUMBNAILS,
            THUMBNAIL_DISCONNECTOME,
        )

        if self.app:
            self.app.logger.debug(f"Looking for thumbnail at: {outpath}")

        if not os.path.exists(outpath):
            if self.app:
                self.app.logger.error(f"Thumbnail file not found at: {outpath}")
            self.image_label.configure(
                text=f"Image not found\nExpected location:\n{outpath}"
            )
            return

        try:
            thumbnail_pil = Image.open(outpath)
            photo_img = ctk.CTkImage(
                light_image=thumbnail_pil,
                dark_image=thumbnail_pil,
                size=thumbnail_pil.size,
            )
            self.image_label.configure(image=photo_img, text="")
            self.image_label.image = photo_img
            if self.app:
                self.app.logger.info(f"Successfully loaded thumbnail from: {outpath}")
        except Exception as e:
            if self.app:
                self.app.logger.error(f"Failed to load thumbnail: {e}", exc_info=True)
            self.image_label.configure(text=f"Error loading image:\n{str(e)}")

    def update_theme(self):
        """Update theme for all widgets in this form"""
        super().update_theme()  # Update frame colors

        update_widgets_theme(self, None)
