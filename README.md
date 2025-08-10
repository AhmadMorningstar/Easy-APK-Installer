# **Easy APK Installer**

This is a simple yet powerful command-line utility for installing multiple APK files on one or more Android devices simultaneously using ADB.

## **How to Get the Program**

1. **Download the latest release:** Go to the [**Releases**](https://www.google.com/search?q=https://github.com/AhmadMorningstar/Easy-APK-Installer/releases) page for this repository.  
2. Download the easy\_apk\_installer\_cli.py file from the latest release.

## **Prerequisites: A Guide for Beginners**

To use this program, you need to have a few things installed and set up on your computer. Follow these steps carefully, and you'll be ready to go in no time.

### **Step 1: Install Python**

If you don't already have Python installed, you'll need to get it. This program was written in Python and requires it to run.

1. **Download Python** from the official website: https://www.python.org/downloads/  
2. **Run the installer.**  
3. **IMPORTANT:** During installation, make sure to check the box that says "**Add Python to PATH**." This is a crucial step that allows the program to run Python commands from any directory.

### **Step 2: Install the 'colorama' Library**

This program uses a library called colorama to add color to the text in the terminal. While not strictly necessary for the program to function, it makes the output much easier to read.

1. Open your command prompt or terminal.  
2. Type the following command and press Enter:

pip install colorama

### **Step 3: Install the Android ADB Tools**

This package contains the **adb (Android Debug Bridge)** command, which is the core tool this program uses to communicate with your Android device(s). You have a few options for installation, depending on your operating system:

#### **For Windows Users**

1. **Official Google Release:** Download the full **Platform-Tools package** from Google's official website: https://developer.android.com/tools/releases/platform-tools  
   * Unzip the downloaded file to a simple location, like C:\\platform-tools, and follow the steps in the next section to add it to your PATH.  
2. **Simple 15-Second Installer:** For an automated and faster option, use the installer from https://androidmtk.com/download-15-seconds-adb-installer.  
   * This installer automatically adds ADB to your system's PATH. When prompted, simply press Y to confirm.

#### **For Linux Users**

The easiest way to install ADB on most Linux distributions is through the system's package manager. The specific command depends on your distribution:

* **Debian, Ubuntu, and Mint:** Use the apt package manager.  
  sudo apt update  
  sudo apt install android-tools-adb android-tools-fastboot

* **Fedora, CentOS, Rocky Linux, and AlmaLinux:** Use the dnf or yum package manager.  
  sudo dnf install android-tools

  or  
  sudo yum install android-tools

* **Arch Linux:** Use the pacman package manager.  
  sudo pacman \-S android-tools

* **Alpine Linux:** Use the apk package manager.  
  sudo apk add adb

* **Gentoo Linux:** Use the emerge package manager.  
  sudo emerge \-a dev-util/android-tools

For distributions not listed above, consult your specific package manager's documentation.

### **Step 4: Connect your Android Device**

Finally, you need to prepare your Android device for communication with your computer.

1. On your phone, go to **Settings** \> **About phone** and tap the **Build number** seven times to enable **Developer Options**.  
2. Go back to the main Settings menu, find **Developer options**, and enable **USB debugging**.  
3. Connect your device to your computer using a USB cable.  
4. When prompted, accept the "Allow USB debugging" dialog on your device.

You are now ready to run the Easy APK Installer\!

Simply run the following command in your terminal:

python easy\_apk\_installer.py  
