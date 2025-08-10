import os
import subprocess
import sys
from collections import defaultdict
import time
from datetime import datetime
import multiprocessing

# For non-blocking keyboard input on Windows
import msvcrt
# For color-coded terminal output (install with 'pip install colorama')
from colorama import Fore, Style, init

# Initialize colorama for Windows terminal support
init(autoreset=True)

# --- Global Variables ---
APK_FOLDER_PATH = ""
SELECTED_DEVICES = [] # Changed to a list for multi-device support
LOG_FILE_NAME = ""
LAST_PATH_FILE = "last_path.txt"

def check_adb_path():
    """
    Checks if 'adb' command is available in the system's PATH.
    """
    try:
        # Check if adb is running by getting its version
        subprocess.run(['adb', 'version'], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

def load_last_path():
    """
    Loads the last used folder path from a file.
    """
    global APK_FOLDER_PATH
    if os.path.exists(LAST_PATH_FILE):
        with open(LAST_PATH_FILE, "r", encoding="utf-8") as f:
            path = f.read().strip()
            if os.path.isdir(path):
                APK_FOLDER_PATH = path
                return True
    return False

def save_last_path(path):
    """
    Saves the current folder path to a file.
    """
    with open(LAST_PATH_FILE, "w", encoding="utf-8") as f:
        f.write(path)

def log_message(message, level="INFO", log_file=None):
    """
    Writes a message to the console and the specified log file.
    """
    if log_file:
        try:
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] [{level}] {message}\n")
        except IOError:
            print(f"{Fore.RED}Error: Could not write to log file '{log_file}'.{Style.RESET_ALL}")
    print(message)

def print_menu():
    """
    Prints the main menu.
    """
    os.system('cls' if os.name == 'nt' else 'clear') # Clear the console
    print(f"{Fore.CYAN}{Style.BRIGHT}---------------------------------------")
    print(f"|{Fore.YELLOW}          Easy APK Installer         {Fore.CYAN}|")
    print(f"---------------------------------------{Style.RESET_ALL}")
    print(f"{Fore.MAGENTA}          By Ahmad Morningstar{Style.RESET_ALL}")
    print(f"{Fore.CYAN}---------------------------------------{Style.RESET_ALL}")
    print(f"{Fore.GREEN}1. Select ADB Devices (single or multiple)")
    print(f"{Fore.GREEN}2. Set APK Folder Path")
    print(f"{Fore.GREEN}3. Start Installation{Style.RESET_ALL}")
    print(f"{Fore.GREEN}4. About{Style.RESET_ALL}")
    print(f"{Fore.GREEN}5. Exit{Style.RESET_ALL}")
    print(f"\n{Fore.MAGENTA}Current Settings:{Style.RESET_ALL}")
    print(f"  {Fore.YELLOW}Devices:  {Style.BRIGHT}{', '.join(SELECTED_DEVICES) if SELECTED_DEVICES else 'Not Selected'}{Style.RESET_ALL}")
    print(f"  {Fore.YELLOW}Folder:   {Style.BRIGHT}{APK_FOLDER_PATH if APK_FOLDER_PATH else 'Not Set'}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}---------------------------------------{Style.RESET_ALL}")

def show_about_menu():
    """
    Displays information about the author and the program.
    """
    os.system('cls' if os.name == 'nt' else 'clear')
    print(f"{Fore.CYAN}{Style.BRIGHT}---------------------------------------")
    print(f"|{Fore.YELLOW}          About the Author          {Fore.CYAN}|")
    print(f"---------------------------------------{Style.RESET_ALL}")
    print(f"{Fore.MAGENTA}Author: {Style.BRIGHT}Ahmad Morningstar{Style.RESET_ALL}")
    print(f"\n{Fore.CYAN}Program Description:{Style.RESET_ALL}")
    print(f"This is a simple yet powerful command-line utility for")
    print(f"installing multiple APK files on one or more Android")
    print(f"devices simultaneously using ADB.")
    print(f"\n{Fore.GREEN}Links:{Style.RESET_ALL}")
    print(f"  {Fore.YELLOW}GitHub:    {Style.BRIGHT}https://github.com/AhmadMorningstar{Style.RESET_ALL}")
    #print(f"  {Fore.YELLOW}YouTube:   {Style.BRIGHT}https://youtube.com/AhmadMorningstar{Style.RESET_ALL}")
    print(f"\n{Fore.CYAN}---------------------------------------{Style.RESET_ALL}")
    print(f"{Fore.GREEN}Press any key to return to the menu...{Style.RESET_ALL}")
    msvcrt.getch()

def get_devices():
    """
    Returns a list of connected ADB devices and their details.
    """
    try:
        result = subprocess.run(['adb', 'devices', '-l'], capture_output=True, text=True, check=True)
        lines = result.stdout.strip().split('\n')
        devices = []
        if len(lines) > 1:
            for line in lines[1:]:
                if line.strip():
                    parts = line.split()
                    serial = parts[0]
                    # Attempt to find the model name
                    model = "Unknown"
                    for part in parts:
                        if part.startswith("model:"):
                            model = part.split(':')[1]
                            break
                    devices.append({'serial': serial, 'model': model})
        return devices
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None

def select_device_menu():
    """
    Handles the device selection menu for single or multiple devices.
    """
    global SELECTED_DEVICES
    devices = get_devices()
    if devices is None:
        print(f"{Fore.RED}Error: 'adb' command not found. Please ensure it's installed and in your PATH.{Style.RESET_ALL}")
        msvcrt.getch()
        return

    if not devices:
        print(f"{Fore.YELLOW}No ADB devices found. Please check your connection and USB debugging settings.{Style.RESET_ALL}")
        msvcrt.getch()
        return

    # Auto-select if there is only one device
    if len(devices) == 1:
        SELECTED_DEVICES = [devices[0]['serial']]
        print(f"{Fore.GREEN}Only one device found. Automatically selected device '{SELECTED_DEVICES[0]}'.{Style.RESET_ALL}")
        msvcrt.getch()
        return

    print("\nAvailable Devices:")
    for i, device in enumerate(devices):
        print(f"  {i + 1}. {Fore.CYAN}Serial:{Style.BRIGHT}{device['serial']}{Style.RESET_ALL}, {Fore.CYAN}Model:{Style.BRIGHT}{device['model']}{Style.RESET_ALL}")

    while True:
        try:
            choice = input(f"\n{Fore.GREEN}Enter the numbers of the devices to select (e.g., 1, 3, 4): {Style.RESET_ALL}")
            selected_indices = [int(i.strip()) - 1 for i in choice.split(',')]
            
            # Check for valid indices
            valid_selection = True
            selected_serials = []
            for index in selected_indices:
                if 0 <= index < len(devices):
                    selected_serials.append(devices[index]['serial'])
                else:
                    valid_selection = False
                    break
            
            if valid_selection and selected_serials:
                SELECTED_DEVICES = selected_serials
                print(f"{Fore.GREEN}Selected devices: '{', '.join(SELECTED_DEVICES)}'{Style.RESET_ALL}")
                break
            else:
                print(f"{Fore.RED}Invalid selection. Please enter one or more valid numbers separated by commas.{Style.RESET_ALL}")
        except ValueError:
            print(f"{Fore.RED}Invalid input. Please enter numbers separated by commas.{Style.RESET_ALL}")
    msvcrt.getch()

def set_folder_path_menu():
    """
    Handles the folder path selection menu.
    """
    global APK_FOLDER_PATH
    path = input(f"{Fore.GREEN}Enter the full path to the folder containing your APKs: {Style.RESET_ALL}")
    if os.path.isdir(path):
        APK_FOLDER_PATH = path
        save_last_path(path)
        print(f"{Fore.GREEN}Folder path set to: '{path}'{Style.RESET_ALL}")
    else:
        print(f"{Fore.RED}Error: The provided path does not exist or is not a directory.{Style.RESET_ALL}")
    msvcrt.getch()

def install_apks_for_device(device_serial, folder_path):
    """
    Installs all APK files found in the given folder for a single device.
    This function is designed to be run in a separate process.
    """
    log_file = f"adb_installer_log_{device_serial}_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.log"
    
    log_message(f"--- ADB Installation Log ---", "HEADER", log_file)
    log_message(f"Selected Device: {device_serial}", "INFO", log_file)
    log_message(f"APK Folder: {folder_path}", "INFO", log_file)

    try:
        apk_files = [f for f in os.listdir(folder_path) if f.endswith('.apk')]
    except FileNotFoundError:
        log_message(f"{Fore.RED}Error: The folder '{folder_path}' was not found.{Style.RESET_ALL}", "ERROR", log_file)
        return

    if not apk_files:
        log_message(f"{Fore.YELLOW}No APK files found in the specified folder.{Style.RESET_ALL}", "WARNING", log_file)
        return

    log_message(f"Total APKs to install: {len(apk_files)}\n", "INFO", log_file)

    for i, apk_file in enumerate(apk_files):
        apk_full_path = os.path.join(folder_path, apk_file)
        
        log_message(f"\n[{i+1}/{len(apk_files)}] Attempting to install on device '{device_serial}': {apk_file}...", "INFO", log_file)
        
        try:
            result = subprocess.run(
                ['adb', '-s', device_serial, 'install', '-r', apk_full_path], # Added '-r' to reinstall if app exists
                capture_output=True,
                text=True,
                check=True,
                timeout=300 # 5-minute timeout for a single APK
            )
            log_message(f"-> {Fore.GREEN}SUCCESS{Style.RESET_ALL}: {apk_file} installed successfully.", "SUCCESS", log_file)
        except subprocess.CalledProcessError as e:
            error_output = e.stderr.strip() or e.stdout.strip()
            log_message(f"-> {Fore.RED}FAILED{Style.RESET_ALL}: {apk_file} failed to install.", "ERROR", log_file)
            
            if "INSTALL_FAILED_VERIFICATION_FAILURE" in error_output:
                error_message = "Verification Failure. Try disabling Google Play Protect or 'Verify apps over USB'."
            elif "INSTALL_FAILED_INSUFFICIENT_STORAGE" in error_output:
                error_message = "Insufficient Storage. The device does not have enough free space."
            else:
                error_message = error_output
            
            log_message(f"   {Fore.RED}Error details: {error_message}{Style.RESET_ALL}", "ERROR", log_file)
        except subprocess.TimeoutExpired:
            log_message(f"-> {Fore.RED}FAILED{Style.RESET_ALL}: Installation of {apk_file} timed out.", "ERROR", log_file)

    log_message(f"\nInstallation process for device '{device_serial}' completed. Log file: {log_file}", "INFO", log_file)


def start_installation_processes():
    """
    Starts the installation process on all selected devices.
    """
    if not SELECTED_DEVICES or not APK_FOLDER_PATH:
        print(f"{Fore.RED}Error: Please select at least one device and set the folder path first.{Style.RESET_ALL}")
        msvcrt.getch()
        return

    print("Starting multi-device installation in separate processes...\n")
    processes = []
    for device in SELECTED_DEVICES:
        # Create a new process for each device
        p = multiprocessing.Process(target=install_apks_for_device, args=(device, APK_FOLDER_PATH))
        processes.append(p)
        p.start()

    # Wait for all processes to finish
    for p in processes:
        p.join()
    
    print(f"\n{Fore.CYAN}All installation processes have completed. Check the log files for details.{Style.RESET_ALL}")
    print("-----------------------------------")
    print(f"{Fore.GREEN}Press any key to return to the menu...{Style.RESET_ALL}")
    msvcrt.getch()

if __name__ == "__main__":
    if not check_adb_path():
        print(f"{Fore.RED}Error: 'adb' command not found. Please ensure the Android SDK Platform-Tools are installed and 'adb' is in your system's PATH.")
        print("You can download the tools from here: https://developer.android.com/tools/releases/platform-tools")
        print(f"Press any key to exit...{Style.RESET_ALL}")
        msvcrt.getch()
        sys.exit()

    # Load the last used path at startup
    load_last_path()

    while True:
        print_menu()
        choice = msvcrt.getch().decode()
        if choice == '1':
            select_device_menu()
        elif choice == '2':
            set_folder_path_menu()
        elif choice == '3':
            start_installation_processes()
        elif choice == '4':
            show_about_menu()
        elif choice == '5':
            print(f"\n{Fore.GREEN}Exiting. Goodbye!{Style.RESET_ALL}")
            break
        else:
            print(f"{Fore.RED}Invalid option. Please try again.{Style.RESET_ALL}")
            time.sleep(1)
