import logging
import queue
from logging.handlers import QueueHandler, QueueListener, RotatingFileHandler
import customtkinter as ctk

from screens.start_screen import StartRunForm
from screens.warp_form import WarpForm
from screens.disconnectome_form import DisconnectomeForm
from screens.result_screen import FinalResult

ctk.set_appearance_mode("light")  # Options: "dark", "light", "system"
ctk.set_default_color_theme("dark-blue")  # Themes: "blue", "green", "dark-blue"

class TkinterTextHandler(logging.Handler):
    """Logging handler that directs logs into a Tkinter Textbox (thread-safe)."""

    def __init__(self, text_widget):
        super().__init__()
        self.text_widget = text_widget
        self.text_widget.configure(state='disabled')

        self.text_widget.tag_config("DEBUG", foreground="cyan")
        self.text_widget.tag_config("INFO", foreground="white")
        self.text_widget.tag_config("WARNING", foreground="yellow")
        self.text_widget.tag_config("ERROR", foreground="red")
        self.text_widget.tag_config("CRITICAL", foreground="red", background="yellow")

    def emit(self, record):
        try:
            msg = self.format(record) + '\n'

            def append():
                self.text_widget.configure(state='normal')
                level = record.levelname
                self.text_widget.insert("end", msg, level)
                self.text_widget.configure(state='disabled')
                self.text_widget.see("end")

            # Use Tkinter .after to safely update text widget from any thread
            self.text_widget.after(0, append)
        except Exception:
            self.handleError(record)


class DisconnectomeApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Disconnectome")
        self.geometry("1024x768")
        self.minsize(640, 480)

        # Configure main grid rows and columns for resizing
        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=0)  # Logging panel row
        self.grid_columnconfigure(0, weight=1)

        self.current_screen = None
        self.current_scrollable_frame = None
        self.app_data = {}

        # Create read-only CTkTextbox for logs
        self.log_widget = ctk.CTkTextbox(self, height=150)
        self.log_widget.grid(row=1, column=0, padx=10, pady=(0, 10), sticky="ew")
        self.log_widget.configure(fg_color="#2F2F2F")  # set background to gray

        # Create a queue for log records
        self.log_queue = queue.Queue(maxsize=1000)

        # Set up logger
        self.logger = logging.getLogger('disconnectome')
        self.logger.setLevel(logging.DEBUG)
        self.logger.handlers.clear()  # Clear existing handlers

        # Add QueueHandler to send logs to queue
        queue_handler = QueueHandler(self.log_queue)
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        queue_handler.setFormatter(formatter)
        self.logger.addHandler(queue_handler)

        # RotatingFileHandler to prevent log file overgrowing (5MB max, 5 backups)
        rotating_file_handler = RotatingFileHandler(
            "disconnectome.log", maxBytes=5*1024*1024, backupCount=5)
        rotating_file_handler.setFormatter(formatter)

        # Create custom Tkinter handler to update GUI
        tkinter_handler = TkinterTextHandler(self.log_widget)
        tkinter_handler.setFormatter(formatter)

        # QueueListener dispatches from queue to file and GUI handlers
        self.queue_listener = QueueListener(
            self.log_queue, rotating_file_handler, tkinter_handler, respect_handler_level=True)
        self.queue_listener.start()

        self.logger.info("DisconnectomeApp started")

        self.show_start_form()

    def on_closing(self):
        # Properly stop the listener thread before closing app
        self.queue_listener.stop()
        self.destroy()

    def _show_screen(self, screen_class, *args):
        if self.current_screen:
            if hasattr(self.current_screen, 'save_data'):
                self.current_screen.save_data(self.app_data)
            self.current_screen.destroy()
            self.current_screen = None
        if self.current_scrollable_frame:
            self.current_scrollable_frame.destroy()
            self.current_scrollable_frame = None

        # Create new scrollable frame container
        self.current_scrollable_frame = ctk.CTkScrollableFrame(self, width=630, height=700)
        self.current_scrollable_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")

        # Bind mouse wheel events for smooth scrolling on all platforms
        sf = self.current_scrollable_frame
        sf.bind_all("<MouseWheel>", lambda e: sf._parent_canvas.yview_scroll(int(-1 * (e.delta / 120)), "units"))
        sf.bind_all("<Button-4>", lambda e: sf._parent_canvas.yview_scroll(-1, "units"))
        sf.bind_all("<Button-5>", lambda e: sf._parent_canvas.yview_scroll(1, "units"))

        # Instantiate and place screen inside scrollable frame
        self.current_screen = screen_class(self.current_scrollable_frame, *args, app=self)
        if hasattr(self.current_screen, 'load_data'):
            self.current_screen.load_data(self.app_data)
        self.current_screen.grid(row=0, column=0, sticky="nsew")

        # Configure grid weights for scrollable frame
        self.current_scrollable_frame.grid_rowconfigure(0, weight=1)
        self.current_scrollable_frame.grid_columnconfigure(0, weight=1)

        self.logger.info(f"Navigated to {screen_class.__name__}")

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
