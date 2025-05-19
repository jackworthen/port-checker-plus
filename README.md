# 🔌 Port Checker Plus

> **Port Checker Plus** is a sleek, GUI-based port scanning tool designed for developers, sysadmins, and network enthusiasts who want quick insights into open ports on a target host — all in a visually intuitive and exportable way!

---

## 🎯 Features

- 🖥️ **User-friendly GUI** built with `Tkinter`
- ⚡ **Multi-threaded scanning** for fast performance
- 🌐 **Resolve hostnames** before scanning
- 🎯 **Input custom ports or ranges** (e.g., `22,80,1000-1010`)
- 🧩 **Filter results** to show only open ports
- 📁 **Export results** to a text file
- 💾 **Save settings** (including default host, ports, timeout, and export preferences)
- ❌ **Cancel unsaved changes** in settings easily

---

## 🚀 Getting Started

### 🔧 Requirements

- Python 3.8+
- No additional libraries — everything is in the standard library!

### 📦 Installation

```bash
git clone https://github.com/yourusername/port-checker-plus.git
cd port-checker-plus
python portCheckerPlus.py
```

---

## ⚙️ Configuration

The application stores settings in  `config.json`. You can modify the behavior through the GUI settings window.

Example:
```json
{
  "timeout": 0.3,
  "export_results": false,
  "export_directory": "",
  "show_open_only": false,
  "default_host": "localhost",
  "default_ports": "1433"
}
```

---

## 🧪 How to Use

1. Enter a hostname or IP (e.g., `localhost`, `192.168.1.1`)
2. Specify ports (e.g., `22,80,443` or ranges like `1000-1100`)
3. Click **Check Ports**
4. View results and optionally export them to a file
5. Use the **Settings** menu to tweak app behavior

---

## 🧰 Developer Notes

- All port scanning is done using Python’s `socket` module.
- Threads allow non-blocking scanning for large ranges.
- GUI built entirely with `Tkinter`, compatible across platforms.

---

## 🤝 Contributing

Contributions, ideas, and feature requests are welcome!

1. Fork the repo
2. Create a new branch (`git checkout -b feature/fooBar`)
3. Commit your changes
4. Push to the branch (`git push origin feature/fooBar`)
5. Create a new Pull Request

---

## 📄 License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.

---

## 💬 Acknowledgments

- Python community ❤️
- Tkinter for the UI toolkit
- All testers and contributors!

---

### 🚨 Disclaimer

This tool is intended for **educational and authorized use only**. Do not scan hosts you do not own or have permission to test.
