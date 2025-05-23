# 🚀 Port Checker Plus

Port Checker Plus is a sleek, user-friendly GUI application built in Python for scanning and resolving TCP and UDP ports on any host. Featuring multi-threading, exportable results, protocol flexibility, and platform-aware configuration storage, it’s perfect for network admins and enthusiasts alike!

---

## 🎨 Features

- ✅ Scan single or multiple ports (range or comma-separated).
- 🌍 Resolve hostnames to IP addresses with retry logic.
- ⚡ Multi-threaded scanning for blazing-fast results.
- 📂 Optional result export with timestamp and service info.
- 🔒 Configurable timeout, retries, and UI preferences.
- 🖥️ Cross-platform support (Windows, macOS, Linux).
- 🧠 Smart input parsing and port validation.
- 🖼️ Built-in settings panel via a clean Tkinter GUI.
- 📄 Export directory selection and auto-log file creation.
- 🔍 Optional filter to show only open ports.
- 🌐 Choose protocol: TCP, UDP, or both (TCP/UDP).
- 📊 Real-time scan progress bar and status indicator.
- 🛠️ Built-in icon support with PyInstaller compatibility.

---

## 🛠️ Installation

1. **Clone this repo or download the script:**

   ```bash
   git clone https://github.com/yourusername/port-checker-plus.git
   cd port-checker-plus
   ```

2. **Install dependencies (Python 3.7+ required):**

   No external packages needed! Just make sure Python’s standard libraries are intact.

3. **(Optional) Create a standalone executable (Windows):**

   ```bash
   pip install pyinstaller
   pyinstaller --onefile --windowed portCheckerPlus.py
   ```

---

## 🧪 How to Use

1. **Run the application:**

   ```bash
   python portCheckerPlus.py
   ```

2. **Enter the hostname or IP and ports:**

   - Format: `80`, `22,80,443`, or `20-25,80,443`
   - Example: `google.com`, `localhost`, `192.168.1.1`

3. **Select the protocol: TCP, UDP, or both.**
4. **Click `Check Ports` to start the scan.**
5. **View results in the scrollable console.**
6. **Use `Clear Results` to reset output.**

---

## ⚙️ Settings Menu

Access via `🔧 View > Settings`:

- Export results toggle and directory.
- Only show open ports toggle.
- Custom timeout for connections.
- Number of DNS retries.
- Default host and ports.
- Select scan protocol: TCP, UDP, or both.

Your settings are saved in:

- 🫏‍♂️ `%APPDATA%\PortCheckerPlus`
- 🍎 `~/Library/Application Support/PortCheckerPlus`
- 🐙 `~/.config/PortCheckerPlus`

---

## 📝 Example Output

```
Resolving hostname: google.com
Resolved IP: 142.250.190.14
Attempt: 1

TCP Port 80 is OPEN (Service: http)
UDP Port 53 is OPEN|FILTERED (no response)

Scan complete.
Number of ports checked: 2
```

---

## 🤝 FAQ

**Q:** Does it require admin/root permissions?  
**A:** Nope! Only basic socket access is needed.

**Q:** Can it export results automatically?  
**A:** Yes, toggle it in Settings and specify your preferred directory.

**Q:** Can it scan UDP ports?  
**A:** Yes, choose UDP or TCP/UDP in the protocol dropdown.

---

## 📜 License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.

---

## 💡 Ideas or Issues?

Feel free to open an issue or suggest improvements! Contributions are always welcome.
