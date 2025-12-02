import os
from pathlib import Path
import customtkinter as ctk
from tkinter import messagebox
from PIL import Image

from lib.constants import THUMBNAIL_DISCONNECTOME, THUMBNAILS, TEMPLATE_DIR
from lib.utils import open_in_file_browser


class FinalResult(ctk.CTkFrame):
    def __init__(self, master, go_back_callback=None, app=None):
        super().__init__(master)
        self.go_back_callback = go_back_callback
        self.app = app  # store app reference
        self.state_manager = app.state_manager if app else None

        # Configure grid weights for responsiveness
        self.grid_columnconfigure(0, weight=1)

        # Title with success label
        title_frame = ctk.CTkFrame(self)
        title_frame.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="w")
        title_frame.grid_columnconfigure((0, 1), weight=0)

        title_label = ctk.CTkLabel(
            title_frame,
            text="Generated Disconnectome ",
            font=ctk.CTkFont(size=20, weight="bold"),
        )
        title_label.grid(row=0, column=0, sticky="w", padx=(0, 5))

        success_label = ctk.CTkLabel(
            title_frame,
            text="Success",
            text_color="green",
            font=ctk.CTkFont(size=18, weight="bold"),
        )
        success_label.grid(row=0, column=1, sticky="w")

        # Figure with image and caption
        self.figure_frame = ctk.CTkFrame(self)
        self.figure_frame.grid(row=1, column=0, padx=20, pady=(0, 10), sticky="ew")
        self.figure_frame.grid_columnconfigure(0, weight=1)

        self.image_label = ctk.CTkLabel(self.figure_frame, text="Loading image...")
        self.image_label.grid(row=0, column=0, sticky="nsew")

        self.caption_label = ctk.CTkLabel(
            self.figure_frame,
            text="Image showing Disconnectome map overlaid on the 40w template, and the lesion map warped to the 40w template",
            wraplength=580,
            justify="center",
        )
        self.caption_label.grid(row=1, column=0, pady=(5, 0), sticky="w")

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
                self.display_clickable_command(command)
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

        command = f"fsleyes {pathTo40WeekTemplateImage} {pathToDisconnectomeMap} -cm red-yellow {pathToLegionMaskIn40WeekTemplateSpace} -cm blue-lightblue"

        return command

    def display_clickable_command(self, copy_command):
        # Remove any existing command display widgets
        for widget in self.winfo_children():
            if isinstance(widget, ctk.CTkLabel) and widget != self.caption_label:
                if "command" in str(widget).lower():
                    widget.destroy()
            elif isinstance(widget, ctk.CTkFrame):
                # Check if this is a command frame (not figure_frame or title_frame)
                if widget != self.figure_frame and widget != self.winfo_children()[0]:
                    widget.destroy()

        instruction_label = ctk.CTkLabel(
            self,
            text="The following command can be used to open the image above in FSLeyes:",
        )
        instruction_label.grid(row=2, column=0, padx=20, sticky="w")

        command_container = ctk.CTkFrame(self)
        command_container.grid(row=3, column=0, padx=20, pady=5, sticky="ew")
        command_container.grid_columnconfigure(0, weight=1)
        command_container.grid_rowconfigure(0, weight=0)

        command_frame = ctk.CTkScrollableFrame(
            command_container, orientation="horizontal", height=40
        )
        command_frame.grid(row=0, column=0, sticky="ew")
        command_frame.grid_rowconfigure(0, weight=1)

        # Split command like: "fsleyes path1 path2"
        parts = copy_command.split()
        base_command = parts[0]  # "fsleyes"

        # Label for the static 'fsleyes ' part
        base_label = ctk.CTkLabel(command_frame, text=base_command + " ")
        base_label.grid(row=0, column=0, sticky="w", padx=(10, 5), pady=5)

        # Label for each path, clickable
        for i, part in enumerate(parts[1:]):
            if Path(part).exists():
                clickable_label = ctk.CTkLabel(
                    command_frame,
                    text=part,
                    text_color="#0074d9",
                    cursor="hand2",
                    underline=True,
                    wraplength=0,
                    justify="left",
                )
                clickable_label.grid(
                    row=0, column=i + 1, sticky="w", padx=(5, 0), pady=5
                )
                clickable_label.bind(
                    "<Button-1>", lambda e, p=part: open_in_file_browser(p)
                )
            else:
                # Non-clickable text (probably a flag like -cm)
                normal_label = ctk.CTkLabel(
                    command_frame,
                    text=part,
                    wraplength=0,
                    justify="left",
                )
                normal_label.grid(row=0, column=i + 1, sticky="w", padx=(5, 0), pady=5)

        # Fixed frame for copy button
        copy_button_frame = ctk.CTkFrame(command_container, width=80)
        copy_button_frame.grid(row=0, column=1, sticky="ns")
        copy_button_frame.grid_propagate(False)
        copy_button = ctk.CTkButton(
            copy_button_frame,
            text="Copy",
            width=60,
            command=lambda: self.copy_to_clipboard(copy_command),
        )
        copy_button.grid(row=0, column=0, padx=10, pady=5)

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

    def copy_to_clipboard(self, text):
        try:
            self.clipboard_clear()
            self.clipboard_append(text)
            self.update()

            if hasattr(self, "app") and hasattr(self.app, "logger"):
                self.app.logger.info(f"Copied command to clipboard: {text}")

            messagebox.showinfo("Copied", "Command copied to clipboard.")
        except Exception as e:
            if hasattr(self, "app") and hasattr(self.app, "logger"):
                self.app.logger.error(
                    f"Failed to copy to clipboard: {e}", exc_info=True
                )
            messagebox.showwarning("Clipboard error", f"Copying failed: {e}")
