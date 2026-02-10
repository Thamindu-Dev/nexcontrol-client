import os
import sys
import threading
import subprocess
import signal
import time
import webbrowser
import logging
import customtkinter as ctk
from PIL import Image
from datetime import datetime

# Configure logging for GUI
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("NexControlGUI")

# Constants
SERVER_HOST = "0.0.0.0"
SERVER_PORT = 8000
DASHBOARD_URL = f"http://localhost:{SERVER_PORT}"
LOG_FILE = "nexcontrol.log"

class NexControlServerGUI(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Window Config
        self.title("NexControl Server Manager")
        self.geometry("800x600")
        self.minsize(600, 480)
        
        # Set Theme
        ctk.set_appearance_mode("Dark")
        ctk.set_default_color_theme("blue")
        
        # State
        self.server_process = None
        self.is_running = False
        
        # UI Layout
        self._create_sidebar()
        self._create_main_content()
        self._create_log_area()
        
        # Start log reader thread
        self.running = True
        self.log_thread = threading.Thread(target=self._read_logs, daemon=True)
        self.log_thread.start()
        
        # Handle close
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _create_sidebar(self):
        self.sidebar = ctk.CTkFrame(self, width=200, corner_radius=0)
        self.sidebar.pack(side="left", fill="y", padx=0, pady=0)
        
        # Title
        self.logo_label = ctk.CTkLabel(
            self.sidebar, 
            text="NexControl", 
            font=ctk.CTkFont(size=24, weight="bold")
        )
        self.logo_label.pack(padx=20, pady=(20, 10))
        
        # Status Indicator
        self.status_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        self.status_frame.pack(padx=20, pady=10, fill="x")
        
        self.status_indicator = ctk.CTkLabel(
            self.status_frame,
            text="● Stopped",
            text_color="red",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        self.status_indicator.pack(side="left")

        # Buttons
        self.start_btn = ctk.CTkButton(
            self.sidebar,
            text="Start Server",
            command=self.start_server,
            fg_color="green",
            hover_color="darkgreen"
        )
        self.start_btn.pack(padx=20, pady=10, fill="x")
        
        self.stop_btn = ctk.CTkButton(
            self.sidebar,
            text="Stop Server",
            command=self.stop_server,
            fg_color="red",
            hover_color="darkred",
            state="disabled"
        )
        self.stop_btn.pack(padx=20, pady=10, fill="x")
        
        self.open_browser_btn = ctk.CTkButton(
            self.sidebar,
            text="Open Dashboard",
            command=self.open_dashboard,
            state="disabled"
        )
        self.open_browser_btn.pack(padx=20, pady=10, fill="x")
        
        # Spacer
        ctk.CTkLabel(self.sidebar, text="").pack(fill="y", expand=True)
        
        # Settings / Info
        self.settings_btn = ctk.CTkButton(
            self.sidebar,
            text="Setup Environment",
            command=self.open_setup,
            fg_color="gray",
            hover_color="darkgray"
        )
        self.settings_btn.pack(padx=20, pady=20, fill="x")

    def _create_main_content(self):
        self.main_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.main_frame.pack(side="right", fill="both", expand=True, padx=20, pady=20)
        
        # Info Cards
        self.info_grid = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.info_grid.pack(fill="x", pady=(0, 20))
        
        # Connection Info
        self.conn_card = ctk.CTkFrame(self.info_grid)
        self.conn_card.pack(side="left", fill="both", expand=True, padx=(0, 10))
        
        ctk.CTkLabel(self.conn_card, text="Local Address", font=ctk.CTkFont(weight="bold")).pack(pady=(10, 5))
        self.local_ip_lbl = ctk.CTkLabel(self.conn_card, text="Unknown")
        self.local_ip_lbl.pack(pady=(0, 10))
        
        # Port Info
        self.port_card = ctk.CTkFrame(self.info_grid)
        self.port_card.pack(side="left", fill="both", expand=True, padx=(10, 0))
        
        ctk.CTkLabel(self.port_card, text="Port", font=ctk.CTkFont(weight="bold")).pack(pady=(10, 5))
        ctk.CTkLabel(self.port_card, text=str(SERVER_PORT)).pack(pady=(0, 10))
        
        self._update_local_ip()

    def _create_log_area(self):
        # Log Title
        ctk.CTkLabel(self.main_frame, text="Server Logs", anchor="w").pack(fill="x")
        
        # Log Textbox
        self.log_textbox = ctk.CTkTextbox(self.main_frame, font=("Consolas", 12))
        self.log_textbox.pack(fill="both", expand=True, pady=(5, 0))
        self.log_textbox.configure(state="disabled")

    def _update_local_ip(self):
        try:
            import socket
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            self.local_ip_lbl.configure(text=f"http://{ip}:{SERVER_PORT}")
        except:
            self.local_ip_lbl.configure(text="Unavailable")

    def start_server(self):
        if self.server_process:
            return
            
        try:
            # Determine command based on environment (frozen or source)
            if getattr(sys, 'frozen', False):
                # If compiled with PyInstaller
                server_exe = os.path.join(sys._MEIPASS, "main") if hasattr(sys, "_MEIPASS") else "main"
                # This is tricky with uvicorn. Better to run python -m uvicorn or similar.
                # For simplicity in this script, we'll assume we are running the python script typically.
                # If packaged, we might need a different entry point. 
                # Let's assume standard python execution for now or handle subprocess correctly.
                cmd = [sys.executable, "-m", "uvicorn", "main:app", "--host", SERVER_HOST, "--port", str(SERVER_PORT)]
            else:
                # Running from source
                cmd = [sys.executable, "-m", "uvicorn", "main:app", "--host", SERVER_HOST, "--port", str(SERVER_PORT)]

            # working directory should be the backend folder
            cwd = os.path.dirname(os.path.abspath(__file__))
            
            # Start process
            # CREATE_NO_WINDOW = 0x08000000 (Windows only)
            kwargs = {}
            if sys.platform == "win32":
                kwargs["creationflags"] = subprocess.CREATE_NO_WINDOW
                
            self.server_process = subprocess.Popen(
                cmd,
                cwd=cwd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                **kwargs
            )
            
            self.is_running = True
            self._update_ui_state(running=True)
            self.log_message("Server starting...")
            
            # Start thread to read stdout/stderr of the process
            threading.Thread(target=self._monitor_process, daemon=True).start()
            
        except Exception as e:
            self.log_message(f"Failed to start server: {e}")

    def stop_server(self):
        if self.server_process:
            self.log_message("Stopping server...")
            try:
                self.server_process.terminate()
                self.server_process.wait(timeout=5)
            except:
                self.server_process.kill()
            
            self.server_process = None
            self.is_running = False
            self._update_ui_state(running=False)
            self.log_message("Server stopped.")

    def _monitor_process(self):
        """Read stdout/stderr from server process"""
        if not self.server_process:
            return
            
        while self.is_running and self.server_process:
            line = self.server_process.stdout.readline()
            if not line:
                break
            self.log_message(line.strip())
            
        # Process ended
        if self.is_running:
            self.is_running = False
            self.server_process = None
            self.after(0, lambda: self._update_ui_state(running=False))
            self.log_message("Server process terminated unexpectedly.")

    def _update_ui_state(self, running):
        if running:
            self.status_indicator.configure(text="● Running", text_color="green")
            self.start_btn.configure(state="disabled", fg_color="gray")
            self.stop_btn.configure(state="normal", fg_color="red")
            self.open_browser_btn.configure(state="normal")
        else:
            self.status_indicator.configure(text="● Stopped", text_color="red")
            self.start_btn.configure(state="normal", fg_color="green")
            self.stop_btn.configure(state="disabled", fg_color="gray")
            self.open_browser_btn.configure(state="disabled")

    def open_dashboard(self):
        webbrowser.open(DASHBOARD_URL)

    def open_setup(self):
        # Run setup_env.py in a new console
        if sys.platform == "win32":
            subprocess.Popen(["start", "cmd", "/k", "python setup_env.py"], shell=True)
        else:
            self.log_message("Run 'python setup_env.py' in terminal to setup environment.")

    def log_message(self, message):
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted = f"[{timestamp}] {message}\n"
        
        # Schedule GUI update on main thread
        self.after(0, lambda: self._append_log(formatted))

    def _append_log(self, text):
        self.log_textbox.configure(state="normal")
        self.log_textbox.insert("end", text)
        self.log_textbox.see("end")
        self.log_textbox.configure(state="disabled")

    def _read_logs(self):
        """Monitor log file for changes"""
        last_pos = 0
        while self.running:
            if os.path.exists(LOG_FILE):
                try:
                    with open(LOG_FILE, "r") as f:
                        f.seek(0, 2) # End
                        current_pos = f.tell()
                        
                        if current_pos < last_pos:
                            last_pos = 0
                        
                        if current_pos > last_pos:
                            f.seek(last_pos)
                            new_lines = f.read()
                            if new_lines:
                                self.after(0, lambda: self._append_log(new_lines))
                            last_pos = current_pos
                except:
                    pass
            time.sleep(1)

    def _on_close(self):
        self.stop_server()
        self.running = False
        self.destroy()

if __name__ == "__main__":
    app = NexControlServerGUI()
    app.mainloop()
