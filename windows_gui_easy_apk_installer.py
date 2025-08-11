import os
import subprocess
import sys
import time
import winreg
import webbrowser
import threading
from datetime import datetime
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog, ttk, scrolledtext

# Windows only: check platform
if sys.platform != "win32":
    # Avoid using messagebox before Tk is created on non-Windows, just exit
    print("This app is Windows-only.")
    sys.exit(1)

# --- Global Variables ---
APK_FOLDER_PATH = ""
APK_FILES_CACHED = []
SELECTED_DEVICE = {}  # Using a dictionary to store both serial and model
REGISTRY_PATH = r"Software\AhmadMorningstar\EasyAPKInstaller"

# Install control globals
install_thread = None
installing_lock = threading.Lock()
is_installing = False
current_process = None
skip_event = threading.Event()

# --- GUI Setup (Dark Mode) ---
root = tk.Tk()
root.title("Easy APK Installer - GUI Dark Mode Edition")
root.geometry("900x560")
root.resizable(False, False)

# Dark color palette
BG = "#0f1720"        # very dark blue-gray
PANEL = "#111827"
ACCENT = "#7c3aed"    # purple
FG = "#e6eef8"        # light text
INFO = "#60a5fa"
SUCCESS = "#34d399"
ERROR = "#f87171"
WARNING = "#fbbf24"
BUTTON_BG = "#111827"
BUTTON_ACTIVE = "#1f2937"

style = ttk.Style()
style.theme_use("clam")
style.configure("TFrame", background=BG)
style.configure("TLabel", background=BG, foreground=FG)
style.configure("TButton", background=BUTTON_BG, foreground=FG, relief="flat")
style.map("TButton",
          background=[('active', BUTTON_ACTIVE), ('disabled', '#111827')],
          foreground=[('disabled', '#8b98a8')])

main_frame = ttk.Frame(root, padding=(10,10,10,10))
main_frame.pack(fill=tk.BOTH, expand=True)

# Top controls frame
controls_frame = ttk.Frame(main_frame)
controls_frame.pack(fill=tk.X, pady=(0,8))

# Buttons frame (left)
btn_frame = ttk.Frame(controls_frame)
btn_frame.pack(side=tk.LEFT, anchor="nw")

# Right side: device/folder/summary
info_frame = ttk.Frame(controls_frame)
info_frame.pack(side=tk.RIGHT, anchor="ne")

# Log output (center)
log_text = scrolledtext.ScrolledText(main_frame, wrap=tk.WORD, height=22, width=110, state="disabled",
                                     bg="#0b1220", fg=FG, insertbackground=FG, relief="flat")
log_text.pack(fill=tk.BOTH, expand=False)

# Status bar
status_var = tk.StringVar(value="Ready")
status_label = ttk.Label(main_frame, textvariable=status_var, anchor="w")
status_label.pack(fill=tk.X, pady=(6,0))

# Helper to safely call GUI updates from threads
def gui_call(fn, *args, **kwargs):
    root.after(0, lambda: fn(*args, **kwargs))

# Logging - thread-safe via gui_call
def log_message_ui(message, level="INFO"):
    """Direct GUI update; must be called from main thread."""
    colors = {
        "INFO": INFO,
        "SUCCESS": SUCCESS,
        "ERROR": ERROR,
        "WARNING": WARNING
    }
    tag = level
    log_text.configure(state="normal")
    # Timestamp for readability
    ts = datetime.now().strftime("%H:%M:%S")
    log_text.insert(tk.END, f"[{ts}] [{level}] {message}\n", tag)
    log_text.tag_config(tag, foreground=colors.get(level, FG))
    log_text.configure(state="disabled")
    log_text.see(tk.END)

def log_message(message, level="INFO"):
    """Thread-safe logging entry."""
    gui_call(log_message_ui, message, level)

def set_status(text):
    gui_call(status_var.set, text)

def set_buttons_state(state=True):
    """Enable or disable action buttons while installing."""
    def apply_state():
        state_str = "normal" if state else "disabled"
        for b in action_buttons.values():
            b.config(state=state_str)
        # skip button should be enabled only when installing
        skip_btn.config(state=("normal" if not state else "disabled") if state else "disabled")
        # but we want Skip enabled only when installing; handled elsewhere
    gui_call(apply_state)

# --- Registry functions ---
def save_path_to_registry(path):
    try:
        key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, REGISTRY_PATH)
        winreg.SetValueEx(key, "LastFolderPath", 0, winreg.REG_SZ, path)
        winreg.CloseKey(key)
        log_message(f"Saved folder to registry: {path}", "INFO")
    except Exception as e:
        log_message(f"Failed to save folder path to registry: {e}", "ERROR")

def load_path_from_registry():
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, REGISTRY_PATH)
        path, _ = winreg.QueryValueEx(key, "LastFolderPath")
        winreg.CloseKey(key)
        return path
    except FileNotFoundError:
        return ""
    except Exception as e:
        log_message(f"Failed to load folder path from registry: {e}", "ERROR")
        return ""

# --- ADB Helpers (unchanged behavior) ---
def check_adb_path():
    try:
        subprocess.run(['adb', 'version'], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

def get_devices():
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
                            model = part.split(':',1)[1]
                            break
                    devices.append({'serial': serial, 'model': model})
        return devices
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None

def scan_for_apks():
    global APK_FILES_CACHED
    APK_FILES_CACHED = []
    if APK_FOLDER_PATH and os.path.isdir(APK_FOLDER_PATH):
        try:
            APK_FILES_CACHED = sorted([f for f in os.listdir(APK_FOLDER_PATH) if f.endswith('.apk')])
            log_message(f"Found {len(APK_FILES_CACHED)} APK(s) in folder.", "INFO")
        except FileNotFoundError:
            APK_FILES_CACHED = []

# --- GUI Actions (adapted) ---
def select_device():
    global SELECTED_DEVICE
    devices = get_devices()
    if devices is None:
        messagebox.showwarning("Error", "'adb' not found or returned error. Ensure adb is in PATH.")
        return
    if not devices:
        messagebox.showwarning("No Devices", "No ADB devices found. Please connect a device and enable USB debugging.")
        return
    if len(devices) == 1:
        SELECTED_DEVICE = devices[0]
        log_message(f"Only one device found. Selected {SELECTED_DEVICE['model']} ({SELECTED_DEVICE['serial']})", "SUCCESS")
        update_info_panel()
        return
    # Build simple selection dialog
    device_names = [f"{d['model']} ({d['serial']})" for d in devices]
    prompt = "Available Devices:\n" + "\n".join(f"{i+1}. {name}" for i, name in enumerate(device_names))
    choice = simpledialog.askinteger("Select Device", prompt, minvalue=1, maxvalue=len(device_names))
    if choice:
        SELECTED_DEVICE = devices[choice - 1]
        log_message(f"Selected device: {SELECTED_DEVICE['model']} ({SELECTED_DEVICE['serial']})", "SUCCESS")
        update_info_panel()

def set_apk_folder():
    global APK_FOLDER_PATH
    path = filedialog.askdirectory(title="Select APK Folder")
    if path:
        APK_FOLDER_PATH = path
        save_path_to_registry(path)
        scan_for_apks()
        update_info_panel()
        log_message(f"Folder path set: {path}", "INFO")

def start_bulk_install():
    global install_thread
    if not SELECTED_DEVICE:
        messagebox.showerror("Error", "Please select a device first.")
        return
    if not APK_FOLDER_PATH:
        messagebox.showerror("Error", "Please set the APK folder first.")
        return
    scan_for_apks()
    if not APK_FILES_CACHED:
        messagebox.showwarning("No APKs", "No APK files found in the specified folder.")
        return
    # Ask about granting permissions
    grant = messagebox.askyesno("Grant Permissions", "Do you want to force-install and grant all permissions (-g)?")
    # Start install thread
    if not acquire_install_lock():
        messagebox.showinfo("Installing", "An installation is already in progress. Please wait or use Skip.")
        return
    skip_event.clear()
    install_thread = threading.Thread(target=install_apks_for_device, args=(SELECTED_DEVICE['serial'], APK_FOLDER_PATH, APK_FILES_CACHED, True, grant), daemon=True)
    install_thread.start()

def install_single_apk():
    global install_thread
    if not SELECTED_DEVICE:
        messagebox.showerror("Error", "Please select a device first.")
        return
    if not APK_FOLDER_PATH:
        messagebox.showerror("Error", "Please set the APK folder first.")
        return
    scan_for_apks()
    if not APK_FILES_CACHED:
        messagebox.showwarning("No APKs", "No APK files found in the specified folder.")
        return
    # Prompt for an APK index
    prompt = "Available APKs:\n" + "\n".join(f"{i+1}. {apk}" for i, apk in enumerate(APK_FILES_CACHED))
    choice = simpledialog.askinteger("Select APK", prompt, minvalue=1, maxvalue=len(APK_FILES_CACHED))
    if not choice:
        return
    apk = APK_FILES_CACHED[choice - 1]
    grant = messagebox.askyesno("Grant Permissions", "Do you want to force-install and grant all permissions (-g) for this APK?")
    if not acquire_install_lock():
        messagebox.showinfo("Installing", "An installation is already in progress. Please wait or use Skip.")
        return
    skip_event.clear()
    install_thread = threading.Thread(target=install_apks_for_device, args=(SELECTED_DEVICE['serial'], APK_FOLDER_PATH, [apk], True, grant), daemon=True)
    install_thread.start()

def show_detailed_device_info():
    if not SELECTED_DEVICE:
        messagebox.showerror("Error", "No device selected. Please select a device first.")
        return
    
    serial = SELECTED_DEVICE['serial']
    
    # We'll gather info and store formatted text
    try:
        manuf = subprocess.run(
            ['adb', '-s', serial, 'shell', 'getprop', 'ro.product.manufacturer'],
            capture_output=True, text=True, check=True, timeout=10).stdout.strip()
        model = subprocess.run(
            ['adb', '-s', serial, 'shell', 'getprop', 'ro.product.model'],
            capture_output=True, text=True, check=True, timeout=10).stdout.strip()
        build_id = subprocess.run(
            ['adb', '-s', serial, 'shell', 'getprop', 'ro.build.display.id'],
            capture_output=True, text=True, check=True, timeout=10).stdout.strip()

        meminfo_output = subprocess.run(
            ['adb', '-s', serial, 'shell', 'cat', '/proc/meminfo'],
            capture_output=True, text=True, check=True, timeout=10).stdout
        ram_total = "N/A"
        for line in meminfo_output.splitlines():
            if 'MemTotal:' in line:
                ram_kb = int(''.join(filter(str.isdigit, line)))
                ram_gb = ram_kb / 1024 / 1024
                ram_total = f"{ram_gb:.2f} GB"
                break

        df_output = subprocess.run(
            ['adb', '-s', serial, 'shell', 'df', '-h', '/data'],
            capture_output=True, text=True, check=True, timeout=10).stdout.splitlines()
        storage_info = "N/A"
        if len(df_output) > 1:
            storage_info = df_output[1].split()[1]  # size of data partition

        cpu_output = subprocess.run(
            ['adb', '-s', serial, 'shell', 'cat', '/proc/cpuinfo'],
            capture_output=True, text=True, check=True, timeout=10).stdout
        cpu_model = "N/A"
        for line in cpu_output.splitlines():
            if 'Hardware' in line:
                cpu_model = line.split(':')[-1].strip()
                break

        gpu_info = "N/A (Complex to fetch via adb)"

    except Exception as e:
        messagebox.showerror("Error", f"Failed to fetch detailed device info:\n{e}")
        return

    # Create modal popup window
    detail_win = tk.Toplevel(root)
    detail_win.title(f"Detailed Info: {model} ({serial})")
    detail_win.geometry("500x400")
    detail_win.configure(bg=BG)
    detail_win.transient(root)
    detail_win.grab_set()

    # Text widget for info
    txt = tk.Text(detail_win, bg="#0b1220", fg=FG, insertbackground=FG, wrap="word", relief="flat")
    txt.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    # Insert colored formatted text
    # Define colors consistent with your log colors:
    yellow = "#fbbf24"
    cyan = "#60a5fa"
    green = "#34d399"
    red = "#f87171"

    def insert_label_value(label, value):
        txt.insert(tk.END, f"  ")
        txt.insert(tk.END, f"{label}: ", ('label',))
        txt.insert(tk.END, f"{value}\n", ('value',))

    # Configure tags for colors
    txt.tag_config("label", foreground=yellow, font=("Segoe UI", 10, "bold"))
    txt.tag_config("value", foreground=FG, font=("Segoe UI", 10))
    txt.tag_config("title", foreground=cyan, font=("Segoe UI", 12, "bold"))

    # Insert title
    txt.insert(tk.END, f"--- Device Information for '{serial}' ---\n\n", 'title')

    # Insert all info
    insert_label_value("Company Name", manuf)
    insert_label_value("Model Name", model)
    insert_label_value("Serial Number", serial)
    insert_label_value("Build Number", build_id)
    insert_label_value("RAM", ram_total)
    insert_label_value("Storage", storage_info)
    insert_label_value("CPU", cpu_model)
    insert_label_value("GPU", gpu_info)

    txt.insert(tk.END, "\nPress Close to return.", ('value',))

    # Disable editing
    txt.config(state="disabled")

    # Close button
    btn_close = ttk.Button(detail_win, text="Close", command=detail_win.destroy)
    btn_close.pack(pady=(0,10))

    # Center window relative to root
    root_x = root.winfo_rootx()
    root_y = root.winfo_rooty()
    root_w = root.winfo_width()
    root_h = root.winfo_height()
    detail_win.update_idletasks()
    w = detail_win.winfo_width()
    h = detail_win.winfo_height()
    x = root_x + (root_w - w) // 2
    y = root_y + (root_h - h) // 2
    detail_win.geometry(f"+{x}+{y}")


def open_about():
    about_win = tk.Toplevel(root)
    about_win.title("About Easy APK Installer")
    about_win.geometry("400x200")
    about_win.resizable(False, False)
    about_win.configure(bg=BG)
    about_win.transient(root)
    about_win.grab_set()

    # Center the window on root
    root_x = root.winfo_rootx()
    root_y = root.winfo_rooty()
    root_w = root.winfo_width()
    root_h = root.winfo_height()
    about_win.update_idletasks()
    w = about_win.winfo_width()
    h = about_win.winfo_height()
    x = root_x + (root_w - w) // 2
    y = root_y + (root_h - h) // 2
    about_win.geometry(f"+{x}+{y}")

    # Title Label
    title_lbl = tk.Label(about_win, text="Easy APK Installer", bg=BG, fg=ACCENT,
                         font=("Segoe UI", 18, "bold"))
    title_lbl.pack(pady=(20, 5))

    # Author Label
    author_lbl = tk.Label(about_win, text="By Ahmad Morningstar", bg=BG, fg=FG,
                          font=("Segoe UI", 12))
    author_lbl.pack(pady=5)

    # Version/Edition Label
    edition_lbl = tk.Label(about_win, text="GUI Dark Mode Edition", bg=BG, fg=INFO,
                           font=("Segoe UI", 10, "italic"))
    edition_lbl.pack(pady=5)

    # Close Button
    close_btn = ttk.Button(about_win, text="Close", command=about_win.destroy)
    close_btn.pack(pady=15)

    # Optional: Add subtle border or shadow by tweaking styles or using frames if you want


def open_youtube():
    webbrowser.open("https://www.youtube.com/@AhmadMorningstar")

def skip_current_install():
    """Sets event and terminates the current adb process if running."""
    if not is_installing:
        log_message("No installation is currently running to skip.", "WARNING")
        return
    skip_event.set()
    log_message("Skip requested. Attempting to stop current install...", "WARNING")
    # Try to terminate current_process if present
    try:
        global current_process
        if current_process and current_process.poll() is None:
            current_process.terminate()
    except Exception as e:
        log_message(f"Failed to terminate process: {e}", "ERROR")

# --- Install logic with GUI-safe logging & skip support ---
def acquire_install_lock():
    """Try to acquire the installing lock and disable UI buttons if successful."""
    acquired = installing_lock.acquire(blocking=False)
    if acquired:
        gui_call(start_install_ui_state)
    return acquired

def release_install_lock():
    """Release lock and re-enable buttons."""
    try:
        installing_lock.release()
    except RuntimeError:
        pass
    gui_call(end_install_ui_state)

def start_install_ui_state():
    """Disable action buttons and enable skip button; update status."""
    global is_installing
    is_installing = True
    for b in action_buttons.values():
        b.config(state="disabled")
    skip_btn.config(state="normal")
    set_status("Installing... (Use 'Skip Current Install' to skip current APK)")

def end_install_ui_state():
    """Enable action buttons, disable skip; update status."""
    global is_installing
    is_installing = False
    for b in action_buttons.values():
        b.config(state="normal")
    skip_btn.config(state="disabled")
    set_status("Ready")

def install_apks_for_device(device_serial, folder_path, apks_to_install, allow_skip=True, grant_permissions=False):
    """
    Core installer loop adapted from original script but GUI-safe and with skip support.
    """
    global current_process
    success_count = 0
    failure_count = 0
    skipped_count = 0

    log_message(f"--- Starting installation for device: {device_serial} ---", "INFO")

    if not apks_to_install:
        log_message("No APK files provided for installation.", "WARNING")
        release_install_lock()
        return

    try:
        for i, apk_file in enumerate(apks_to_install):
            if skip_event.is_set():
                # If a global skip before starting next apk, treat as skipped
                skipped_count += 1
                log_message(f"Skipped (pre): {apk_file}", "WARNING")
                continue

            apk_full_path = os.path.join(folder_path, apk_file)
            log_message(f"[{i+1}/{len(apks_to_install)}] Installing '{apk_file}'...", "INFO")
            # Build adb command
            command = ['adb', '-s', device_serial, 'install', '-r']
            if grant_permissions:
                command.append('-g')
            command.append(apk_full_path)

            try:
                # Use Popen so we can terminate if skip requested
                current_process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                # Poll loop similar to original, but with skip event check
                while True:
                    if skip_event.is_set():
                        try:
                            current_process.terminate()
                            log_message(f"Terminated install process for '{apk_file}' due to skip.", "WARNING")
                        except Exception as e:
                            log_message(f"Error terminating process: {e}", "ERROR")
                        skipped_count += 1
                        break
                    if current_process.poll() is not None:
                        break
                    time.sleep(0.1)

                # After process finishes or was terminated
                stdout, stderr = current_process.communicate(timeout=5)
                ret = current_process.returncode

                if skip_event.is_set() and ret != 0:
                    # we already counted skipped_count above; just continue
                    log_message(f"Skipped: {apk_file}", "WARNING")
                    # clear the skip_event if user wants to skip only the current apk (we keep it cleared so next apk installs normally)
                    skip_event.clear()
                    continue

                if ret == 0 and "Success" in (stdout + stderr):
                    log_message(f"-> SUCCESS: {apk_file} installed successfully.", "SUCCESS")
                    success_count += 1
                else:
                    # On some adb versions, ret==0 but no "Success", follow original logic
                    if ret == 0:
                        log_message(f"-> FAILED: {apk_file} failed to install. (No 'Success' message found)", "ERROR")
                    else:
                        log_message(f"-> FAILED: {apk_file} failed with return code {ret}.", "ERROR")
                    if stdout:
                        log_message(f"  STDOUT: {stdout.strip()}", "INFO")
                    if stderr:
                        log_message(f"  STDERR: {stderr.strip()}", "ERROR")
                    failure_count += 1

            except subprocess.TimeoutExpired:
                log_message(f"Process timeout for {apk_file}.", "ERROR")
                failure_count += 1
            except FileNotFoundError:
                log_message("Error: 'adb' command not found during install. Ensure adb is in PATH.", "ERROR")
                failure_count += 1
            except Exception as e:
                log_message(f"Unexpected error installing {apk_file}: {e}", "ERROR")
                failure_count += 1
            finally:
                current_process = None

        # Summary
        log_message(f"\nInstallation for device '{device_serial}' complete.", "INFO")
        log_message(f"Summary: {success_count} successful, {failure_count} failed, {skipped_count} skipped.", "INFO")
        set_status("Install completed.")
    finally:
        # Always release lock and reset skip_event
        skip_event.clear()
        release_install_lock()

# --- UI Widgets and Buttons ---
# Info panel labels
device_var = tk.StringVar(value="Device: Not Selected")
folder_var = tk.StringVar(value="Folder: Not Set")
apk_count_var = tk.StringVar(value="APKs found: 0")

def update_info_panel():
    device_display = "Not Selected"
    if SELECTED_DEVICE:
        device_display = f"{SELECTED_DEVICE.get('model','Unknown')} ({SELECTED_DEVICE.get('serial','')})"
    device_var.set(f"Device: {device_display}")
    folder_display = APK_FOLDER_PATH if APK_FOLDER_PATH else "Not Set"
    folder_var.set(f"Folder: {folder_display}")
    apk_count_var.set(f"APKs found: {len(APK_FILES_CACHED)}")

lbl_device = ttk.Label(info_frame, textvariable=device_var, font=("Segoe UI", 10))
lbl_device.pack(anchor="e")
lbl_folder = ttk.Label(info_frame, textvariable=folder_var, font=("Segoe UI", 10))
lbl_folder.pack(anchor="e")
lbl_count = ttk.Label(info_frame, textvariable=apk_count_var, font=("Segoe UI", 10))
lbl_count.pack(anchor="e")

# Action buttons (left)
action_buttons = {}
buttons = [
    ("Select Device", select_device),
    ("Set APK Folder", set_apk_folder),
    ("Start Bulk Install", start_bulk_install),
    ("Install Single APK", install_single_apk),
    ("Show Device Info", show_detailed_device_info),
    ("About", open_about),
    ("YouTube Guide", open_youtube),
    ("Exit", root.destroy)
]

for i, (text, cmd) in enumerate(buttons):
    b = tk.Button(btn_frame, text=text, width=20, command=cmd, bg=BUTTON_BG, fg=FG, activebackground=BUTTON_ACTIVE, relief="flat")
    b.grid(row=i//2, column=i%2, padx=6, pady=6, sticky="w")
    action_buttons[text] = b

# Skip button (prominent, red)
skip_btn = tk.Button(btn_frame, text="Skip Current Install", width=42, command=skip_current_install,
                     bg="#7f1d1d", fg=FG, activebackground="#991b1b", relief="raised", state="disabled")
skip_btn.grid(row=4, column=0, columnspan=2, padx=6, pady=(10,4), sticky="w")

# Initialize info
APK_FOLDER_PATH = load_path_from_registry()
scan_for_apks()
update_info_panel()

# Check adb path at start
if not check_adb_path():
    # Show error and still open GUI but disable install related buttons
    log_message("Error: 'adb' command not found. Please install Platform-Tools and add adb to PATH.", "ERROR")
    for name in ("Start Bulk Install", "Install Single APK", "Select Device", "Show Device Info"):
        if name in action_buttons:
            action_buttons[name].config(state="disabled")
    set_status("ADB not found. Install platform-tools and add to PATH.")

# Start the Tk main loop
root.mainloop()
