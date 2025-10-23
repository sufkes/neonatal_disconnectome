import logging
import queue
import os
from logging.handlers import QueueHandler, QueueListener, RotatingFileHandler

import customtkinter as ctk
from customtkinter import CTkImage
from PIL import Image

from screens.disconnectome_form import DisconnectomeForm
from screens.result_screen import FinalResult
from screens.start_screen import StartRunForm
from screens.warp_form import WarpForm
from utils import get_theme_names_from_folder, load_settings, update_settings

DARK_GREY = "#2F2F2F"
THEME_OPTIONS = get_theme_names_from_folder()
settings = load_settings()

if settings:
    ctk.set_appearance_mode(settings.get("appearance", "light"))
    theme = settings.get("theme", THEME_OPTIONS[0])
    ctk.set_default_color_theme(f"themes/{theme}.json")
else:
    ctk.set_default_color_theme(f"themes/{THEME_OPTIONS[0]}.json")
    ctk.set_appearance_mode("light")


class TkinterTextHandler(logging.Handler):
    """Logging handler that directs logs into a Tkinter Textbox (thread-safe)."""

    def __init__(self, text_widget):
        super().__init__()
        self.text_widget = text_widget
        self.text_widget.configure(state="disabled")

        self.text_widget.tag_config("DEBUG", foreground="cyan")
        self.text_widget.tag_config("INFO", foreground="white")
        self.text_widget.tag_config("WARNING", foreground="yellow")
        self.text_widget.tag_config("ERROR", foreground="red")
        self.text_widget.tag_config("CRITICAL", foreground="red", background="yellow")

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


class DisconnectomeApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Disconnectome")
        self.geometry("1024x768")
        self.minsize(640, 480)

        # Configure grid: 3 rows (header, main, footer)
        self.grid_rowconfigure(1, weight=1)  # main expands
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(
            2, weight=0
        )  # footer row weight, or set to 1 if you want it to expand

        self.create_header()
        self.create_footer()

        # --- Main scrollable content area ---
        self.content_frame = ctk.CTkScrollableFrame(self, corner_radius=0)
        self.content_frame.grid(row=1, column=0, sticky="nsew")

        # Logger setup
        self._init_logging()

        self.current_screen = None
        self.current_screen_class = None
        self.current_screen_args = None
        self.app_data = {}

        self.logger.info("DisconnectomeApp started")
        self.show_start_form()

    def create_header(self):
        # --- Header ---
        # Destroy existing header if exists
        if hasattr(self, "header"):
            self.header.destroy()
        self.header = ctk.CTkFrame(self, height=60, corner_radius=0)
        self.header.grid(row=0, column=0, sticky="ew")
        self.header.grid_propagate(False)

        # Logo (replace "logo_light.png" and "logo_dark.png" with your actual logo files)
        light_img = Image.open("web/img/logo.png")
        dark_img = Image.open("web/img/logo.png")
        self.logo_image = CTkImage(
            light_image=light_img, dark_image=dark_img, size=(40, 40)
        )
        self.logo_label = ctk.CTkLabel(self.header, image=self.logo_image, text="")
        self.logo_label.pack(side="left", padx=15, pady=10)

        # Appearance mode selector dropdown
        appearance_options = ["Light", "Dark", "System"]
        current_mode = ctk.get_appearance_mode()

        self.appearance_menu = ctk.CTkOptionMenu(
            self.header, values=appearance_options, command=self.change_appearance_mode
        )
        self.appearance_menu.set(current_mode.capitalize())
        self.appearance_menu.pack(side="right", padx=15, pady=10)

        # List your themes - can be names or paths

        self.theme_selector = ctk.CTkOptionMenu(
            self.header, values=THEME_OPTIONS, command=self.change_theme, width=150
        )
        if settings:
            saved_theme = settings.get("theme", THEME_OPTIONS[0])
            self.theme_selector.set(saved_theme)  # Default value
        else:
            self.theme_selector.set(THEME_OPTIONS[0])  # Default value
        self.theme_selector.pack(side="right", padx=10, pady=10)

    def create_footer(self):
        if hasattr(self, "footer"):
            self.footer.destroy()
        # --- Footer with logging ---
        self.footer = ctk.CTkFrame(
            self, height=150, corner_radius=0, fg_color=(DARK_GREY, DARK_GREY)
        )
        self.footer.grid(row=2, column=0, sticky="nsew", padx=30, pady=(0, 10))
        self.footer.grid_propagate(False)
        self.footer.grid_columnconfigure(0, weight=1)
        self.footer.grid_rowconfigure(0, weight=1)

        self.log_textbox = ctk.CTkTextbox(self.footer, fg_color=(DARK_GREY, DARK_GREY))
        self.log_textbox.grid(row=0, column=0, sticky="nsew")

        # Toggle button grid in column 1
        self.toggle_btn = ctk.CTkButton(
            self.footer,
            text="▼",  # Start with arrow down meaning box is visible
            width=25,
            height=25,
            command=self.toggle_log_visibility,
            corner_radius=0,
        )
        self.toggle_btn.grid(row=0, column=1, sticky="ne", padx=5, pady=5)

    def toggle_log_visibility(self):
        if self.log_textbox.winfo_ismapped():
            self.log_textbox.grid_remove()
            self.toggle_btn.configure(text="▲")  # Up arrow meaning box is hidden
            self.footer.configure(height=35)  # Adjust footer height when hidden
        else:
            self.log_textbox.grid()
            self.toggle_btn.configure(text="▼")  # Down arrow when box visible
            self.footer.configure(height=150)  # Restore footer height

    def _init_logging(self):
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

        tkinter_handler = TkinterTextHandler(self.log_textbox)
        tkinter_handler.setFormatter(formatter)

        self.queue_listener = QueueListener(
            self.log_queue,
            rotating_file_handler,
            tkinter_handler,
            respect_handler_level=True,
        )
        self.queue_listener.start()

    def on_closing(self):
        self.queue_listener.stop()
        self.destroy()

    def _show_screen(self, screen_class, *args):
        self.current_screen_class = screen_class
        self.current_screen_args = args

        if self.current_screen:
            if hasattr(self.current_screen, "save_data"):
                self.current_screen.save_data(self.app_data)
            self.current_screen.grid_forget()  # Hide instead of destroying

        if (
            self.current_screen_class
            and self.current_screen
            and isinstance(self.current_screen, screen_class)
        ):
            # Reuse existing screen instance
            self.current_screen.grid(row=0, column=0, sticky="nsew")
            self.update()
        else:
            # Create new screen instance if needed
            self.current_screen = screen_class(self.content_frame, *args, app=self)
            if hasattr(self.current_screen, "load_data"):
                self.current_screen.load_data(self.app_data)
            self.current_screen.grid(row=0, column=0, sticky="nsew")
            self.update()

        self.content_frame.grid_rowconfigure(0, weight=1)
        self.content_frame.grid_columnconfigure(0, weight=1)

        self.logger.info(f"Navigated to {screen_class.__name__}")

    def refresh_styles(self):
        # Update header
        self.header.configure(fg_color=ctk.ThemeManager.theme["CTkFrame"]["fg_color"])
        self.logo_label.configure(
            text_color=ctk.ThemeManager.theme["CTkLabel"]["text_color"]
        )

        self.appearance_menu.configure(
            fg_color=ctk.ThemeManager.theme["CTkOptionMenu"]["fg_color"],
            button_color=ctk.ThemeManager.theme["CTkOptionMenu"]["button_color"],
            button_hover_color=ctk.ThemeManager.theme["CTkOptionMenu"][
                "button_hover_color"
            ],
            text_color=ctk.ThemeManager.theme["CTkOptionMenu"]["text_color"],
        )

        self.theme_selector.configure(
            fg_color=ctk.ThemeManager.theme["CTkOptionMenu"]["fg_color"],
            button_color=ctk.ThemeManager.theme["CTkOptionMenu"]["button_color"],
            button_hover_color=ctk.ThemeManager.theme["CTkOptionMenu"][
                "button_hover_color"
            ],
            text_color=ctk.ThemeManager.theme["CTkOptionMenu"]["text_color"],
        )

        # Update footer
        # Optional: keep footer gray regardless of theme
        self.footer.configure(
            fg_color=(DARK_GREY, DARK_GREY),
        )

        self.log_textbox.configure(
            fg_color=(DARK_GREY, DARK_GREY),
            border_color=ctk.ThemeManager.theme["CTkTextbox"]["border_color"],
            text_color=ctk.ThemeManager.theme["CTkTextbox"]["text_color"],
            scrollbar_button_color=ctk.ThemeManager.theme["CTkTextbox"][
                "scrollbar_button_color"
            ],
            scrollbar_button_hover_color=ctk.ThemeManager.theme["CTkTextbox"][
                "scrollbar_button_hover_color"
            ],
        )

        self.logger.info(ctk.ThemeManager.theme["CTkScrollableFrame"])

        # Update main content frame

        sf_theme = ctk.ThemeManager.theme["CTkScrollableFrame"]
        self.content_frame.configure(
            label_fg_color=sf_theme["label_fg_color"],
            fg_color=sf_theme["fg_color"],
            border_color=sf_theme["border_color"],
        )

        # You can add calls to update current_screen widgets themes as well if needed
        if self.current_screen and hasattr(self.current_screen, "update_theme"):
            self.current_screen.update_theme()

    def change_appearance_mode(self, new_mode):
        ctk.set_appearance_mode(new_mode.lower())
        update_settings(appearance=new_mode)
        self.logger.info(f"Appearance mode changed to {new_mode}")
        self.refresh_styles()

    def change_theme(self, selected_theme):
        # Load the selected theme JSON file from the themes folder
        theme_path = f"themes/{selected_theme}.json"
        if os.path.isfile(theme_path):
            ctk.set_default_color_theme(theme_path)
        else:
            ctk.set_default_color_theme(selected_theme)

        update_settings(theme=selected_theme)
        self.logger.info(f"Theme changed to {selected_theme}")
        self.refresh_styles()

    def show_start_form(self):
        self._show_screen(StartRunForm, self.show_warp_form)

    def show_warp_form(self):
        self._show_screen(WarpForm, self.show_start_form)

    def show_disconnectome_form(self):
        self._show_screen(DisconnectomeForm, self.show_warp_form)

    def show_final_result(self):
        self._show_screen(FinalResult, self.show_disconnectome_form)


if __name__ == "__main__":
    app = DisconnectomeApp()
    app.protocol("WM_DELETE_WINDOW", app.on_closing)
    app.mainloop()
