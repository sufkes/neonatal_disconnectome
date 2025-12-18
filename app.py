import logging
import os
import queue
from logging.handlers import QueueHandler, QueueListener, RotatingFileHandler

import sys
import tkinter as tk
import tkinter.font as tkfont

import customtkinter as ctk
from PIL import Image

from lib.gui_utils import update_widgets_theme
from screens.ctk_hyperlink_manager import CTkHyperlinkManager
from screens.disconnectome_form import DisconnectomeForm
from screens.result_screen import FinalResult
from screens.start_screen import StartRunForm
from screens.warp_form import WarpForm
from screens.warped_lesion_form import WarpedLesionForm
from lib.utils import (
    open_in_file_browser,
)

# Import new state management
from lib.state_management import StateManager

from lib.theme_manager import ThemeManager

from lib.data_downloader import DataDownloader
from screens.data_download_dialog import DataDownloadDialog

# Initialize state manager globally
state_manager = StateManager()


class TkinterTextHandler(logging.Handler):
    """Logging handler that directs logs into a Tkinter Textbox (truly thread-safe)."""

    def __init__(self, text_widget, brightness):
        super().__init__()
        self.text_widget = text_widget
        self.text_widget.configure(state="disabled")
        self._update_tags(brightness)

        # Thread-safe queue for log messages
        self._log_queue = []
        self._is_processing = False

    def emit(self, record):
        try:
            msg = self.format(record) + "\n"
            level = record.levelname

            # Add to queue instead of direct after() call
            self._log_queue.append((msg, level))

            # Schedule processing if not already scheduled
            if not self._is_processing:
                self._schedule_process()

        except Exception:
            # Don't call handleError here as it can cause recursion
            pass

    def _schedule_process(self):
        """Schedule log processing on main thread"""
        try:
            if self.text_widget.winfo_exists():
                self._is_processing = True
                self.text_widget.after(100, self._process_queue)
        except:
            self._is_processing = False

    def _process_queue(self):
        """Process queued log messages on main thread"""
        try:
            if not self.text_widget.winfo_exists():
                self._is_processing = False
                return

            # Process all queued messages
            while self._log_queue:
                msg, level = self._log_queue.pop(0)

                self.text_widget.configure(state="normal")
                self.text_widget.insert("end", msg, level)
                self.text_widget.configure(state="disabled")
                self.text_widget.see("end")

            self._is_processing = False

        except Exception:
            self._is_processing = False

    def _update_tags(self, brightness):
        """Update tag colors from current theme."""

        if brightness == 0:  # Light mode
            self.text_widget.tag_config("DEBUG", foreground="#00aaaa")  # Teal/cyan
            self.text_widget.tag_config("INFO", foreground="#333333")  # Dark gray
            self.text_widget.tag_config("WARNING", foreground="#FF9500")  # Orange
            self.text_widget.tag_config("ERROR", foreground="#cc0000")  # Dark red
            self.text_widget.tag_config(
                "CRITICAL", foreground="#ffffff", background="#cc0000"
            )  # White on red
        else:  # Dark mode
            self.text_widget.tag_config("DEBUG", foreground="#66ffff")  # Light cyan
            self.text_widget.tag_config("INFO", foreground="#ffffff")  # White
            self.text_widget.tag_config("WARNING", foreground="#FFB340")  # Light orange
            self.text_widget.tag_config("ERROR", foreground="#ff9999")  # Light red
            self.text_widget.tag_config(
                "CRITICAL", foreground="#000000", background="#ffff00"
            )  # Black on yellow


class DisconnectomeApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Disconnectome")
        self.minsize(640, 480)
        width = int(self.winfo_screenwidth() * 0.9)
        height = int(self.winfo_screenheight() * 0.9)
        x = int((self.winfo_screenwidth() - width) / 2)
        y = int((self.winfo_screenheight() - height) / 2)
        self.geometry(f"{width}x{height}+{x}+{y}")

        # Use global state manager
        self.state_manager = state_manager

        # Subscribe to state changes
        self.state_manager.subscribe(self.on_state_changed)

        # Initialize theme manager FIRST
        self.theme_manager = ThemeManager(themes_folder="themes")

        # Load theme from config
        config = self.state_manager.get_config()
        ctk.set_appearance_mode(config.appearance)

        if not self.theme_manager.load_theme(config.theme):
            # Fallback to first available
            available = self.theme_manager.get_available_themes()
            if available:
                self.theme_manager.load_theme(available[0])

        # Subscribe to theme changes
        self.theme_manager.subscribe(self.on_theme_changed_global)

        # Initialize data downloader
        self.data_downloader = DataDownloader()

        # Configure grid: 3 rows (header, main, footer)
        self.grid_rowconfigure(0, weight=0)  # header fixed height
        self.grid_rowconfigure(1, weight=1)  # main area expands
        self.grid_rowconfigure(2, weight=0)  # footer fixed height
        self.grid_columnconfigure(0, weight=1)  # single column for entire app

        # Create main_container inside row 1
        self.main_container = ctk.CTkFrame(self)
        self.main_container.grid(row=1, column=0, sticky="nsew")
        self.main_container.grid_rowconfigure(0, weight=1)
        self.main_container.grid_columnconfigure(0, weight=4)  # Main content
        self.main_container.grid_columnconfigure(
            1, weight=0, minsize=180
        )  # Smaller side panel (was 200)

        self.create_menu()
        self.create_header()
        self.create_footer()
        self.create_side_panel()

        # --- Main scrollable content area ---
        self.content_frame = ctk.CTkScrollableFrame(
            self.main_container, corner_radius=0
        )
        self.content_frame.grid(row=0, column=0, sticky="nsew")

        # Logger setup
        self._init_logging()

        self.current_screen = None
        self.current_screen_class = None

        # DEPRECATED: Keep for backward compatibility during migration
        self.app_data = {}

        self.logger.info("DisconnectomeApp started")
        self.show_start_form()

        # Check data installation after UI is ready
        self.after(500, self.check_data_installation)

    def on_theme_changed_global(self, theme_name: str):
        """Called when theme changes globally"""
        self.logger.info(f"Global theme changed to: {theme_name}")
        self.refresh_styles()

    def poll_processing_state(self):
        """Poll processing state every 500ms and update side panel"""
        processing = self.state_manager.get_processing()

        # Update side panel with current state
        self.update_side_panel()

        # Continue polling if processing is running
        if processing.current_step in ["step1_running", "step2_running"]:
            self.after(500, self.poll_processing_state)
        elif processing.current_step in [
            "step1_complete",
            "step2_complete",
            "step1_failed",
            "step2_failed",
        ]:
            # Do one final update after completion/failure
            self.update_side_panel()

    def on_state_changed(self, state_type: str):
        """
        Callback when state changes

        Args:
            state_type: "config" or "processing"
        """
        if state_type == "config":
            self.logger.debug("Configuration state changed")
            # Update UI elements based on config changes
        elif state_type == "processing":
            self.logger.debug("Processing state changed")
            # Update side panel or other UI elements
            self.update_side_panel()

    def update_side_panel(self):
        """Update side panel with current processing state"""
        processing = self.state_manager.get_processing()
        config = self.state_manager.get_config()

        # Save current scroll position
        scroll_pos = self.textbox.yview()

        # Clear existing content
        self.textbox.configure(state="normal")
        self.textbox.delete("1.0", "end")

        # Add input data section
        self.textbox.insert("end", "Input Data\n", "header")
        self.textbox.insert("end", "\n")

        input_summary = processing.get_input_summary()
        if input_summary:
            for key, value in input_summary.items():
                if value:
                    self._add_side_panel_item(key, value)
        else:
            self.textbox.insert("end", "  No input data yet\n\n", "info")

        # ===== PROGRESS SECTION =====
        if processing.current_step:
            self.textbox.insert("end", "\nProcessing Status\n", "header")
            self.textbox.insert("end", "\n")

            # Step 1 status
            if processing.step1_completed:
                self.textbox.insert("end", "✓ ", "success")
                self.textbox.insert("end", "Step 1: Warp to Template - Complete\n\n")
            elif processing.current_step == "step1_running":
                self.textbox.insert("end", "⟳ ", "info")
                self.textbox.insert(
                    "end",
                    f"Step 1: Warp to Template - Running - {processing.current_step_details}...\n",
                )
                if processing.step1_progress > 0:
                    progress_pct = int(processing.step1_progress * 100)
                    self.textbox.insert("end", f"  Progress: {progress_pct}%\n\n")
            elif processing.lesion_already_warped:
                self.textbox.insert("end", "⊘ ", "info")
                self.textbox.insert("end", "Step 1: Skipped (pre-warped lesion)\n\n")
            else:
                self.textbox.insert("end", "○ ", "pending")
                self.textbox.insert("end", "Step 1: Warp to Template - Pending\n\n")

            # Step 2 status
            if processing.step2_completed:
                self.textbox.insert("end", "✓ ", "success")
                self.textbox.insert(
                    "end", "Step 2: Generate Disconnectome - Complete\n\n"
                )
            elif processing.current_step == "step2_running":
                self.textbox.insert("end", "⟳ ", "info")
                self.textbox.insert(
                    "end",
                    f"Step 2: Generate Disconnectome - Running - {processing.current_step_details}...\n",
                )
                if processing.step2_progress > 0:
                    progress_pct = int(processing.step2_progress * 100)
                    self.textbox.insert("end", f"  Progress: {progress_pct}%\n\n")
            elif processing.step1_completed:
                self.textbox.insert("end", "○ ", "pending")
                self.textbox.insert("end", "Step 2: Generate Disconnectome - Ready\n\n")
            else:
                self.textbox.insert("end", "○ ", "pending")
                self.textbox.insert(
                    "end", "Step 2: Generate Disconnectome - Pending\n\n"
                )

        # ===== OUTPUT DATA SECTION =====
        output_summary = processing.get_output_summary(config.runs_folder)
        if output_summary:
            self.textbox.insert("end", "\nOutput Data\n", "header")
            self.textbox.insert("end", "\n")

            for key, value in output_summary.items():
                self._add_side_panel_path(key, value)
        elif processing.step1_completed or processing.step2_completed:
            # Show message if steps completed but no outputs found
            self.textbox.insert("end", "\nOutput Data\n", "header")
            self.textbox.insert("end", "\n")
            self.textbox.insert(
                "end", "  Processing complete but output files not found\n", "warning"
            )

        self.textbox.configure(state="disabled")

        # Restore scroll position
        self.textbox.yview_moveto(scroll_pos[0])

    def _add_side_panel_item(self, label: str, value: str):
        """Add a text item to side panel"""
        self.textbox.insert("end", f"{label}: ", "input")
        self.textbox.insert("end", f"{value}\n\n")

    def _add_side_panel_path(self, label: str, path: str):
        """Add a clickable path to side panel"""
        tag = self.hyperlink_manager.add(path)
        self.textbox.insert("end", f"{label}:\n", "output")
        self.textbox.insert("end", f"  {path}\n\n", tag)

    def toggle_sidepanel(self):
        if self.sidepanel.winfo_ismapped():
            self.sidepanel.grid_remove()
            self.main_container.grid_columnconfigure(1, minsize=0, weight=0)
            self.main_container.grid_columnconfigure(0, weight=1)
        else:
            self.sidepanel.grid()
            self.main_container.grid_columnconfigure(1, minsize=200, weight=1)
            self.main_container.grid_columnconfigure(0, weight=4)

    def create_header(self):
        """Create application header with app icon and controls"""
        if hasattr(self, "header"):
            self.header.destroy()

        self.header = ctk.CTkFrame(self, height=60, corner_radius=0)
        self.header.grid(row=0, column=0, sticky="ew")
        self.header.grid_propagate(False)

        # Toggle side panel button
        self.toggle_sidepanel_btn = ctk.CTkButton(
            self.header, text="☰", width=40, command=self.toggle_sidepanel
        )
        self.toggle_sidepanel_btn.pack(side="right", padx=10, pady=10)

        # Logo

        try:
            # PyInstaller-aware path resolution
            if getattr(sys, "frozen", False):
                base_path = sys._MEIPASS
            else:
                from lib.constants import PROJECT_ROOT

                base_path = PROJECT_ROOT

            full_logo_path = os.path.join(base_path, "app_icon.png")
            light_img = Image.open(full_logo_path)
            dark_img = Image.open(full_logo_path)
        except (FileNotFoundError, OSError):
            # create a simple placeholder; e.g., a solid gray square
            light_img = Image.new("RGBA", (40, 40), (200, 200, 200, 255))
            dark_img = light_img  # same placeholder for dark mode

        self.logo_image = ctk.CTkImage(
            light_image=light_img, dark_image=dark_img, size=(40, 40)
        )
        self.logo_label = ctk.CTkLabel(self.header, image=self.logo_image, text="")
        self.logo_label.pack(side="left", padx=15, pady=10)

        # Appearance mode selector
        appearance_options = ["Light", "Dark", "System"]
        current_mode = self.state_manager.get_config().appearance

        self.appearance_menu = ctk.CTkOptionMenu(
            self.header, values=appearance_options, command=self.change_appearance_mode
        )
        self.appearance_menu.set(current_mode)
        self.appearance_menu.pack(side="right", padx=15, pady=10)

        # Theme selector with available themes
        available_themes = self.theme_manager.get_available_themes()

        self.theme_selector = ctk.CTkOptionMenu(
            self.header,
            values=available_themes if available_themes else ["default"],
            command=self.change_theme,
            width=150,
        )

        current_theme = self.theme_manager.current_theme_name
        if current_theme in available_themes:
            self.theme_selector.set(current_theme)
        elif available_themes:
            self.theme_selector.set(available_themes[0])

        self.theme_selector.pack(side="right", padx=10, pady=10)

    def create_footer(self):
        """Create footer with logging console that adapts to theme"""
        if hasattr(self, "footer"):
            self.footer.destroy()

        # Create footer frame
        self.footer = ctk.CTkFrame(self, height=150, corner_radius=0)
        self.footer.grid(row=2, column=0, sticky="nsew", padx=30, pady=(0, 10))
        self.footer.grid_propagate(False)
        self.footer.grid_columnconfigure(0, weight=1)
        self.footer.grid_rowconfigure(0, weight=1)

        # Create log textbox
        self.log_textbox = ctk.CTkTextbox(self.footer)
        self.log_textbox.grid(row=0, column=0, sticky="nsew")

        # Create toggle button
        self.toggle_btn = ctk.CTkButton(
            self.footer,
            text="▼",
            width=25,
            height=25,
            command=self.toggle_log_visibility,
            corner_radius=0,
        )
        self.toggle_btn.grid(row=0, column=1, sticky="ne", padx=5, pady=5)

        # Apply initial theme colors
        self._update_footer_theme()

    def _update_footer_theme(self):
        """Update footer colors based on current theme"""
        theme = ctk.ThemeManager.theme
        appearance_mode = ctk.get_appearance_mode()
        is_dark = appearance_mode == "Dark"

        # Get theme colors
        def get_color(widget_type, property_name, default_light, default_dark):
            try:
                if widget_type in theme and property_name in theme[widget_type]:
                    value = theme[widget_type][property_name]
                    if isinstance(value, (list, tuple)) and len(value) >= 2:
                        return value[1] if is_dark else value[0]
                    return value
            except:
                pass
            return default_dark if is_dark else default_light

        # Footer background - slightly different from main
        footer_bg = "#2F2F2F" if is_dark else "#F5F5F5"

        # Update footer frame
        self.footer.configure(fg_color=footer_bg)

        # Update log textbox with theme colors
        self.log_textbox.configure(
            fg_color=footer_bg,
            border_color=get_color("CTkTextbox", "border_color", "#D1D1D6", "#48484A"),
            text_color=get_color("CTkTextbox", "text_color", "#000000", "#FFFFFF"),
        )

        # Update toggle button
        self.toggle_btn.configure(
            fg_color=get_color("CTkButton", "fg_color", "#007AFF", "#0A84FF"),
            hover_color=get_color("CTkButton", "hover_color", "#0051D5", "#409CFF"),
            text_color=get_color("CTkButton", "text_color", "#FFFFFF", "#FFFFFF"),
        )

        # Update logging handler tag colors
        if hasattr(self, "tkinter_handler"):
            brightness = 1 if is_dark else 0
            self.tkinter_handler._update_tags(brightness)

    def create_side_panel(self):
        """Create compact side panel for displaying input/output information"""
        self.sidepanel = ctk.CTkFrame(self.main_container)
        self.sidepanel.grid(row=0, column=1, sticky="nsew")

        self.textbox = tk.Text(
            self.sidepanel,
            wrap="word",
            font=("Verdana", 12),
            padx=5,
            pady=5,
        )
        self.textbox.grid(row=0, column=0, sticky="nsew", padx=3, pady=3)

        self._configure_sidepanel_tags()

        self.sidepanel.grid_rowconfigure(0, weight=1)
        self.sidepanel.grid_columnconfigure(0, weight=1)

        # Make side panel narrower (was 200, now 180)
        self.sidepanel.configure(width=180)

        # Initialize hyperlink manager
        self.hyperlink_manager = CTkHyperlinkManager(self.textbox, open_in_file_browser)

        # Initial content
        self.textbox.insert("end", "Input Data\n", "header")
        self.textbox.insert("end", "\n")
        self.textbox.configure(state="disabled")

    def _configure_sidepanel_tags(self):
        """Configure text tags for side panel with current theme colors"""

        theme = ctk.ThemeManager.theme

        # Check if we're in dark mode
        appearance_mode = ctk.get_appearance_mode()
        is_dark = appearance_mode == "Dark"

        # Helper function to get theme colors
        def get_color(widget, prop, light_default, dark_default):
            try:
                if widget in theme and prop in theme[widget]:
                    val = theme[widget][prop]
                    if isinstance(val, (list, tuple)) and len(val) >= 2:
                        return val[1] if is_dark else val[0]
                    return val
            except:
                pass
            return dark_default if is_dark else light_default

        # Get colors from theme
        bg = get_color("CTkFrame", "fg_color", "#FFFFFF", "#2B2B2B")
        fg = get_color("CTkLabel", "text_color", "#000000", "#FFFFFF")

        # Configure textbox background and text
        self.textbox.configure(
            bg=bg,
            fg=fg,
            insertbackground=fg,  # Cursor color
            selectbackground=get_color(
                "CTkEntry", "border_color", "#D1D1D6", "#48484A"
            ),
            selectforeground=fg,
        )

        # Configure fonts
        header_font = tkfont.Font(family="Verdana", size=12, weight="bold")
        title_font = tkfont.Font(family="Verdana", size=10, weight="bold")

        # Configure text tags
        self.textbox.tag_configure("header", font=header_font, foreground=fg)
        self.textbox.tag_configure("input", font=title_font, foreground="#1EB44D")
        self.textbox.tag_configure("output", font=title_font, foreground="#1EB44D")
        self.textbox.tag_configure("success", foreground="#34C759")
        self.textbox.tag_configure(
            "info", foreground="#0A84FF" if is_dark else "#007AFF"
        )
        self.textbox.tag_configure("pending", foreground="#8E8E93")
        self.textbox.tag_configure("warning", foreground="#FF9500")

    def show_limited_mode_warning(self):
        """Warn user that app will run in limited mode without data"""
        from tkinter import messagebox

        messagebox.showwarning(
            "Limited Functionality",
            "The application will run in limited mode without data files.\n\n"
            "Some features will be unavailable. You can download data files "
            "later from the Data menu.",
        )

        # You might want to disable certain features
        # For example:
        # self.start_button.configure(state="disabled")
        # self.warp_button.configure(state="disabled") foreground="#FF9500")

    def toggle_log_visibility(self):
        if self.log_textbox.winfo_ismapped():
            self.log_textbox.grid_remove()
            self.toggle_btn.configure(text="▲")
            self.footer.configure(height=35)
        else:
            self.log_textbox.grid()
            self.toggle_btn.configure(text="▼")
            self.footer.configure(height=150)

    def _init_logging(self):
        """Initialize logging system"""
        self.log_queue = queue.Queue(maxsize=1000)
        self.logger = logging.getLogger("disconnectome")
        self.logger.setLevel(logging.DEBUG)
        self.logger.handlers.clear()

        queue_handler = QueueHandler(self.log_queue)
        formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
        queue_handler.setFormatter(formatter)
        self.logger.addHandler(queue_handler)

        rotating_file_handler = RotatingFileHandler(
            "disconnectome.log", maxBytes=5 * 1024 * 1024, backupCount=5
        )
        rotating_file_handler.setFormatter(formatter)

        mode = ctk.get_appearance_mode()
        # Map to brightness index (system resolves to light/dark)
        brightness = 1 if mode == "Dark" else 0  # 0=light, 1=dark

        self.tkinter_handler = TkinterTextHandler(self.log_textbox, brightness)
        self.tkinter_handler.setFormatter(formatter)

        self.queue_listener = QueueListener(
            self.log_queue,
            rotating_file_handler,
            self.tkinter_handler,
            respect_handler_level=True,
        )
        self.queue_listener.start()

    def on_closing(self):
        """Clean up resources before closing"""
        self.queue_listener.stop()
        self.state_manager.unsubscribe(self.on_state_changed)
        self.destroy()

    def _show_screen(self, screen_class, *args):
        """Navigate to a different screen"""
        self.current_screen_class = screen_class

        if self.current_screen:
            self.current_screen.grid_forget()

        # Always create new screen instance for now
        # TODO: Implement screen caching/reuse if needed
        self.current_screen = screen_class(self.content_frame, *args, app=self)

        self.current_screen.grid(row=0, column=0, sticky="nsew")
        self.update()

        self.content_frame.grid_rowconfigure(0, weight=1)
        self.content_frame.grid_columnconfigure(0, weight=1)

        self.logger.info(f"Navigated to {screen_class.__name__}")

    def refresh_styles(self):
        """Refresh UI styles based on current theme"""
        theme = ctk.ThemeManager.theme

        # Update main window
        self.configure(fg_color=theme["CTkFrame"]["fg_color"])

        # Update header
        self.header.configure(fg_color=theme["CTkFrame"]["fg_color"])

        # Update appearance menu
        self.appearance_menu.configure(
            fg_color=theme["CTkOptionMenu"]["fg_color"],
            button_color=theme["CTkOptionMenu"]["button_color"],
            button_hover_color=theme["CTkOptionMenu"]["button_hover_color"],
            text_color=theme["CTkOptionMenu"]["text_color"],
        )

        # Update theme selector
        self.theme_selector.configure(
            fg_color=theme["CTkOptionMenu"]["fg_color"],
            button_color=theme["CTkOptionMenu"]["button_color"],
            button_hover_color=theme["CTkOptionMenu"]["button_hover_color"],
            text_color=theme["CTkOptionMenu"]["text_color"],
        )

        # Update buttons
        update_widgets_theme(
            [
                self.toggle_sidepanel_btn,
                self.toggle_btn,
                # ... more buttons
            ],
            "CTkButton",
        )

        # Update footer
        self.footer.configure(fg_color=theme["CTkFrame"]["fg_color"])
        self.log_textbox.configure(
            fg_color=theme["CTkTextbox"]["fg_color"],
            border_color=theme["CTkTextbox"]["border_color"],
            text_color=theme["CTkTextbox"]["text_color"],
        )
        mode = ctk.get_appearance_mode()
        # Map to brightness index (system resolves to light/dark)
        brightness = 1 if mode == "Dark" else 0  # 0=light, 1=dark

        self.tkinter_handler._update_tags(brightness)

        # Update footer
        self._update_footer_theme()

        # Update main content frame
        self.main_container.configure(
            fg_color=theme["CTkFrame"]["fg_color"],
            border_color=theme["CTkFrame"]["border_color"],
        )

        sf_theme = theme["CTkScrollableFrame"]
        self.content_frame.configure(
            label_fg_color=sf_theme["label_fg_color"],
            fg_color=sf_theme["fg_color"],
            border_color=sf_theme["border_color"],
        )

        # Update side panel
        self._update_sidepanel_theme()

        # Update all menus
        if hasattr(self, "menubar"):
            self._apply_menu_theme(self.menubar)
        if hasattr(self, "data_menu"):
            self._apply_menu_theme(self.data_menu)
        if hasattr(self, "view_menu"):
            self._apply_menu_theme(self.view_menu)
        if hasattr(self, "appearance_submenu"):
            self._apply_menu_theme(self.appearance_submenu)
        if hasattr(self, "theme_submenu"):
            self._apply_menu_theme(self.theme_submenu)
        if hasattr(self, "help_menu"):
            self._apply_menu_theme(self.help_menu)

        # Update current screen theme
        if self.current_screen and hasattr(self.current_screen, "update_theme"):
            self.current_screen.update_theme()

    def _update_sidepanel_theme(self):
        """Update side panel colors for current theme"""
        theme = ctk.ThemeManager.theme

        # Update side panel frame
        self.sidepanel.configure(
            fg_color=theme["CTkFrame"]["fg_color"],
            border_color=theme["CTkFrame"].get("border_color", "transparent"),
        )

        # Reconfigure all text tags with new theme colors
        self._configure_sidepanel_tags()

        # Refresh the content to apply new colors
        self.update_side_panel()

    def change_appearance_mode(self, new_mode):
        """Change application appearance mode"""
        ctk.set_appearance_mode(new_mode.lower())
        self.state_manager.update_config(appearance=new_mode)
        self.logger.info(f"Appearance mode changed to {new_mode}")
        self.refresh_styles()

    def change_theme(self, selected_theme: str):
        """Change application theme"""
        if self.theme_manager.load_theme(selected_theme):
            self.state_manager.update_config(theme=selected_theme)
            self.logger.info(f"Theme changed to {selected_theme}")
        else:
            self.logger.error(f"Failed to load theme: {selected_theme}")

    def show_start_form(self):
        """Show start form - only if data is available"""
        if not self._check_data_available():
            # Show download prompt only when needed
            from tkinter import messagebox

            response = messagebox.askyesno(
                "Data Required",
                "This feature requires data files.\n\nDownload now?",
                parent=self,
            )
            if response:
                self.show_data_download_dialog()
            return  # Don't show form

        self._show_screen(StartRunForm, self.show_warp_form)

    def show_warp_form(self):
        """Show warp form - only if data is available"""
        if not self._check_data_available():
            # Show download prompt only when needed
            from tkinter import messagebox

            response = messagebox.askyesno(
                "Data Required",
                "This feature requires data files.\n\nDownload now?",
                parent=self,
            )
            if response:
                self.show_data_download_dialog()
            return  # Don't show form

        self._show_screen(WarpForm, self.show_start_form)

    def show_warped_lesion_form(self):
        """Show warped lesion form - only if data is available"""
        if not self._check_data_available():
            # Show download prompt only when needed
            from tkinter import messagebox

            response = messagebox.askyesno(
                "Data Required",
                "This feature requires data files.\n\nDownload now?",
                parent=self,
            )
            if response:
                self.show_data_download_dialog()
            return  # Don't show form

        self._show_screen(WarpedLesionForm, self.show_start_form)

    def show_disconnectome_form(self):
        """Show disconnectome form - only if data is available"""
        if not self._check_data_available():
            # Show download prompt only when needed
            from tkinter import messagebox

            response = messagebox.askyesno(
                "Data Required",
                "This feature requires data files.\n\nDownload now?",
                parent=self,
            )
            if response:
                self.show_data_download_dialog()
            return  # Don't show form

        self._show_screen(DisconnectomeForm, self.show_warp_form)

    def show_final_result(self):
        """Show final result form - only if data is available"""
        if not self._check_data_available():
            # Show download prompt only when needed
            from tkinter import messagebox

            response = messagebox.askyesno(
                "Data Required",
                "This feature requires data files.\n\nDownload now?",
                parent=self,
            )
            if response:
                self.show_data_download_dialog()
            return  # Don't show form

        self._show_screen(FinalResult, self.show_disconnectome_form)

    def _check_data_available(self):
        """Quick check if data is available"""
        # Check local data
        if not getattr(sys, "frozen", False):
            from pathlib import Path

            local_data = Path(__file__).parent / "data"
            if (local_data / "controls").exists():
                return True

        # Check system data
        return self.data_downloader.is_fully_installed()

    def check_data_installation(self):
        """
        Check if required data files are installed.
        If not, prompt user to download them.
        """
        # In dev mode, check if local data exists first
        if not getattr(sys, "frozen", False):
            from pathlib import Path

            project_root = Path(__file__).parent
            local_data = project_root / "data"
            local_controls = local_data / "controls"
            local_template = local_data / "template"

            # If we have local data with controls, we're good
            if (
                local_controls.exists()
                and local_template.exists()
                and any(local_controls.iterdir())
            ):
                self.logger.info(f"Using local data directory: {local_data}")
                self.on_data_ready()
                return

        # Check downloaded/system data
        if self.data_downloader.is_fully_installed():
            self.logger.info("All required data files are installed")
            return

        self.logger.warning("Required data files are missing")
        self._show_data_warning_banner()

    def show_data_download_dialog(self):
        """Show the data download dialog"""

        def on_complete(success):
            if success:
                self.logger.info("Data download completed successfully")
                self.on_data_ready()
            else:
                self.logger.error("Data download failed")
                self.show_download_failure_dialog()

        DataDownloadDialog(self, on_complete=on_complete)

    def _show_data_warning_banner(self):
        """Show non-intrusive warning about missing data"""
        # Check if banner already exists
        if hasattr(self, "_warning_banner") and self._warning_banner.winfo_exists():
            return

        self._warning_banner = ctk.CTkFrame(
            self.header, fg_color=("orange", "darkorange"), height=35
        )
        self._warning_banner.pack(side="bottom", fill="x", padx=10, pady=(0, 5))
        self._warning_banner.pack_propagate(False)

        warning_label = ctk.CTkLabel(
            self._warning_banner,
            text="⚠️ Data files not installed. Download from Data menu to enable processing.",
            text_color="white",
            font=ctk.CTkFont(size=12, weight="bold"),
        )
        warning_label.pack(side="left", padx=15, pady=5)

        download_btn = ctk.CTkButton(
            self._warning_banner,
            text="Download Now",
            width=120,
            height=25,
            command=self._download_from_banner,
        )
        download_btn.pack(side="right", padx=5, pady=5)

        dismiss_btn = ctk.CTkButton(
            self._warning_banner,
            text="✕",
            width=25,
            height=25,
            command=self._warning_banner.destroy,
        )
        dismiss_btn.pack(side="right", padx=(0, 10), pady=5)

    def _download_from_banner(self):
        """Handle download button click from banner"""
        if hasattr(self, "_warning_banner"):
            self._warning_banner.destroy()
        self.show_data_download_dialog()

    def on_data_ready(self):
        """
        Called when data is confirmed to be installed and ready.
        Update any paths or configurations that depend on downloaded data.
        """
        # Update paths in constants if needed
        from lib import constants

        # Log data locations
        self.logger.info(f"Controls directory: {constants.CONTROLS_DIR}")
        self.logger.info(f"Templates directory: {constants.TEMPLATE_TEMPLATES_DIR}")

        # Enable any features that were disabled
        # For example, if you disabled the start button:
        # self.start_button.configure(state="normal")

    def show_download_failure_dialog(self):
        """Show dialog when download fails"""
        from tkinter import messagebox

        response = messagebox.askyesnocancel(
            "Download Failed",
            "Failed to download required data files.\n\n"
            "Would you like to:\n"
            "• YES - Retry download\n"
            "• NO - Continue without data (limited functionality)\n"
            "• CANCEL - Exit application",
        )

        if response is True:  # Yes - retry
            self.show_data_download_dialog()
        elif response is False:  # No - continue
            self.show_limited_mode_warning()
        else:  # Cancel - exit
            self.quit()

    def create_menu(self):
        """Create themed menu bar with data management and view options"""
        menubar = tk.Menu(self)

        # Apply theme colors to menubar
        self._apply_menu_theme(menubar)

        # ====================================================================
        # FILE MENU
        # ====================================================================
        file_menu = tk.Menu(menubar, tearoff=0)
        self._apply_menu_theme(file_menu)

        file_menu.add_command(
            label="Start a new run",
            command=self.start_a_new_run,
            accelerator="Cmd+N" if sys.platform == "darwin" else "Ctrl+N",
        )

        file_menu.add_separator()
        file_menu.add_command(
            label="Exit Application",
            command=self.destroy,
            accelerator="Cmd+Q" if sys.platform == "darwin" else "Ctrl+Q",
        )

        menubar.add_cascade(label="File", menu=file_menu)
        # ====================================================================
        # DATA MENU
        # ====================================================================
        data_menu = tk.Menu(menubar, tearoff=0)
        self._apply_menu_theme(data_menu)

        data_menu.add_command(
            label="Download Data Files...",
            command=self.show_data_download_dialog,
            accelerator="Cmd+D" if sys.platform == "darwin" else "Ctrl+D",
        )
        data_menu.add_command(label="Check Data Status", command=self.show_data_status)
        data_menu.add_separator()
        data_menu.add_command(
            label="Change Data Location...", command=self.change_data_location
        )
        data_menu.add_command(label="Open Data Folder", command=self.open_data_folder)

        menubar.add_cascade(label="Data", menu=data_menu)

        # ====================================================================
        # VIEW MENU
        # ====================================================================
        view_menu = tk.Menu(menubar, tearoff=0)
        self._apply_menu_theme(view_menu)

        view_menu.add_command(
            label="Toggle Side Panel",
            command=self.toggle_sidepanel,
            accelerator="Cmd+1" if sys.platform == "darwin" else "Ctrl+1",
        )
        view_menu.add_command(
            label="Toggle Console",
            command=self.toggle_log_visibility,
            accelerator="Cmd+2" if sys.platform == "darwin" else "Ctrl+2",
        )
        view_menu.add_separator()

        # Appearance submenu
        appearance_submenu = tk.Menu(view_menu, tearoff=0)
        self._apply_menu_theme(appearance_submenu)
        appearance_submenu.add_command(
            label="Light Mode", command=lambda: self.change_appearance_mode("Light")
        )
        appearance_submenu.add_command(
            label="Dark Mode", command=lambda: self.change_appearance_mode("Dark")
        )
        appearance_submenu.add_command(
            label="System", command=lambda: self.change_appearance_mode("System")
        )
        view_menu.add_cascade(label="Appearance", menu=appearance_submenu)

        # Theme submenu
        theme_submenu = tk.Menu(view_menu, tearoff=0)
        self._apply_menu_theme(theme_submenu)
        for theme_name in self.theme_manager.get_available_themes():
            theme_submenu.add_command(
                label=theme_name.replace("_", " ").title(),
                command=lambda t=theme_name: self.change_theme(t),
            )
        view_menu.add_cascade(label="Theme", menu=theme_submenu)

        menubar.add_cascade(label="View", menu=view_menu)

        # ====================================================================
        # HELP MENU
        # ====================================================================
        help_menu = tk.Menu(menubar, tearoff=0)
        self._apply_menu_theme(help_menu)

        help_menu.add_command(label="About Disconnectome", command=self.show_about)

        menubar.add_cascade(label="Help", menu=help_menu)

        # Configure menu bar
        self.config(menu=menubar)

        # Store references for theme updates
        self.menubar = menubar
        self.data_menu = data_menu
        self.view_menu = view_menu
        self.appearance_submenu = appearance_submenu
        self.theme_submenu = theme_submenu
        self.help_menu = help_menu

        # Bind keyboard shortcuts
        self._bind_menu_shortcuts()

    def _apply_menu_theme(self, menu):
        """Apply current theme colors to a menu widget"""
        theme = ctk.ThemeManager.theme
        appearance_mode = ctk.get_appearance_mode()
        is_dark = appearance_mode == "Dark"

        # Helper to get theme colors
        def get_color(widget_type, property_name, default_light, default_dark):
            try:
                if widget_type in theme and property_name in theme[widget_type]:
                    value = theme[widget_type][property_name]
                    if isinstance(value, (list, tuple)) and len(value) >= 2:
                        return value[1] if is_dark else value[0]
                    return value
            except:
                pass
            return default_dark if is_dark else default_light

        # Get colors from current theme
        bg_color = get_color("CTkFrame", "fg_color", "#FFFFFF", "#2B2B2B")
        fg_color = get_color("CTkLabel", "text_color", "#000000", "#FFFFFF")
        active_bg = get_color("CTkButton", "hover_color", "#E0E0E0", "#3A3A3A")
        select_color = get_color("CTkButton", "fg_color", "#007AFF", "#0A84FF")

        try:
            menu.config(
                bg=bg_color,
                fg=fg_color,
                activebackground=active_bg,
                activeforeground=fg_color,
                selectcolor=select_color,
                relief=tk.FLAT,
                borderwidth=0,
                activeborderwidth=0,
            )
        except Exception as e:
            # Some platforms may not support all options
            self.logger.debug(f"Menu theme config warning: {e}")

    def _bind_menu_shortcuts(self):
        """Bind keyboard shortcuts for menu items"""
        # Determine modifier key (Cmd on macOS, Ctrl elsewhere)
        modifier = "Command" if sys.platform == "darwin" else "Control"

        # Data shortcuts
        self.bind(f"<{modifier}-d>", lambda e: self.show_data_download_dialog())

        # View shortcuts
        self.bind(f"<{modifier}-1>", lambda e: self.toggle_sidepanel())
        self.bind(f"<{modifier}-2>", lambda e: self.toggle_log_visibility())

    def show_about(self):
        """Show about dialog"""
        from tkinter import messagebox
        from lib.constants import __version__, __build_date__, __author__

        about_text = (
            f"Disconnectome v{__version__}\n"
            f"Build Date: {__build_date__}\n\n"
            f"Developed by {__author__}\n\n"
            "Brain disconnectome analysis tool for\n"
            "neonatal brain imaging data\n\n"
            "For research use only\n\n"
            "---\n\n"
            "Technologies:\n"
            "• Python 3.11+\n"
            "• CustomTkinter\n"
            "• ANTs (Advanced Normalization Tools)\n"
            "• dHCP Brain Templates\n\n"
            "Data Location:\n"
            f"{self.data_downloader.data_dir}"
        )

        messagebox.showinfo("About Disconnectome", about_text, parent=self)

    def show_data_menu(self):
        """Show data management options"""
        from tkinter import messagebox

        # Get current status
        status = self.data_downloader.check_installation()
        info = self.data_downloader.get_download_info()

        # Build status message
        msg = "Data Installation Status:\n\n"

        for pkg_name, is_installed in status.items():
            status_icon = "✓" if is_installed else "✗"
            msg += f"{status_icon} {pkg_name}\n"

        msg += f"\nData Location:\n{self.data_downloader.data_dir}\n"

        if info["missing_count"] > 0:
            msg += f"\nMissing: {info['missing_count']} packages (~{info['total_size_mb']} MB)"

        # Show messagebox with options
        response = messagebox.askyesno(
            "Data Management", msg + "\n\nWould you like to manage data files?"
        )

        if response:
            self.show_data_management_dialog()

    def show_data_management_dialog(self):
        """Show detailed data management dialog"""
        # Create a simple dialog with options
        dialog = ctk.CTkToplevel(self)
        dialog.title("Data Management")
        dialog.geometry("400x300")

        # Make modal
        dialog.transient(self)
        dialog.grab_set()

        frame = ctk.CTkFrame(dialog)
        frame.pack(fill="both", expand=True, padx=20, pady=20)

        # Title
        title = ctk.CTkLabel(
            frame, text="Data Management", font=ctk.CTkFont(size=16, weight="bold")
        )
        title.pack(pady=(0, 20))

        # Download button
        download_btn = ctk.CTkButton(
            frame,
            text="Download/Update Data Files",
            command=lambda: [dialog.destroy(), self.show_data_download_dialog()],
        )
        download_btn.pack(pady=5, fill="x")

        # Check status button
        check_btn = ctk.CTkButton(
            frame,
            text="Check Installation Status",
            command=lambda: self.show_data_status(),
        )
        check_btn.pack(pady=5, fill="x")

        # Change location button
        location_btn = ctk.CTkButton(
            frame,
            text="Change Data Location",
            command=lambda: [dialog.destroy(), self.change_data_location()],
        )
        location_btn.pack(pady=5, fill="x")

        # Open location button
        open_btn = ctk.CTkButton(
            frame, text="Open Data Folder", command=lambda: self.open_data_folder()
        )
        open_btn.pack(pady=5, fill="x")

        # Close button
        close_btn = ctk.CTkButton(frame, text="Close", command=dialog.destroy)
        close_btn.pack(pady=(20, 0))

    def show_data_status(self):
        """Show detailed data installation status"""
        from tkinter import messagebox

        status = self.data_downloader.check_installation()

        msg = "Data Installation Status:\n\n"
        for pkg_name, config in self.data_downloader.DATA_SOURCES.items():
            is_installed = status.get(pkg_name, False)
            status_icon = "✓" if is_installed else "✗"

            msg += f"{status_icon} {config['description']}\n"
            if is_installed:
                pkg_path = self.data_downloader.get_package_path(pkg_name)
                if pkg_path:
                    msg += f"   Location: {pkg_path}\n"

        msg += f"\nData Directory: {self.data_downloader.data_dir}"

        messagebox.showinfo("Data Status", msg)

    def change_data_location(self):
        """Allow user to change data storage location"""
        from tkinter import filedialog, messagebox

        new_location = filedialog.askdirectory(
            title="Choose New Data Location",
            initialdir=str(self.data_downloader.data_dir.parent),
        )

        if new_location:
            # Update downloader
            old_location = self.data_downloader.data_dir
            self.data_downloader = DataDownloader(data_dir=new_location)

            self.logger.info(f"Data location changed: {old_location} -> {new_location}")

            messagebox.showinfo(
                "Location Changed",
                f"Data location changed to:\n{new_location}\n\n"
                "You may need to re-download data files.",
            )

            # Check if data needs to be downloaded
            if not self.data_downloader.is_fully_installed():
                response = messagebox.askyesno(
                    "Download Data",
                    "Data files not found in new location.\n\n"
                    "Would you like to download them now?",
                )
                if response:
                    self.show_data_download_dialog()

    def open_data_folder(self):
        """Open data folder in file manager"""
        from lib.utils import open_in_file_browser

        data_path = str(self.data_downloader.data_dir)

        # Create directory if it doesn't exist
        self.data_downloader.data_dir.mkdir(parents=True, exist_ok=True)

        open_in_file_browser(data_path)

    def start_a_new_run(self):
        self.logger.info("Starting a new run...")
        self.state_manager.reset_processing()
        self.show_start_form()


if __name__ == "__main__":
    app = DisconnectomeApp()
    app.protocol("WM_DELETE_WINDOW", app.on_closing)
    app.mainloop()
