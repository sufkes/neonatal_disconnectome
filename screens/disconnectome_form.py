import os
import threading
import customtkinter as ctk
from tkinter import messagebox
from PIL import Image

from constants import THUMBNAILS_DIR, TEMPLATE_DIR, THUMBNAILS
from utils import getRoundedAge, open_in_file_browser
from .loading_overlay import LoadingOverlay

from backend.logging_utils import run_step2_with_logging

class DisconnectomeForm(ctk.CTkFrame):
  def __init__(self, master, go_back_callback=None, app=None):
    super().__init__(master)
    self.go_back_callback = go_back_callback
    self.app = app  # store app reference

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

    header_label = ctk.CTkLabel(header_frame, text="Subject warped to age matched template ", font=ctk.CTkFont(size=20, weight="bold"))
    header_label.grid(row=0, column=0, sticky="w")

    success_label = ctk.CTkLabel(header_frame, text="Success", text_color="green", font=ctk.CTkFont(weight="bold"))
    success_label.grid(row=0, column=1, sticky="w", padx=(10,0))

    # Aside text
    aside_text = (
        "In the previous step, the subject’s brain image and lesion mask were aligned with an age-matched template. "
        "Please inspect the aligned image and lesion mask to ensure that alignment was successful before proceeding "
        "to the next step. To best assess alignment, inspect the images in an external 3D image viewer (e.g. FSLeyes)."
    )
    aside_label = ctk.CTkLabel(self, text=aside_text, wraplength=550, justify="left")
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

    self.back_button = ctk.CTkButton(button_frame, text="Back", command=self.go_back)
    self.back_button.grid(row=0, column=0, sticky="w")

    self.next_button = ctk.CTkButton(button_frame, text="Next", command=self.on_next)
    self.next_button.grid(row=0, column=1, sticky="e")

    # Load placeholder images (replace with actual images as needed)
    self.images = {}
    self.load_placeholder_images()

    # Create content in tabs
    self.create_tab_content()

  def load_placeholder_images(self):
      runs_dir = self.app.app_data.get('runs_folder', '')
      subject = self.app.app_data.get('subject_id', '')
      # Creates simple gray placeholder images; replace by actual PIL.Image.open(filepath) for real images
      for key in ["plot_aligned_image_pair", "lesion_on_original", "lesion_on_age_matched_template_clusters"]:
        outpath = os.path.join(runs_dir, subject, THUMBNAILS, key+".png")
        thumbnail_pil = Image.open(outpath)
        self.images[key] = ctk.CTkImage(light_image=thumbnail_pil, dark_image=thumbnail_pil, size=thumbnail_pil.size)

  def create_tab_content(self):
    brain_image = self.app.app_data.get('brain_image_path', '')
    lesion_mask = self.app.app_data.get('lesion_mask_path', '')
    runs_dir = self.app.app_data.get('runs_folder', '')
    subject = self.app.app_data.get('subject_id', '')
    age = self.app.app_data.get('gest_age', '')
    brain_type = self.app.app_data.get('brain_type', '')
    roundedAge = getRoundedAge(age)

    templateSpacePrefix = os.path.join(runs_dir, subject, "template_space", roundedAge + "W")
    templateSpaceSuffix = f"{roundedAge}-week-template-space-warped.nii.gz"

    # Tab 1
    tab1 = self.tabview.tab("Aligned image pair")
    pathToWarpedSubjectBrainImage = os.path.join(templateSpacePrefix,"brain_img_" + templateSpaceSuffix)
    pathToAgeMatchedDHCPTemplate = os.path.join(TEMPLATE_DIR, "templates", f"week{roundedAge}_{brain_type}.nii.gz")
    command = f"fsleyes {pathToAgeMatchedDHCPTemplate} {pathToWarpedSubjectBrainImage}"
    self.create_preview_section(tab1,
        image_key="plot_aligned_image_pair",
        caption="Subject brain image (top) warped to age-matched template (bottom).",
        copy_command=command
    )

    # Tab 2
    tab2 = self.tabview.tab("Lesion mask on original subject brain image")
    command = f"fsleyes {brain_image} {lesion_mask} -cm blue-lightblue"
    self.create_preview_section(tab2,
        image_key="lesion_on_original",
        caption="Lesion mask (cyan) overlaid on original subject brain image. Each row shows the image centered on each distinct lesion cluster.",
        copy_command=command
    )

    # Tab 3
    tab3 = self.tabview.tab("Lesion mask on age-matched template")
    pathToLegionMaskInAgeMatchedTemplateSpace = os.path.join(templateSpacePrefix, "lesion_mask_" + templateSpaceSuffix)
    command = f"fsleyes {pathToAgeMatchedDHCPTemplate} {pathToLegionMaskInAgeMatchedTemplateSpace} -cm blue-lightblue"
    self.create_preview_section(tab3,
        image_key="lesion_on_age_matched_template_clusters",
        caption="Warped lesion mask (cyan) overlaid on age-matched template. Each row shows the image centered on each distinct lesion cluster.",
        copy_command=command
    )

  def create_preview_section(self, parent, image_key, caption, copy_command):
    # Configure parent's grid for layout
    parent.grid_rowconfigure(1, weight=1)  # Make caption label expand vertically as needed
    parent.grid_columnconfigure(0, weight=1)

    image_label = ctk.CTkLabel(parent, image=self.images[image_key], text="")
    image_label.grid(row=0, column=0, pady=(10,5))

    caption_label = ctk.CTkLabel(parent, text=caption, wraplength=580, justify="center")
    caption_label.grid(row=1, column=0, pady=(0,10), sticky="ew")

    instruction_label = ctk.CTkLabel(parent, text="The following command can be used to open the image above in FSLeyes:")
    instruction_label.grid(row=2, column=0, sticky="w")

    command_frame = ctk.CTkFrame(parent)
    command_frame.grid(row=3, column=0, pady=5, sticky="w")
    # Allow columns to expand so copying button stays right if needed
    command_frame.grid_columnconfigure(0, weight=1)

    # Split command like: "fsleyes path1 path2"
    parts = copy_command.split()
    base_command = parts[0]  # "fsleyes"
    paths = parts[1:]        # ["path1", "path2", ...]

    # Label for the static 'fsleyes ' part
    base_label = ctk.CTkLabel(command_frame, text=base_command + " ")
    base_label.grid(row=0, column=0, sticky="w")

    wrap_px = 350
    # Label for each path, clickable
    for i, path in enumerate(paths):
      clickable_label = ctk.CTkLabel(command_frame, text=path, text_color="#0074d9", cursor="hand2", underline=True, wraplength=wrap_px, justify="left")
      clickable_label.grid(row=0, column=i+1, sticky="w", padx=(5,0))
      clickable_label.bind("<Button-1>", lambda e, p=path: open_in_file_browser(p))

    copy_button = ctk.CTkButton(command_frame, text="Copy", width=60, command=lambda: self.copy_to_clipboard(copy_command))
    copy_button.grid(row=0, column=len(paths) + 1, padx=10, sticky="e")

  def copy_to_clipboard(self, text):
    try:
        # Use CustomTkinter/Tk native clipboard calls
        self.clipboard_clear()
        self.clipboard_append(text)
        self.update()  # Force clipboard update

        # Log success assuming self.app.logger exists and is configured
        if hasattr(self, 'app') and hasattr(self.app, 'logger'):
            self.app.logger.info(f"Copied command to clipboard: {text}")

        # Show info popup
        messagebox.showinfo("Copied", "Command copied to clipboard.")
    except Exception as e:
        # Log error
        if hasattr(self, 'app') and hasattr(self.app, 'logger'):
            self.app.logger.error(f"Failed to copy to clipboard: {e}", exc_info=True)

        # Show warning popup
        messagebox.showwarning("Clipboard error", f"Copying failed: {e}")

  def on_next(self):
    if hasattr(self.app, "show_final_result"):
      self.next_button.configure(state="disabled")
      self.back_button.configure(state="disabled")

      self.loading_overlay.show()

      # Retrieve values
      runs_dir = self.app.app_data.get('runs_folder', '')
      subject = self.app.app_data.get('subject_id', '')
      image_type = self.app.app_data.get('brain_type', '')
      lesion_image = self.app.app_data.get('lesion_mask_path', '')
      age = self.app.app_data.get('gest_age', '')


      self.app.logger.info(f"runs_dir: {runs_dir}\nsubject: {subject}\nimage_type: {image_type}\nlesion_image: {lesion_image}\nage: {age}")

      # Run step2 in a background thread
      def run_step2():
        try:
          from backend.logic import  step2
          success = step2(runs_dir, subject, lesion_image, age, 0, image_type)
          # Schedule UI update on main thread:
          self.after(0, lambda: self.on_step2_complete(success))
        except Exception as e:
          if self.app and self.app.logger:
            self.app.logger.error(f"Exception during step2: {e}", exc_info=True)
          self.after(0, lambda: self.on_step2_complete(False))

      threading.Thread(target=run_step2, daemon=True).start()

  def on_step2_complete(self, success):
    # Hide loading overlay and re-enable button
    self.loading_overlay.hide()
    self.next_button.configure(state="normal")
    self.back_button.configure(state="normal")

    if success:
      # Navigate to next screen
      if self.app:
        self.app.show_final_result()
    else:
      # Error notification; you can customize this popup/dialog
      self.app.logger.error("Step2 failed. Please check logs and try again.")

  def go_back(self):
    if self.go_back_callback:
      self.go_back_callback()
