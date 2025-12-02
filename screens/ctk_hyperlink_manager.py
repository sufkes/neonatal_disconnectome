import customtkinter as ctk


class CTkHyperlinkManager:
    def __init__(self, text_widget, callback):
        self.text_widget = text_widget
        self.callback = callback
        self.links = {}

    def add(self, path):
        tag = f"hyper-{len(self.links)}"
        self.links[tag] = path
        self.text_widget.tag_configure(tag, foreground="#0074d9", underline=True)
        self.text_widget.tag_bind(tag, "<Enter>", self._enter)
        self.text_widget.tag_bind(tag, "<Leave>", self._leave)
        self.text_widget.tag_bind(tag, "<Button-1>", self._click)
        return tag

    def _enter(self, event):
        self.text_widget.configure(cursor="hand2")

    def _leave(self, event):
        self.text_widget.configure(cursor="xterm")

    def _click(self, event):
        for tag in self.text_widget.tag_names(ctk.CURRENT):
            if tag.startswith("hyper-"):
                self.callback(self.links[tag])
                return
