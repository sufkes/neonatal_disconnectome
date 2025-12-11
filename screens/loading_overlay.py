import customtkinter as ctk


class LoadingOverlay(ctk.CTkFrame):
    """Themed loading overlay that adapts to current theme"""

    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)

        # Configure overlay with semi-transparent backdrop
        # Don't call _update_overlay_colors yet - widgets don't exist!
        self._set_initial_overlay_color()

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
        )
        self.status_label.grid(row=1, column=0)

        # Detail label for substep info
        self.detail_label = ctk.CTkLabel(
            self.content_frame, text="", font=ctk.CTkFont(size=11)
        )
        self.detail_label.grid(row=2, column=0, pady=(5, 0))

        # Progress percentage label
        self.progress_label = ctk.CTkLabel(
            self.content_frame, text="", font=ctk.CTkFont(size=12)
        )
        self.progress_label.grid(row=3, column=0, pady=(5, 0))

        # NOW update colors after all widgets are created
        self._update_overlay_colors()

        self.progressbar.stop()
        self.hide()

    def _set_initial_overlay_color(self):
        """Set just the overlay background color initially"""
        appearance_mode = ctk.get_appearance_mode()
        is_dark = appearance_mode == "Dark"

        # Semi-transparent overlay - darker version of background
        if is_dark:
            overlay_color = "#1A1A1A"  # Very dark gray for dark mode
        else:
            overlay_color = "#E0E0E0"  # Light gray for light mode

        self.configure(fg_color=overlay_color)

    def _update_overlay_colors(self):
        """Update overlay colors based on current theme and appearance mode"""
        theme = ctk.ThemeManager.theme
        appearance_mode = ctk.get_appearance_mode()
        is_dark = appearance_mode == "Dark"

        # Get base background color from theme
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

        # Semi-transparent overlay - darker version of background
        if is_dark:
            overlay_color = "#1A1A1A"  # Very dark gray for dark mode
        else:
            overlay_color = "#E0E0E0"  # Light gray for light mode

        self.configure(fg_color=overlay_color)

        # Update label colors to match theme
        text_color = get_color("CTkLabel", "text_color", "#000000", "#FFFFFF")

        # Only configure if labels exist
        if hasattr(self, "status_label"):
            self.status_label.configure(text_color=text_color)

        # Detail and progress labels slightly dimmed
        if is_dark:
            detail_color = "#CCCCCC"
            progress_color = "#AAAAAA"
        else:
            detail_color = "#666666"
            progress_color = "#888888"

        if hasattr(self, "detail_label"):
            self.detail_label.configure(text_color=detail_color)
        if hasattr(self, "progress_label"):
            self.progress_label.configure(text_color=progress_color)

    def show(self, status="Processing...", detail=""):
        """Show overlay with optional status message"""
        self._update_overlay_colors()  # Update colors before showing
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

    def update_theme(self):
        """Update overlay theme colors"""
        self._update_overlay_colors()

    def hide(self):
        """Hide overlay"""
        self.progressbar.stop()
        self.place_forget()
        self.update_idletasks()  # Force UI update
