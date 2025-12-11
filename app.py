import logging
import queue
from logging.handlers import QueueHandler, QueueListener, RotatingFileHandler

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

# Initialize state manager globally
state_manager = StateManager()


class TkinterTextHandler(logging.Handler):
    """Logging handler that directs logs into a Tkinter Textbox (thread-safe)."""

    def __init__(self, text_widget, brightness):
        super().__init__()

        self.text_widget = text_widget
        self.text_widget.configure(state="disabled")

        self._update_tags(brightness)

    def emit(self, record):
        try:
            msg = self.format(record) + "\n"

            def append():
                if self.text_widget.winfo_exists():
                    self.text_widget.configure(state="normal")
                    level = record.levelname
                    self.text_widget.insert("end", msg, level)
                    self.text_widget.configure(state="disabled")
                    self.text_widget.see("end")

            self.text_widget.after(0, append)
        except Exception:
            self.handleError(record)

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
        self.geometry("1024x768")
        self.minsize(640, 480)

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
        """Create application header with logo and controls"""
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
            light_img = Image.open("logo.png")
            dark_img = Image.open("logo.png")
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

        # Use smaller font sizes
        self.textbox = tk.Text(
            self.sidepanel,
            wrap="word",
            font=("Helvetica", 9),  # Smaller base font
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
        header_font = tkfont.Font(family="Helvetica", size=11, weight="bold")
        title_font = tkfont.Font(family="Helvetica", size=10, weight="bold")

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
            # Save current screen state (deprecated method)
            if hasattr(self.current_screen, "save_data"):
                self.current_screen.save_data(self.app_data)
            self.current_screen.grid_forget()

        # Always create new screen instance for now
        # TODO: Implement screen caching/reuse if needed
        self.current_screen = screen_class(self.content_frame, *args, app=self)

        # Load screen state (deprecated method)
        if hasattr(self.current_screen, "load_data"):
            self.current_screen.load_data(self.app_data)

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
        self._show_screen(StartRunForm, self.show_warp_form)

    def show_warp_form(self):
        self._show_screen(WarpForm, self.show_start_form)

    def show_warped_lesion_form(self):
        """Show form for processing pre-warped lesion masks"""
        self._show_screen(WarpedLesionForm, self.show_start_form)

    def show_disconnectome_form(self):
        self._show_screen(DisconnectomeForm, self.show_warp_form)

    def show_final_result(self):
        self._show_screen(FinalResult, self.show_disconnectome_form)


if __name__ == "__main__":
    app = DisconnectomeApp()
    app.protocol("WM_DELETE_WINDOW", app.on_closing)
    app.mainloop()
