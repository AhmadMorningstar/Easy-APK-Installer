import os
import subprocess
import sys
import time
import webbrowser
# For non-blocking keyboard input on Unix-like systems
import select
# For color-coded terminal output (install with 'pip install colorama')
from colorama import Fore, Style, init

# Initialize colorama for terminal support
init(autoreset=True)

# --- Global Variables ---
APK_FOLDER_PATH = ""
APK_FILES_CACHED = []
SELECTED_DEVICE = {} # Using a dictionary to store both serial and model

def check_adb_path():
    """
    Checks if 'adb' command is available in the system's PATH.
    """
    try:
        # Use a cross-platform check
        subprocess.run(['adb', 'version'], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

def log_message(message, level="INFO"):
    """
    Writes a message to the console with color coding.
    """
    color = Fore.WHITE
    if level == "INFO":
        color = Fore.CYAN
    elif level == "SUCCESS":
        color = Fore.GREEN
    elif level == "ERROR":
        color = Fore.RED
    elif level == "WARNING":
        color = Fore.YELLOW
    
    print(f"{color}{message}{Style.RESET_ALL}")

def print_menu():
    """
    Prints the main menu.
    """
    os.system('cls' if os.name == 'nt' else 'clear')
    print(f"{Fore.CYAN}{Style.BRIGHT}---------------------------------------")
    print(f"|{Fore.YELLOW}       Easy APK Installer            {Fore.CYAN}|")
    print(f"---------------------------------------{Style.RESET_ALL}")
    print(f"{Fore.MAGENTA}          By Ahmad Morningstar{Style.RESET_ALL}")
    print(f"{Fore.CYAN}---------------------------------------{Style.RESET_ALL}")
    print(f"{Fore.GREEN}1. Select ADB Device")
    print(f"{Fore.GREEN}2. Set APK Folder Path")
    print(f"{Fore.GREEN}3. Start bulk installation")
    print(f"{Fore.GREEN}4. Select a specific APK to install")
    print(f"{Fore.GREEN}5. Print device information")
    print(f"{Fore.GREEN}6. About")
    print(f"{Fore.GREEN}7. YouTube Guide")
    print(f"{Fore.GREEN}8. Exit{Style.RESET_ALL}")
    print(f"\n{Fore.MAGENTA}Current Settings:{Style.RESET_ALL}")
    
    device_display = "Not Selected"
    if SELECTED_DEVICE:
        device_display = f"{SELECTED_DEVICE['model']} ({SELECTED_DEVICE['serial']})"
    
    apk_count = len(APK_FILES_CACHED) if APK_FILES_CACHED else 0

    print(f"  {Fore.YELLOW}Device:    {Style.BRIGHT}{device_display}{Style.RESET_ALL}")
    print(f"  {Fore.YELLOW}Folder:    {Style.BRIGHT}{APK_FOLDER_PATH if APK_FOLDER_PATH else 'Not Set'}{Style.RESET_ALL}")
    print(f"  {Fore.YELLOW}APKs found: {Style.BRIGHT}{apk_count}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}---------------------------------------{Style.RESET_ALL}")
    print(f"\n{Fore.GREEN}Enter your choice and press Enter:{Style.RESET_ALL} ", end="")


def open_youtube_guide():
    """
    Opens the YouTube guide link in the default web browser.
    """
    youtube_url = "https://www.youtube.com/@AhmadMorningstar"
    print(f"\n{Fore.CYAN}Opening YouTube guide in your browser...{Style.RESET_ALL}")
    try:
        webbrowser.open(youtube_url)
    except webbrowser.Error as e:
        log_message(f"Failed to open browser: {e}", "ERROR")

def show_about_menu():
    """
    Displays information about the author and the program.
    """
    os.system('cls' if os.name == 'nt' else 'clear')
    print(f"{Fore.CYAN}{Style.BRIGHT}---------------------------------------")
    print(f"|{Fore.YELLOW}          About the Author             {Fore.CYAN}|")
    print(f"---------------------------------------{Style.RESET_ALL}")
    print(f"{Fore.MAGENTA}Author: {Style.BRIGHT}Ahmad Morningstar{Style.RESET_ALL}")
    print(f"\n{Fore.CYAN}Program Description:{Style.RESET_ALL}")
    print(f"This is a simple yet powerful command-line utility for")
    print(f"installing APK files on an Android device using ADB.")
    print(f"\n{Fore.GREEN}Links:{Style.RESET_ALL}")
    print(f"  {Fore.YELLOW}GitHub:    {Style.BRIGHT}https://github.com/AhmadMorningstar{Style.RESET_ALL}")
    print(f"\n{Fore.CYAN}---------------------------------------{Style.RESET_ALL}")
    input(f"{Fore.GREEN}Press Enter to return to the menu...{Style.RESET_ALL}")

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
    Handles the device selection menu for a single device.
    """
    global SELECTED_DEVICE
    devices = get_devices()
    if devices is None:
        print(f"{Fore.RED}Error: 'adb' command not found. Please ensure it's installed and in your PATH.{Style.RESET_ALL}")
        input("Press Enter to continue...")
        return

    if not devices:
        print(f"{Fore.YELLOW}No ADB devices found. Please check your connection and USB debugging settings.{Style.RESET_ALL}")
        input("Press Enter to continue...")
        return

    if len(devices) == 1:
        SELECTED_DEVICE = devices[0]
        print(f"{Fore.GREEN}Only one device found. Automatically selected:{Style.RESET_ALL} {Fore.CYAN}{SELECTED_DEVICE['model']} ({SELECTED_DEVICE['serial']}){Style.RESET_ALL}")
        input("Press Enter to continue...")
        return

    print("\nAvailable Devices:")
    for i, device in enumerate(devices):
        print(f"  {i + 1}. {Fore.CYAN}Serial:{Style.BRIGHT}{device['serial']}{Style.RESET_ALL}, {Fore.CYAN}Model:{Style.BRIGHT}{device['model']}{Style.RESET_ALL}")

    while True:
        try:
            choice = input(f"\n{Fore.GREEN}Enter the number of the device to select: {Style.RESET_ALL}")
            selected_index = int(choice.strip()) - 1
            
            if 0 <= selected_index < len(devices):
                SELECTED_DEVICE = devices[selected_index]
                print(f"{Fore.GREEN}Selected device:{Style.RESET_ALL} {Fore.CYAN}{SELECTED_DEVICE['model']} ({SELECTED_DEVICE['serial']}){Style.RESET_ALL}")
                break
            else:
                print(f"{Fore.RED}Invalid selection. Please enter a valid number.{Style.RESET_ALL}")
        except ValueError:
            print(f"{Fore.RED}Invalid input. Please enter a number.{Style.RESET_ALL}")
    input("Press Enter to continue...")

def set_folder_path_menu():
    """
    Handles the folder path selection menu.
    """
    global APK_FOLDER_PATH, APK_FILES_CACHED
    path = input(f"{Fore.GREEN}Enter the full path to the folder containing your APKs: {Style.RESET_ALL}")
    if os.path.isdir(path):
        APK_FOLDER_PATH = path
        scan_for_apks() # Scan the new path immediately
        print(f"{Fore.GREEN}Folder path set to: '{path}'.{Style.RESET_ALL}")
    else:
        print(f"{Fore.RED}Error: The provided path does not exist or is not a directory.{Style.RESET_ALL}")
    input("Press Enter to continue...")

def scan_for_apks():
    """
    Scans the APK_FOLDER_PATH for APK files and caches the list.
    """
    global APK_FILES_CACHED
    APK_FILES_CACHED = []
    if APK_FOLDER_PATH and os.path.isdir(APK_FOLDER_PATH):
        try:
            APK_FILES_CACHED = sorted([f for f in os.listdir(APK_FOLDER_PATH) if f.endswith('.apk')])
        except FileNotFoundError:
            pass # Path no longer exists, list remains empty
    
def install_apks_for_device(device_serial, folder_path, apks_to_install, allow_skip=True, grant_permissions=False):
    """
    Installs a list of APKs on a single device, showing real-time progress and allowing skips.
    """
    success_count = 0
    failure_count = 0
    skipped_count = 0
    
    log_message(f"--- Starting installation for device: {device_serial} ---", "INFO")
    
    if not apks_to_install:
        log_message(f"No APK files were provided for device: {device_serial}.", "WARNING")
        return

    spinner = ['/', '-', '\\', '|']
    spinner_index = 0

    for i, apk_file in enumerate(apks_to_install):
        apk_full_path = os.path.join(folder_path, apk_file)
        
        print(f"\n[{i+1}/{len(apks_to_install)}] Installing '{apk_file}'... ", end="", flush=True)

        command = ['adb', '-s', device_serial, 'install', '-r']
        if grant_permissions:
            command.append('-g')
        command.append(apk_full_path)
        
        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        skipped_this_apk = False
        while process.poll() is None:
            sys.stdout.write(f"\r[{i+1}/{len(apks_to_install)}] Installing '{apk_file}'... {Fore.YELLOW}{spinner[spinner_index]}{Style.RESET_ALL}")
            sys.stdout.flush()
            spinner_index = (spinner_index + 1) % len(spinner)

            if allow_skip:
                if sys.stdin in select.select([sys.stdin], [], [], 0)[0]:
                    key = sys.stdin.read(1).lower()
                    if key == 's':
                        sys.stdout.write("\r" + " " * 80 + "\r")
                        sys.stdout.flush()
                        log_message(f"Skipping '{apk_file}'...", "WARNING")
                        process.terminate()
                        skipped_this_apk = True
                        break
            time.sleep(0.1)
        
        sys.stdout.write("\r" + " " * 80 + "\r")
        sys.stdout.flush()
        
        stdout, stderr = process.communicate()
        
        if skipped_this_apk:
            skipped_count += 1
            continue
            
        if process.returncode == 0:
            if "Success" in (stdout + stderr):
                log_message(f"-> SUCCESS: {apk_file} installed successfully.", "SUCCESS")
                success_count += 1
            else:
                log_message(f"-> FAILED: {apk_file} failed to install. (No 'Success' message found)", "ERROR")
                failure_count += 1
        else:
            log_message(f"-> FAILED: {apk_file} failed with return code {process.returncode}.", "ERROR")
            failure_count += 1
            
        if stdout:
            print(f"  {Fore.MAGENTA}-> {stdout.strip()}{Style.RESET_ALL}")
        if stderr:
            print(f"  {Fore.RED}-> {stderr.strip()}{Style.RESET_ALL}")
    
    log_message(f"\nInstallation for device '{device_serial}' complete.", "INFO")
    print(f"\nSummary for '{device_serial}': {Fore.GREEN}{success_count} successful{Style.RESET_ALL}, {Fore.RED}{failure_count} failed.{Style.RESET_ALL}, {Fore.YELLOW}{skipped_count} skipped.{Style.RESET_ALL}")
    print(f"Total APKs processed: {len(apks_to_install)}")
    print("-----------------------------------")
    
    input(f"{Fore.GREEN}Press Enter to return to the menu...{Style.RESET_ALL}")


def start_bulk_installation():
    """
    Gets all APKs in the folder and starts the installation process with 'skip' verification.
    """
    if not SELECTED_DEVICE:
        print(f"{Fore.RED}Error: Please select a device first.{Style.RESET_ALL}")
        input("Press Enter to continue...")
        return

    if not APK_FOLDER_PATH:
        print(f"{Fore.RED}Error: Please set the folder path first.{Style.RESET_ALL}")
        input("Press Enter to continue...")
        return

    apk_files = APK_FILES_CACHED
    if not apk_files:
        print(f"{Fore.YELLOW}No APK files found in the specified folder.{Style.RESET_ALL}")
        input("Press Enter to continue...")
        return

    grant_permissions = False
    while True:
        choice = input(f"\n{Fore.GREEN}Do you want to force-install and grant all permissions? (y/n): {Style.RESET_ALL}").lower()
        if choice in ['y', 'n']:
            grant_permissions = (choice == 'y')
            break
        else:
            print(f"{Fore.RED}Invalid input. Please enter 'y' or 'n'.{Style.RESET_ALL}")

    install_apks_for_device(SELECTED_DEVICE['serial'], APK_FOLDER_PATH, apk_files, allow_skip=True, grant_permissions=grant_permissions)


def select_and_install_single_apk():
    """
    Allows the user to select a single APK and starts the installation.
    """
    if not SELECTED_DEVICE:
        print(f"{Fore.RED}Error: Please select a device first.{Style.RESET_ALL}")
        input("Press Enter to continue...")
        return
    
    if not APK_FOLDER_PATH:
        print(f"{Fore.RED}Error: Please set the folder path first.{Style.RESET_ALL}")
        input("Press Enter to continue...")
        return

    apk_files = APK_FILES_CACHED
    if not apk_files:
        print(f"{Fore.YELLOW}No APK files found in the specified folder.{Style.RESET_ALL}")
        input("Press Enter to continue...")
        return
        
    print("\nAvailable APKs:")
    for i, apk in enumerate(apk_files):
        print(f"  {i + 1}. {Fore.CYAN}{apk}{Style.RESET_ALL}")
    print(f"  {Fore.YELLOW}0. Go Back to Main Menu{Style.RESET_ALL}")

    while True:
        try:
            choice = int(input(f"\n{Fore.GREEN}Enter the number of the APK to install or '0' to go back: {Style.RESET_ALL}"))
            if choice == 0:
                print(f"{Fore.YELLOW}Returning to main menu...{Style.RESET_ALL}")
                return
            elif 1 <= choice <= len(apk_files):
                selected_apk_file = apk_files[choice - 1]
                log_message(f"Selected APK: '{selected_apk_file}'", "INFO")

                grant_permissions = False
                while True:
                    permission_choice = input(f"{Fore.GREEN}Do you want to force-install and grant all permissions for this APK? (y/n): {Style.RESET_ALL}").lower()
                    if permission_choice in ['y', 'n']:
                        grant_permissions = (permission_choice == 'y')
                        break
                    else:
                        print(f"{Fore.RED}Invalid input. Please enter 'y' or 'n'.{Style.RESET_ALL}")
                
                install_apks_for_device(SELECTED_DEVICE['serial'], APK_FOLDER_PATH, [selected_apk_file], allow_skip=False, grant_permissions=grant_permissions)
                break
            else:
                print(f"{Fore.RED}Invalid number. Please enter a number from the list or '0'.{Style.RESET_ALL}")
        except ValueError:
            print(f"{Fore.RED}Invalid input. Please enter a number.{Style.RESET_ALL}")


def print_device_info():
    """
    Fetches and prints detailed information for the selected device.
    """
    if not SELECTED_DEVICE:
        print(f"{Fore.RED}Error: No device has been selected. Please select one first.{Style.RESET_ALL}")
        input("Press Enter to continue...")
        return

    print("\n")
    print(f"{Fore.CYAN}--- Device Information for '{SELECTED_DEVICE['serial']}' ---{Style.RESET_ALL}")
    try:
        # Get device properties
        manufacturer = subprocess.run(['adb', '-s', SELECTED_DEVICE['serial'], 'shell', 'getprop', 'ro.product.manufacturer'], capture_output=True, text=True, check=True, timeout=10).stdout.strip()
        model = subprocess.run(['adb', '-s', SELECTED_DEVICE['serial'], 'shell', 'getprop', 'ro.product.model'], capture_output=True, text=True, check=True, timeout=10).stdout.strip()
        build_id = subprocess.run(['adb', '-s', SELECTED_DEVICE['serial'], 'shell', 'getprop', 'ro.build.display.id'], capture_output=True, text=True, check=True, timeout=10).stdout.strip()
        
        # Get RAM info
        meminfo_output = subprocess.run(['adb', '-s', SELECTED_DEVICE['serial'], 'shell', 'cat', '/proc/meminfo'], capture_output=True, text=True, check=True, timeout=10).stdout
        ram_total = 'N/A'
        for line in meminfo_output.splitlines():
            if 'MemTotal:' in line:
                ram_kb = int(''.join(filter(str.isdigit, line)))
                ram_gb = ram_kb / 1024 / 1024
                ram_total = f"{ram_gb:.2f} GB"
                break

        # Get Storage info
        df_output = subprocess.run(['adb', '-s', SELECTED_DEVICE['serial'], 'shell', 'df', '-h', '/data'], capture_output=True, text=True, check=True, timeout=10).stdout.splitlines()
        storage_info = 'N/A'
        if len(df_output) > 1:
            storage_info = df_output[1].split()[1] # Size of the data partition
        
        # Get CPU info
        cpu_output = subprocess.run(['adb', '-s', SELECTED_DEVICE['serial'], 'shell', 'cat', '/proc/cpuinfo'], capture_output=True, text=True, check=True, timeout=10).stdout
        cpu_model = 'N/A'
        for line in cpu_output.splitlines():
            if 'Hardware' in line:
                cpu_model = line.split(':')[-1].strip()
                break
        
        # Note on GPU: Getting reliable GPU info via simple adb commands is difficult.
        gpu_info = "N/A (Complex to fetch via adb)"

        print(f"  {Fore.YELLOW}Company Name:{Style.RESET_ALL}       {manufacturer}")
        print(f"  {Fore.YELLOW}Model Name:{Style.RESET_ALL}         {model}")
        print(f"  {Fore.YELLOW}Serial Number:{Style.RESET_ALL}      {SELECTED_DEVICE['serial']}")
        print(f"  {Fore.YELLOW}Build Number:{Style.RESET_ALL}       {build_id}")
        print(f"  {Fore.YELLOW}RAM:{Style.RESET_ALL}                {ram_total}")
        print(f"  {Fore.YELLOW}Storage:{Style.RESET_ALL}            {storage_info}")
        print(f"  {Fore.YELLOW}CPU:{Style.RESET_ALL}                {cpu_model}")
        print(f"  {Fore.YELLOW}GPU:{Style.RESET_ALL}                {gpu_info}")
        print(f"{Fore.CYAN}---------------------------------------{Style.RESET_ALL}")

    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError) as e:
        print(f"{Fore.RED}  Error fetching details for device '{SELECTED_DEVICE['serial']}': {e}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}---------------------------------------{Style.RESET_ALL}")
    
    input(f"{Fore.GREEN}Press Enter to return to the menu...{Style.RESET_ALL}")

if __name__ == "__main__":
    # Check for adb
    if not check_adb_path():
        print(f"{Fore.RED}Error: 'adb' command not found. Please ensure the Android SDK Platform-Tools are installed and 'adb' is in your system's PATH.")
        print(f"You can download the tools from here: https://developer.android.com/tools/releases/platform-tools")
        input(f"Press Enter to exit...{Style.RESET_ALL}")
        sys.exit()

    # Initial check for connected devices to improve user experience
    devices_on_startup = get_devices()
    if not devices_on_startup:
        print(f"{Fore.YELLOW}No ADB devices found on startup. Please connect a device and enable USB debugging.")
        input(f"Press Enter to continue to the main menu...{Style.RESET_ALL}")

    # Initialize path as empty, no remembering feature
    APK_FOLDER_PATH = ""
    scan_for_apks()

    while True:
        print_menu()
        choice = input()
        
        if choice == '1':
            select_device_menu()
        elif choice == '2':
            set_folder_path_menu()
        elif choice == '3':
            start_bulk_installation()
        elif choice == '4':
            select_and_install_single_apk()
        elif choice == '5':
            print_device_info()
        elif choice == '6':
            show_about_menu()
        elif choice == '7':
            open_youtube_guide()
        elif choice == '8':
            print(f"\n{Fore.GREEN}Exiting. Goodbye!{Style.RESET_ALL}")
            break
        else:
            print(f"{Fore.RED}Invalid option. Please try again.{Style.RESET_ALL}")
            time.sleep(1)