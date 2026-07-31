import customtkinter as ctk
import threading
import time
import sys
import os

# Set appearance and theme
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Facebook AdsPower Checker")
        self.geometry("800x600")
        self.resizable(False, False)

        # Title Label
        self.title_label = ctk.CTkLabel(self, text="Facebook Account Checker", font=ctk.CTkFont(size=24, weight="bold"))
        self.title_label.pack(pady=(20, 10))

        # Status Frame
        self.status_frame = ctk.CTkFrame(self)
        self.status_frame.pack(pady=10, padx=20, fill="x")

        self.status_label = ctk.CTkLabel(self.status_frame, text="Status: Ready", font=ctk.CTkFont(size=14))
        self.status_label.pack(side="left", padx=10, pady=10)

        self.time_label = ctk.CTkLabel(self.status_frame, text="Time: 00:00", font=ctk.CTkFont(size=14))
        self.time_label.pack(side="right", padx=10, pady=10)

        # Progress Frame
        self.progress_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.progress_frame.pack(pady=10, padx=20, fill="x")
        
        self.progress_bar = ctk.CTkProgressBar(self.progress_frame, height=15)
        self.progress_bar.pack(side="left", fill="x", expand=True, padx=(0, 10))
        self.progress_bar.set(0)

        self.progress_label = ctk.CTkLabel(self.progress_frame, text="0 / 0 (0%)", width=100)
        self.progress_label.pack(side="right")

        # Logs Textbox
        self.log_box = ctk.CTkTextbox(self, width=760, height=350, font=("Consolas", 12))
        self.log_box.pack(pady=(10, 20), padx=20)
        self.log_box.configure(state="disabled")

        # Start Button
        self.start_button = ctk.CTkButton(self, text="START CHECK", font=ctk.CTkFont(size=16, weight="bold"), height=40, command=self.start_check)
        self.start_button.pack(pady=(0, 20))

        self.start_time = None
        self.timer_running = False

    def log(self, message):
        """Append a message to the log box safely from any thread."""
        def append_log():
            self.log_box.configure(state="normal")
            self.log_box.insert("end", str(message) + "\n")
            self.log_box.see("end")
            self.log_box.configure(state="disabled")
        self.after(0, append_log)

    def update_progress(self, current, total):
        """Update progress bar safely from any thread."""
        def update():
            if total > 0:
                progress_val = current / total
                self.progress_bar.set(progress_val)
                percent = int(progress_val * 100)
                self.progress_label.configure(text=f"{current} / {total} ({percent}%)")
        self.after(0, update)

    def update_timer(self):
        """Update elapsed time on the UI."""
        if self.timer_running and self.start_time:
            elapsed = int(time.time() - self.start_time)
            mins, secs = divmod(elapsed, 60)
            self.time_label.configure(text=f"Time: {mins:02d}:{secs:02d}")
            self.after(1000, self.update_timer)

    def start_check(self):
        """Start the background check thread."""
        self.start_button.configure(state="disabled", text="RUNNING...")
        self.status_label.configure(text="Status: Checking profiles...")
        self.progress_bar.set(0)
        self.progress_label.configure(text="0 / 0 (0%)")
        
        self.log_box.configure(state="normal")
        self.log_box.delete("0.0", "end")
        self.log_box.configure(state="disabled")

        self.start_time = time.time()
        self.timer_running = True
        self.update_timer()

        thread = threading.Thread(target=self.run_background_process)
        thread.daemon = True
        thread.start()

    def run_background_process(self):
        """The actual process that runs check_fb_bans."""
        try:
            # We import here so that if there are missing dependencies, we can catch it.
            import check_fb_bans
            check_fb_bans.main(log_cb=self.log, prog_cb=self.update_progress)
            self.log("✅ Process completed successfully!")
            self.after(0, lambda: self.status_label.configure(text="Status: Finished"))
        except Exception as e:
            self.log(f"❌ CRITICAL ERROR: {e}")
            self.after(0, lambda: self.status_label.configure(text="Status: Error"))
        finally:
            self.timer_running = False
            self.after(0, lambda: self.start_button.configure(state="normal", text="START CHECK"))

if __name__ == "__main__":
    app = App()
    app.mainloop()
