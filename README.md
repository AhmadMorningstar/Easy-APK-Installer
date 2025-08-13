# **Easy APK Installer**

A simple and powerful utility for installing multiple APK files on one or more connected Android devices simultaneously using ADB.

### **How to Download and Run**

There are two primary versions of this application available on the **[Releases](https://github.com/AhmadMorningstar/Easy-APK-Installer/releases).** page. Choose the one that corresponds to your operating system.

#### **For Windows Users**

* Download the easy\_apk\_installer.exe file from the latest release.  
* This version provides a **graphical user interface (GUI)** with a **dark** theme.  
* You can run the executable directly after downloading it. No additional software is required beyond the ADB prerequisites.

#### **For Linux & Mac Users** (Cooming Soon!)

* Download the easy\_apk\_installer.py file from the latest release.  
* This version runs in your terminal.  
* You will need to have Python and the colorama library installed (see Prerequisites).  
* Run the file from your terminal using the following command:  
  python easy\_apk\_installer.py

### **File Descriptions**

| File Name | Operating System | Description |
| :---- | :---- | :---- |
| easy\_apk\_installer.exe | Windows | A standalone executable with a graphical user interface (GUI). |
| easy\_apk\_installer.py | Linux & Mac | A Python script for use in the terminal. |

### **Prerequisites**

To get started, you must first have the **Android ADB tools** set up on your system. For Windows That’s all You need but for Linux and Mac version, you also need Python and a library.

#### **Step 1: Install the Android ADB Tools**

This package contains the adb (Android Debug Bridge) command, the core tool this program uses to communicate with your Android devices.

* **For Windows Users:**  
  * **Official Google Release:** Download the Platform-Tools package from [Google's official website](https://developer.android.com/tools/releases/platform-tools). Unzip the file and add the directory to your system's PATH.  
  * **15-Second Installer:** For a faster, automated option, download and run the installer from [https://androidmtk.com/download-15-seconds-adb-installer](https://androidmtk.com/download-15-seconds-adb-installer). When prompted, simply press Y and Enter to confirm each step.  
* **For Linux Users:**  
  * The easiest way is through your system's package manager.  
  * **Debian, Ubuntu, Mint:** sudo apt install android-tools-adb  
  * **Fedora, CentOS:** sudo dnf install android-tools  
  * **Arch Linux:** sudo pacman \-S android-tools  
* **For Mac Users:**  
  * Download the Platform-Tools package from [Google's official website](https://developer.android.com/tools/releases/platform-tools) and add the directory to your system's PATH. Alternatively, you can use a package manager like Homebrew.

#### **Step 2: Python & Library (Linux & Mac Only)**

The Python version requires Python and the colorama library to run.

* **Install Python:** Download and install Python from the [official website](https://www.python.org/downloads/).  
* **Install 'colorama':** Open your terminal and run the following command to install the library, which provides colored text for better readability:  
  pip install colorama

### **Step 3: Connect Your Android Device**

Finally, prepare your Android device for communication with your computer.

1. On your phone, go to **Settings \> About phone** and tap **Build number** seven times to enable Developer Options.  
2. Navigate back to the main Settings menu, find **Developer options**, and enable **USB debugging**.  
3. Connect your device to your computer with a USB cable.  
4. When prompted on your device, accept the **"Allow USB debugging"** dialog.
