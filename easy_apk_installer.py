import os
import subprocess
import sys
from datetime import datetime
import multiprocessing
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
import threading
import queue
import ctypes  # Import ctypes for DPI awareness

# This is the crucial step for DPI awareness on Windows.
# It should be called before creating any Tkinter widgets.
try:
    # Set the process to be DPI aware, so Windows doesn't scale it.
    ctypes.windll.shcore.SetProcessDpiAwareness(1)
except AttributeError:
    # This might fail on non-Windows systems, which is fine.
    pass

# For color-coded terminal output (we'll adapt this for the GUI)
from colorama import Fore, Style, init

# Initialize colorama for Windows terminal support
init(autoreset=True)

# --- Global Variables ---
LAST_PATH_FILE = "last_path.txt"
DEFAULT_FONT_SIZE = 12

class ADBInstallerApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Easy APK Installer")

        # Set an initial large window size and state for better high-DPI handling
        self.geometry("1200x800")
        self.state('zoomed')
        
        self.apk_folder_path = ""
        self.selected_devices = []
        self.device_options = {}
        self.log_queue = queue.Queue()
        self.processes = []
        
        # Check for ADB on startup
        if not self.check_adb_path():
            messagebox.showerror("Error", "The 'adb' command was not found. Please ensure the Android SDK Platform-Tools are installed and in your system's PATH.")
            self.destroy()
            return
        
        self.load_last_path()
        self.create_widgets()
        self.refresh_devices()
        self.after(100, self.process_log_queue)

    def create_widgets(self):
        """Sets up all the GUI components."""
        
        # Main header frame
        header_frame = tk.Frame(self, pady=10)
        header_frame.pack(fill="x")
        title_label = tk.Label(header_frame, text="Easy APK Installer Menu", font=("Arial", DEFAULT_FONT_SIZE + 4, "bold"))
        title_label.pack()
        author_label = tk.Label(header_frame, text="By Ahmad Morningstar", font=("Arial", DEFAULT_FONT_SIZE, "italic"))
        author_label.pack()
        
        # Settings frame
        settings_frame = tk.LabelFrame(self, text="Current Settings", padx=10, pady=10, font=("Arial", DEFAULT_FONT_SIZE))
        settings_frame.pack(fill="x", padx=10, pady=5)
        
        self.device_label_var = tk.StringVar(value="Device: Not Selected")
        self.device_label = tk.Label(settings_frame, textvariable=self.device_label_var, anchor="w", justify="left", font=("Arial", DEFAULT_FONT_SIZE))
        self.device_label.pack(fill="x")
        
        self.folder_label_var = tk.StringVar(value=f"Folder: {self.apk_folder_path if self.apk_folder_path else 'Not Set'}")
        self.folder_label = tk.Label(settings_frame, textvariable=self.folder_label_var, anchor="w", justify="left", font=("Arial", DEFAULT_FONT_SIZE))
        self.folder_label.pack(fill="x")
        
        # Control buttons frame
        control_frame = tk.Frame(self, pady=10)
        control_frame.pack(fill="x", padx=10)
        
        tk.Button(control_frame, text="Select Devices", command=self.select_device_menu, font=("Arial", DEFAULT_FONT_SIZE)).pack(side="left", padx=5, fill="x", expand=True)
        tk.Button(control_frame, text="Set APK Folder", command=self.set_folder_path_menu, font=("Arial", DEFAULT_FONT_SIZE)).pack(side="left", padx=5, fill="x", expand=True)
        tk.Button(control_frame, text="Start Installation", command=self.start_installation_processes, font=("Arial", DEFAULT_FONT_SIZE)).pack(side="left", padx=5, fill="x", expand=True)
        tk.Button(control_frame, text="About", command=self.show_about_menu, font=("Arial", DEFAULT_FONT_SIZE)).pack(side="left", padx=5, fill="x", expand=True)
        tk.Button(control_frame, text="Exit", command=self.destroy, font=("Arial", DEFAULT_FONT_SIZE)).pack(side="left", padx=5, fill="x", expand=True)

        # Log text area
        self.log_text = scrolledtext.ScrolledText(self, state='disabled', wrap='word', font=("Courier", DEFAULT_FONT_SIZE), height=20)
        self.log_text.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Tag colors for log messages
        self.log_text.tag_config("SUCCESS", foreground="green")
        self.log_text.tag_config("ERROR", foreground="red")
        self.log_text.tag_config("WARNING", foreground="orange")
        self.log_text.tag_config("INFO", foreground="blue")
        self.log_text.tag_config("HEADER", foreground="purple", font=("Arial", DEFAULT_FONT_SIZE + 2, "bold"))

    def check_adb_path(self):
        """Checks if 'adb' command is available in the system's PATH."""
        try:
            subprocess.run(['adb', 'version'], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False

    def load_last_path(self):
        """Loads the last used folder path from a file."""
        if os.path.exists(LAST_PATH_FILE):
            with open(LAST_PATH_FILE, "r", encoding="utf-8") as f:
                path = f.read().strip()
                if os.path.isdir(path):
                    self.apk_folder_path = path

    def save_last_path(self, path):
        """Saves the current folder path to a file."""
        with open(LAST_PATH_FILE, "w", encoding="utf-8") as f:
            f.write(path)
            
    def log_message(self, message, level="INFO"):
        """Inserts a message into the log text area with color tags."""
        self.log_text.configure(state='normal')
        self.log_text.insert(tk.END, f"[{datetime.now().strftime('%H:%M:%S')}] {message}\n", level)
        self.log_text.see(tk.END)
        self.log_text.configure(state='disabled')
    
    def log_to_queue(self, message, level="INFO"):
        """Puts a message in the queue to be processed by the main thread."""
        self.log_queue.put((message, level))

    def process_log_queue(self):
        """Periodically checks the queue and updates the GUI."""
        while not self.log_queue.empty():
            message, level = self.log_queue.get()
            self.log_message(message, level)
        self.after(100, self.process_log_queue)

    def refresh_devices(self):
        """Finds connected devices and updates the device selection list."""
        devices = self.get_devices()
        if devices is None:
            self.log_message("Error: 'adb' command not found.", "ERROR")
            self.device_options = {}
            return
        
        self.device_options = {device['serial']: device['model'] for device in devices}
        
        # Auto-select if there is only one device
        if len(devices) == 1:
            self.selected_devices = [devices[0]['serial']]
            self.device_label_var.set(f"Device: {self.selected_devices[0]} (auto-selected)")
            self.log_message(f"Only one device found. Automatically selected '{self.selected_devices[0]}'.", "INFO")
        elif not devices:
            self.selected_devices = []
            self.device_label_var.set("Device: Not Selected")
        else:
            self.device_label_var.set("Device: Click 'Select Devices' to choose.")
            
    def get_devices(self):
        """Returns a list of connected ADB devices and their details."""
        try:
            result = subprocess.run(['adb', 'devices', '-l'], capture_output=True, text=True, check=True)
            lines = result.stdout.strip().split('\n')
            devices = []
            if len(lines) > 1:
                for line in lines[1:]:
                    if line.strip():
                        parts = line.split()
                        serial = parts[0]
                        model = "Unknown"
                        for part in parts:
                            if part.startswith("model:"):
                                model = part.split(':')[1]
                                break
                        devices.append({'serial': serial, 'model': model})
            return devices
        except (subprocess.CalledProcessError, FileNotFoundError):
            return None

    def select_device_menu(self):
        """Handles the device selection menu in a Toplevel window."""
        devices = self.get_devices()
        if not devices:
            messagebox.showinfo("Devices", "No ADB devices found. Please check your connection and USB debugging settings.")
            return

        selection_window = tk.Toplevel(self)
        selection_window.title("Select Devices")
        selection_window.geometry("300x400")
        selection_window.grab_set()
        
        tk.Label(selection_window, text="Available Devices:", font=("Arial", DEFAULT_FONT_SIZE, "bold")).pack(pady=5)

        listbox_frame = tk.Frame(selection_window)
        listbox_frame.pack(fill="both", expand=True, padx=10)

        scrollbar = tk.Scrollbar(listbox_frame)
        scrollbar.pack(side="right", fill="y")
        
        device_listbox = tk.Listbox(listbox_frame, selectmode="extended", yscrollcommand=scrollbar.set, font=("Arial", DEFAULT_FONT_SIZE))
        device_listbox.pack(fill="both", expand=True)
        scrollbar.config(command=device_listbox.yview)

        for i, device in enumerate(devices):
            device_listbox.insert(tk.END, f"{device['serial']} ({device['model']})")
        
        def save_selection():
            selected_indices = device_listbox.curselection()
            self.selected_devices = [devices[i]['serial'] for i in selected_indices]
            if self.selected_devices:
                self.device_label_var.set(f"Devices: {', '.join(self.selected_devices)}")
            else:
                self.device_label_var.set("Device: Not Selected")
            selection_window.destroy()

        tk.Button(selection_window, text="Confirm", command=save_selection, font=("Arial", DEFAULT_FONT_SIZE)).pack(pady=10)

    def set_folder_path_menu(self):
        """Opens a file dialog to set the APK folder path."""
        path = filedialog.askdirectory(title="Select APK Folder")
        if path:
            self.apk_folder_path = path
            self.save_last_path(path)
            self.folder_label_var.set(f"Folder: {self.apk_folder_path}")
            self.log_message(f"Folder path set to: '{path}'", "INFO")

    def show_about_menu(self):
        """Displays information about the author and the program."""
        about_window = tk.Toplevel(self)
        about_window.title("About")
        about_window.geometry("400x300")
        about_window.grab_set()  # Make it a modal window
        
        about_text = (
            "About the Author\n"
            "This is a simple yet powerful command-line utility for "
            "installing multiple APK files on one or more Android "
            "devices simultaneously using ADB.\n\n"
            "Author: Ahmad Morningstar\n\n"
            "Links:\n"
            "  GitHub:    https://github.com/AhmadMorningstar\n"
            "  YouTube:   https://youtube.com/AhmadMorningstar\n"
        )
        tk.Label(about_window, text=about_text, justify="left", wraplength=350, padx=10, pady=10, font=("Arial", DEFAULT_FONT_SIZE)).pack()

    def install_apks_for_device(self, device_serial, folder_path):
        """
        Installs all APK files for a single device.
        This function is run in a separate process.
        """
        self.log_to_queue(f"--- ADB Installation Log for {device_serial} ---", "HEADER")
        self.log_to_queue(f"Selected Device: {device_serial}", "INFO")
        self.log_to_queue(f"APK Folder: {folder_path}", "INFO")
        
        try:
            apk_files = [f for f in os.listdir(folder_path) if f.endswith('.apk')]
        except FileNotFoundError:
            self.log_to_queue(f"Error: The folder '{folder_path}' was not found.", "ERROR")
            return

        if not apk_files:
            self.log_to_queue(f"No APK files found in the specified folder for device {device_serial}.", "WARNING")
            return
            
        self.log_to_queue(f"Total APKs to install: {len(apk_files)}\n", "INFO")
        
        for i, apk_file in enumerate(apk_files):
            apk_full_path = os.path.join(folder_path, apk_file)
            self.log_to_queue(f"[{i+1}/{len(apk_files)}] Attempting to install on device '{device_serial}': {apk_file}...", "INFO")
            
            try:
                result = subprocess.run(
                    ['adb', '-s', device_serial, 'install', '-r', apk_full_path],
                    capture_output=True,
                    text=True,
                    check=True,
                    timeout=300
                )
                self.log_to_queue(f"-> SUCCESS: {apk_file} installed successfully.", "SUCCESS")
            except subprocess.CalledProcessError as e:
                error_output = e.stderr.strip() or e.stdout.strip()
                self.log_to_queue(f"-> FAILED: {apk_file} failed to install.", "ERROR")
                if "INSTALL_FAILED_VERIFICATION_FAILURE" in error_output:
                    error_message = "Verification Failure. Try disabling Google Play Protect."
                elif "INSTALL_FAILED_INSUFFICIENT_STORAGE" in error_output:
                    error_message = "Insufficient Storage. Device does not have enough free space."
                else:
                    error_message = error_output
                self.log_to_queue(f"   Error details: {error_message}", "ERROR")
            except subprocess.TimeoutExpired:
                self.log_to_queue(f"-> FAILED: Installation of {apk_file} timed out.", "ERROR")
        
        self.log_to_queue(f"\nInstallation process for device '{device_serial}' completed.", "INFO")

    def start_installation_processes(self):
        """Starts the installation process on all selected devices."""
        if not self.selected_devices or not self.apk_folder_path:
            messagebox.showerror("Error", "Please select at least one device and set the APK folder path.")
            return

        # Clear previous log output
        self.log_text.configure(state='normal')
        self.log_text.delete(1.0, tk.END)
        self.log_text.configure(state='disabled')
        
        self.log_message("Starting multi-device installation in separate processes...")
        
        for device in self.selected_devices:
            # Create a new process for each device
            p = multiprocessing.Process(target=self.install_apks_for_device, args=(device, self.apk_folder_path))
            self.processes.append(p)
            p.start()
        
        # A thread to monitor the child processes and the queue
        monitor_thread = threading.Thread(target=self.monitor_processes, daemon=True)
        monitor_thread.start()

    def monitor_processes(self):
        """Monitors the installation processes and logs their completion."""
        for p in self.processes:
            p.join()
        
        self.log_to_queue("\nAll installation processes have completed.", "INFO")
        self.processes = []

if __name__ == "__main__":
    app = ADBInstallerApp()
    if 'app' in locals():
        app.mainloop()
