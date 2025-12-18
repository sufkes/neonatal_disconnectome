"""
Data Download Dialog

UI for downloading required data files on first launch
"""

import customtkinter as ctk
import threading
from typing import Optional
import logging

from lib.data_downloader import DataDownloader

logger = logging.getLogger("disconnectome")


class DataDownloadDialog(ctk.CTkToplevel):
    """
    Dialog for downloading required data files
    """

    def __init__(self, parent, on_complete: Optional[callable] = None):
        super().__init__(parent)

        self.on_complete = on_complete
        self.downloader = DataDownloader()
        self.download_successful = False
        self.download_thread = None

        # Configure window
        self.title("Download Required Data")
        self.geometry("600x400")
        self.resizable(False, False)

        # Make modal
        self.transient(parent)
        self.grab_set()

        # Center on parent
        self.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() - 600) // 2
        y = parent.winfo_y() + (parent.winfo_height() - 400) // 2
        self.geometry(f"+{x}+{y}")

        self.create_ui()
        self.check_and_show_info()

    def create_ui(self):
        """Create dialog UI"""
        # Main container
        self.main_frame = ctk.CTkFrame(self)
        self.main_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # Title
        self.title_label = ctk.CTkLabel(
            self.main_frame,
            text="Required Data Files",
            font=ctk.CTkFont(size=20, weight="bold"),
        )
        self.title_label.pack(pady=(0, 10))

        # Info text
        self.info_frame = ctk.CTkFrame(self.main_frame)
        self.info_frame.pack(fill="both", expand=True, pady=(0, 20))

        self.info_text = ctk.CTkTextbox(self.info_frame, wrap="word", height=150)
        self.info_text.pack(fill="both", expand=True, padx=10, pady=10)

        # Progress section
        self.progress_frame = ctk.CTkFrame(self.main_frame)
        self.progress_frame.pack(fill="x", pady=(0, 20))

        self.status_label = ctk.CTkLabel(
            self.progress_frame, text="Ready to download", font=ctk.CTkFont(size=12)
        )
        self.status_label.pack(pady=(10, 5))

        self.progress_bar = ctk.CTkProgressBar(self.progress_frame, width=500)
        self.progress_bar.pack(pady=(0, 5))
        self.progress_bar.set(0)

        self.progress_text = ctk.CTkLabel(
            self.progress_frame, text="", font=ctk.CTkFont(size=12)
        )
        self.progress_text.pack(pady=(0, 10))

        # Buttons
        self.button_frame = ctk.CTkFrame(self.main_frame)
        self.button_frame.pack(fill="x")

        self.cancel_button = ctk.CTkButton(
            self.button_frame, text="Cancel", command=self.on_cancel, width=120
        )
        self.cancel_button.pack(side="left", padx=(0, 10))

        self.download_button = ctk.CTkButton(
            self.button_frame, text="Download", command=self.start_download, width=120
        )
        self.download_button.pack(side="right")

        # Choose location button
        self.location_button = ctk.CTkButton(
            self.button_frame,
            text="Choose Location",
            command=self.choose_location,
            width=140,
        )
        self.location_button.pack(side="right", padx=(0, 10))

    def check_and_show_info(self):
        """Check what needs to be downloaded and display info"""
        download_info = self.downloader.get_download_info()

        if download_info["missing_count"] == 0:
            # All data already installed
            self.info_text.insert(
                "1.0",
                "All required data files are already installed!\n\n"
                f"Data location: {self.downloader.data_dir}\n\n"
                "You can proceed with using the application.",
            )
            self.download_button.configure(text="Continue", state="normal")
            self.location_button.configure(state="disabled")
        else:
            # Build info message
            info_msg = (
                "This application requires additional data files to function.\n\n"
                f"Total download size: ~{download_info['total_size_mb']} MB\n\n"
                "The following packages will be downloaded:\n\n"
            )

            for pkg in download_info["packages"]:
                info_msg += f"• {pkg['description']} (~{pkg['size_mb']} MB)\n"

            info_msg += (
                f"\n\nData will be stored in:\n{self.downloader.data_dir}\n\n"
                "You only need to download this data once."
            )

            self.info_text.insert("1.0", info_msg)
            self.info_text.configure(state="disabled")

    def choose_location(self):
        """Let user choose download location"""
        from tkinter import filedialog

        directory = filedialog.askdirectory(
            title="Choose Data Storage Location",
            initialdir=str(self.downloader.data_dir.parent),
        )

        if directory:
            self.downloader = DataDownloader(data_dir=directory)
            self.check_and_show_info()
            logger.info(f"Data location changed to: {directory}")

    def start_download(self):
        """Start downloading data"""
        # Check if already installed
        if self.downloader.is_fully_installed():
            self.download_successful = True
            self.close_dialog()
            return

        # Disable buttons during download
        self.download_button.configure(state="disabled")
        self.location_button.configure(state="disabled")

        # Start download in background thread
        self.download_thread = threading.Thread(
            target=self._download_worker, daemon=True
        )
        self.download_thread.start()

    def _download_worker(self):
        """Background thread worker for downloading"""
        try:
            success = self.downloader.download_all_required(
                progress_callback=self._update_progress
            )

            # Update UI on main thread
            self.after(0, lambda: self._download_complete(success))

        except Exception as e:
            logger.error(f"Download failed: {e}", exc_info=True)
            self.after(0, lambda: self._download_complete(False))

    def _update_progress(self, filename: str, bytes_done: int, bytes_total: int):
        """Update progress bar (called from download thread)"""
        # Calculate progress
        if bytes_total > 0:
            progress = bytes_done / bytes_total
        else:
            progress = 0

        # Update UI on main thread
        def update_ui():
            self.progress_bar.set(progress)
            self.status_label.configure(text=f"Downloading: {filename}")

            # Format sizes
            mb_done = bytes_done / (1024 * 1024)
            mb_total = bytes_total / (1024 * 1024)
            self.progress_text.configure(
                text=f"{mb_done:.1f} MB / {mb_total:.1f} MB ({progress * 100:.1f}%)"
            )

        self.after(0, update_ui)

    def _download_complete(self, success: bool):
        """Handle download completion"""
        if success:
            self.download_successful = True
            self.status_label.configure(text="Download complete!", text_color="green")
            self.progress_bar.set(1.0)
            self.progress_text.configure(text="All files downloaded successfully")

            # Change button to close
            self.download_button.configure(text="Continue", state="normal")
            self.download_button.configure(command=self.close_dialog)

        else:
            self.status_label.configure(text="Download failed", text_color="red")
            self.progress_text.configure(
                text="Please check your internet connection and try again"
            )

            # Re-enable download button
            self.download_button.configure(text="Retry", state="normal")
            self.location_button.configure(state="normal")

    def on_cancel(self):
        """Handle cancel button"""
        if self.download_thread and self.download_thread.is_alive():
            # TODO: Implement cancellation if needed
            logger.warning("Download cancellation not yet implemented")

        self.download_successful = False
        self.close_dialog()

    def close_dialog(self):
        """Close dialog and call completion callback"""
        if self.on_complete:
            self.on_complete(self.download_successful)

        self.grab_release()
        self.destroy()


class DataDownloadPrompt(ctk.CTkToplevel):
    """
    Simple prompt asking if user wants to download data
    """

    def __init__(self, parent, on_response: callable):
        super().__init__(parent)

        self.on_response = on_response
        self.user_choice = None

        # Configure window
        self.title("Data Download Required")
        self.geometry("500x250")
        self.resizable(False, False)

        # Make modal
        self.transient(parent)
        self.grab_set()

        # Center on parent
        self.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() - 500) // 2
        y = parent.winfo_y() + (parent.winfo_height() - 250) // 2
        self.geometry(f"+{x}+{y}")

        self.create_ui()

    def create_ui(self):
        """Create prompt UI"""
        frame = ctk.CTkFrame(self)
        frame.pack(fill="both", expand=True, padx=20, pady=20)

        # Icon/Title
        title = ctk.CTkLabel(
            frame,
            text="⚠️ Data Files Required",
            font=ctk.CTkFont(size=18, weight="bold"),
        )
        title.pack(pady=(0, 15))

        # Message
        message = ctk.CTkLabel(
            frame,
            text=(
                "This application requires additional data files to function.\n\n"
                "These files will be downloaded from a secure server and\n"
                "stored on your computer (~3.6 GB total).\n\n"
                "Would you like to download them now?"
            ),
            justify="center",
        )
        message.pack(pady=(0, 20))

        # Buttons
        button_frame = ctk.CTkFrame(frame)
        button_frame.pack(fill="x")

        cancel_btn = ctk.CTkButton(
            button_frame, text="Exit Application", command=self.on_cancel, width=150
        )
        cancel_btn.pack(side="left", padx=5)

        later_btn = ctk.CTkButton(
            button_frame, text="Download Later", command=self.on_later, width=150
        )
        later_btn.pack(side="left", padx=5)

        download_btn = ctk.CTkButton(
            button_frame, text="Download Now", command=self.on_download, width=150
        )
        download_btn.pack(side="right", padx=5)

    def on_download(self):
        """User chose to download"""
        self.user_choice = "download"
        self.close_prompt()

    def on_later(self):
        """User chose to download later"""
        self.user_choice = "later"
        self.close_prompt()

    def on_cancel(self):
        """User chose to exit"""
        self.user_choice = "exit"
        self.close_prompt()

    def close_prompt(self):
        """Close prompt and call response callback"""
        self.grab_release()
        self.destroy()

        if self.on_response:
            self.on_response(self.user_choice)
