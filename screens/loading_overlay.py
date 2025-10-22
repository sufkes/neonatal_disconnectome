import customtkinter as ctk

class LoadingOverlay(ctk.CTkFrame):
  def __init__(self, master, **kwargs):
      super().__init__(master, **kwargs)

      # Make overlay cover entire parent, dark backdrop color
      self.place(relx=0, rely=0, relwidth=1, relheight=1)
      self.configure(fg_color="#333333")  # dark gray backdrop

      # Centered indeterminate progress bar
      self.progressbar = ctk.CTkProgressBar(self, mode="indeterminate", width=250, height=20)
      self.progressbar.place(relx=0.5, rely=0.5, anchor="center")

      self.progressbar.stop()
      self.hide()

  def show(self):
      self.lift()  # bring to front
      self.place(relx=0, rely=0, relwidth=1, relheight=1)
      self.progressbar.start()

  def hide(self):
      self.progressbar.stop()
      self.place_forget()
