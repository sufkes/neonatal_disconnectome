import os
import platform
import subprocess
import customtkinter as ctk
from PIL import Image

from constants import THUMBNAILS, TEMPLATE_DIR
from utils import open_in_file_browser

class FinalResult(ctk.CTkFrame):
  def __init__(self, master, go_back_callback=None, app=None):
    super().__init__(master)
    self.go_back_callback = go_back_callback
    self.app = app  # store app reference

    # Configure grid weights for responsiveness
    self.grid_columnconfigure(0, weight=1)

    # Title with success label
    title_frame = ctk.CTkFrame(self)
    title_frame.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="w")
    title_frame.grid_columnconfigure((0,1), weight=0)

    title_label = ctk.CTkLabel(title_frame, text="Generated Disconnectome ", font=ctk.CTkFont(size=20, weight="bold"))
    title_label.grid(row=0, column=0, sticky="w", padx=(0,5))

    success_label = ctk.CTkLabel(title_frame, text="Success", text_color="green", font=ctk.CTkFont(size=18, weight="bold"))
    success_label.grid(row=0, column=1, sticky="w")

    # Figure with image and caption
    self.figure_frame = ctk.CTkFrame(self)
    self.figure_frame.grid(row=1, column=0, padx=20, pady=(0,10), sticky="ew")
    self.figure_frame.grid_columnconfigure(0, weight=1)

    self.image_label = ctk.CTkLabel(self.figure_frame, text="")
    self.image_label.grid(row=0, column=0, sticky="nsew")

    self.caption_label = ctk.CTkLabel(self.figure_frame, text="Image showing Disconnectome map overlaid on the 40w template, and the lesion map warped to the 40w template", wraplength=580, justify="left")
    self.caption_label.grid(row=1, column=0, pady=(5, 0), sticky="w")

    # Explanation paragraph
    info_label = ctk.CTkLabel(self, text="The following command can be used to open the image above in FSLeyes:",
                              wraplength=580, justify="left")
    info_label.grid(row=2, column=0, padx=20, pady=(10, 5), sticky="w")

    # Command container with clickable labels and copy button
    self.command_frame = ctk.CTkFrame(self)
    self.command_frame.grid(row=3, column=0, padx=20, pady=(0, 20), sticky="w")
    self.command_frame.grid_columnconfigure(0, weight=1)

    # Build command similar to DisconnectomeForm logic
    self.command, self.paths = self.build_command()

    # Display the command parts dynamically with clickable paths
    self.display_clickable_command()

    self.set_image()

    # Copy button
    copy_button = ctk.CTkButton(self.command_frame, text="Copy", width=80, command=self.copy_command_to_clipboard)
    copy_button.grid(row=0, column=len(self.paths)+1, padx=10, sticky="e")

  def build_command(self):
    # Adapted from your DisconnectomeForm command construction
    runs_dir = self.app.app_data.get('runs_folder', '')
    subject = self.app.app_data.get('subject_id', '')
    brain_type = self.app.app_data.get('brain_type', '')


    pathTo40WeekTemplateImage = os.path.join(TEMPLATE_DIR, "templates", f"week40_{brain_type}.nii.gz")
    pathToDisconnectomeMap = os.path.join(runs_dir, subject, "disconnectome", "disconnectome-threshold_0.nii.gz")
    pathToLegionMaskIn40WeekTemplateSpace = os.path.join(runs_dir, subject, "disconnectome","lesion_mask_40-week-template-space-warped.nii.gz")

    paths = [pathTo40WeekTemplateImage, pathToDisconnectomeMap, pathToLegionMaskIn40WeekTemplateSpace]
    command = f"fsleyes {pathTo40WeekTemplateImage} {pathToDisconnectomeMap} -cm red-yellow {pathToLegionMaskIn40WeekTemplateSpace} -cm blue-lightblue"

    return command, paths

  def display_clickable_command(self):
      # Clear old widgets if any
      for widget in self.command_frame.winfo_children():
          if isinstance(widget, ctk.CTkLabel):
              widget.destroy()

      # Static 'fsleyes ' label
      base_label = ctk.CTkLabel(self.command_frame, text="fsleyes ")
      base_label.grid(row=0, column=0, sticky="w")


      # Create clickable labels for each path
      for i, path in enumerate(self.paths):
          clickable = ctk.CTkLabel(self.command_frame, text=path, text_color="#0074d9", cursor="hand2",
                                    underline=True, wraplength=350, justify="left")
          clickable.grid(row=0, column=i+1, sticky="w", padx=(5 if i>0 else 0, 0))
          clickable.bind("<Button-1>", lambda e, p=path: open_in_file_browser(p))

  def set_image(self):
    # Load your image here and update self.image_label accordingly
    runs_dir = self.app.app_data.get('runs_folder', '')
    subject = self.app.app_data.get('subject_id', '')
    try:
      outpath = os.path.join(runs_dir, subject, THUMBNAILS, 'disconnectome_at_lesion_centroids_0.png')
      thumbnail_pil = Image.open(outpath)
      photo_img = ctk.CTkImage(light_image=thumbnail_pil, dark_image=thumbnail_pil, size=thumbnail_pil.size)
      self.image_label.configure(image=photo_img, text="")
      self.image_label.image = photo_img
    except Exception as e:
      self.app.logger.error(f"Failed to load image: {e}")

  def copy_command_to_clipboard(self):
      self.clipboard_clear()
      self.clipboard_append(self.command)
