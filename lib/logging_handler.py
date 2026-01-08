"""
Thread-safe logging handler for Tkinter text widgets.
"""

import logging
import queue
import threading
from typing import Optional


class ThreadSafeTkinterHandler(logging.Handler):
    """
    Thread-safe logging handler that writes to a Tkinter Text widget.

    This handler uses a queue-based approach to ensure all GUI updates
    happen on the main thread, preventing race conditions and crashes.
    """

    def __init__(self, text_widget, brightness: int = 0, max_lines: int = 1000):
        """
        Initialize handler.

        Args:
            text_widget: Tkinter Text widget to write to
            brightness: 0 for light mode, 1 for dark mode
            max_lines: Maximum number of lines to keep in widget
        """
        super().__init__()
        self.text_widget = text_widget
        self.brightness = brightness
        self.max_lines = max_lines

        # Configure widget
        self.text_widget.configure(state="disabled")
        self._update_tags(brightness)

        # Thread-safe message queue
        self._message_queue = queue.Queue(maxsize=1000)
        self._running = True

        # Start consumer thread
        self._start_consumer()

    def _start_consumer(self):
        """Start consumer thread that writes to widget"""

        def consume():
            """Consumer loop"""
            while self._running:
                try:
                    # Get message with timeout
                    msg, level = self._message_queue.get(timeout=0.1)

                    # Schedule write on GUI thread
                    if self.text_widget.winfo_exists():
                        self.text_widget.after(
                            0, lambda: self._write_message(msg, level)
                        )

                except queue.Empty:
                    continue
                except Exception as e:
                    # Log to console as fallback
                    print(f"Error in log consumer: {e}")

        consumer_thread = threading.Thread(target=consume, daemon=True)
        consumer_thread.start()

    def emit(self, record):
        """Emit a log record (called from any thread)"""
        try:
            msg = self.format(record) + "\n"
            level = record.levelname

            # Add to queue (non-blocking)
            try:
                self._message_queue.put_nowait((msg, level))
            except queue.Full:
                # Queue full, drop oldest message and try again
                try:
                    self._message_queue.get_nowait()
                    self._message_queue.put_nowait((msg, level))
                except:
                    pass  # Give up if still fails

        except Exception:
            self.handleError(record)

    def _write_message(self, msg: str, level: str):
        """Write message to widget (must be called on GUI thread)"""
        if not self.text_widget.winfo_exists():
            return

        try:
            # Enable widget for editing
            self.text_widget.configure(state="normal")

            # Insert message with appropriate tag
            self.text_widget.insert("end", msg, level)

            # Limit number of lines
            line_count = int(self.text_widget.index("end-1c").split(".")[0])
            if line_count > self.max_lines:
                # Delete oldest lines
                delete_count = line_count - self.max_lines
                self.text_widget.delete("1.0", f"{delete_count}.0")

            # Scroll to end
            self.text_widget.see("end")

            # Disable widget
            self.text_widget.configure(state="disabled")

        except Exception as e:
            # Widget might be destroyed
            print(f"Error writing log message: {e}")

    def _update_tags(self, brightness: int):
        """Update tag colors based on brightness"""
        self.brightness = brightness

        if brightness == 0:  # Light mode
            self.text_widget.tag_config("DEBUG", foreground="#00aaaa")
            self.text_widget.tag_config("INFO", foreground="#333333")
            self.text_widget.tag_config("WARNING", foreground="#FF9500")
            self.text_widget.tag_config("ERROR", foreground="#cc0000")
            self.text_widget.tag_config(
                "CRITICAL", foreground="#ffffff", background="#cc0000"
            )
        else:  # Dark mode
            self.text_widget.tag_config("DEBUG", foreground="#66ffff")
            self.text_widget.tag_config("INFO", foreground="#ffffff")
            self.text_widget.tag_config("WARNING", foreground="#FFB340")
            self.text_widget.tag_config("ERROR", foreground="#ff9999")
            self.text_widget.tag_config(
                "CRITICAL", foreground="#000000", background="#ffff00"
            )

    def update_brightness(self, brightness: int):
        """Update brightness mode (can be called from any thread)"""

        def update():
            self._update_tags(brightness)

        if self.text_widget.winfo_exists():
            self.text_widget.after(0, update)

    def close(self):
        """Close the handler"""
        self._running = False
        super().close()
