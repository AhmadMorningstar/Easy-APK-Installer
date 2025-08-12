# **Easy APK Installer**

This is a simple yet powerful utility for installing multiple APK files on one or more Android devices simultaneously using ADB. The project offers a command-line interface (CLI) and a graphical user interface (GUI) to suit different user needs.

## **How to Download and Run**

There are three versions available on the [**Releases**](https://github.com/AhmadMorningstar/Easy-APK-Installer/releases) page. Choose the one that works best for you.

#### **For Windows Users (No Python Required)**

1. Download the **easy\_apk\_installer.exe** file from the latest release.  
2. After downloading, you can run the executable directly.

#### **For Users with Python**

1. Download the **easy\_apk\_installer\_cli.py** or **gui\_easy\_apk\_installer.py** file from the latest release.  
2. Make sure you have Python and the necessary libraries installed (see Step 2 in the Prerequisites section).  
3. Run the corresponding file from your terminal:  
   * For the CLI version: python easy\_apk\_installer\_cli.py  
   * For the GUI version: python gui\_easy\_apk\_installer.py

## **Prerequisites: A Guide for Beginners**

To use the Python versions of this program, you will need to set up your environment.

### **Step 1: Install Python**

If you don't already have Python installed, you'll need to get it. This program was written in Python and requires it to run. **(This step is not necessary for the .exe file.)**

1. **Download Python** from the official website: https://www.python.org/downloads/  
2. **Run the installer.**  
3. **IMPORTANT:** During installation, make sure to check the box that says "**Add Python to PATH**." This is a crucial step that allows the program to run Python commands from any directory.

### **Step 2: Install the 'colorama' Library**

This program uses a library called colorama to add color to the text in the terminal. While not strictly necessary for the program to function, it makes the output much easier to read. **(This step is only for the CLI version.)**

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
