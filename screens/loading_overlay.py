import customtkinter as ctk


class LoadingOverlay(ctk.CTkFrame):
    """Improved loading overlay with better responsiveness"""

    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)

        # Make overlay cover entire parent, semi-transparent dark backdrop
        self.configure(
            fg_color=("#333333", "#1a1a1a")
        )  # Dark gray with slight transparency effect

        # Create container for centered content
        self.content_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.content_frame.place(relx=0.5, rely=0.5, anchor="center")

        # Loading spinner (indeterminate progress bar)
        self.progressbar = ctk.CTkProgressBar(
            self.content_frame, mode="indeterminate", width=300, height=8
        )
        self.progressbar.grid(row=0, column=0, pady=(0, 10))

        # Status label
        self.status_label = ctk.CTkLabel(
            self.content_frame,
            text="Processing...",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="white",
        )
        self.status_label.grid(row=1, column=0)

        # Detail label for substep info
        self.detail_label = ctk.CTkLabel(
            self.content_frame,
            text="",
            font=ctk.CTkFont(size=11),
            text_color=("#cccccc", "#999999"),
        )
        self.detail_label.grid(row=2, column=0, pady=(5, 0))

        # Progress percentage label
        self.progress_label = ctk.CTkLabel(
            self.content_frame,
            text="",
            font=ctk.CTkFont(size=12),
            text_color=("#aaaaaa", "#888888"),
        )
        self.progress_label.grid(row=3, column=0, pady=(5, 0))

        self.progressbar.stop()
        self.hide()

    def show(self, status="Processing...", detail=""):
        """Show overlay with optional status message"""
        self.status_label.configure(text=status)
        self.detail_label.configure(text=detail)
        self.progress_label.configure(text="")
        self.lift()  # Bring to front
        self.place(relx=0, rely=0, relwidth=1, relheight=1)
        self.progressbar.start()
        self.update_idletasks()  # Force UI update

    def update_status(self, status=None, detail=None, progress=None):
        """Update overlay status without hiding/showing"""
        if status is not None:
            self.status_label.configure(text=status)
        if detail is not None:
            self.detail_label.configure(text=detail)
        if progress is not None:
            self.progress_label.configure(text=f"{int(progress * 100)}%")
        self.update_idletasks()  # Force UI update

    def hide(self):
        """Hide overlay"""
        self.progressbar.stop()
        self.place_forget()
        self.update_idletasks()  # Force UI update
