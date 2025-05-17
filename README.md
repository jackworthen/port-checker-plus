# 🔌 Port Checker Plus 🎉

**Port Checker Plus** is a **user-friendly, customizable, and colorful GUI tool** for scanning ports on any host! Built with 💙 Python and Tkinter, it's perfect for network tinkerers, sysadmins, and anyone curious about what's open or not on a server!

---

## ✨ Features

- 🔍 **Scan any host and port range** (e.g. `1-100`, `22,80,443`)
- 🟢 **Only Show Open Ports** with a simple checkbox
- 🗂️ **Export Results** to a `.txt` file with timestamps
- ⚙️ **Settings Panel** with:
  - Customizable default host and ports
  - Adjustable timeout (now with a compact UI 😉)
  - Export directory selection
- 🎨 Clean and compact **Tkinter GUI**

---

## 🚀 Getting Started

### ✅ Prerequisites

- Python 3.x
- No external dependencies!

### 📦 Installation

```bash
git clone https://github.com/jackworthen/port-checker-plus.git
cd port-checker-plus
python portCheckerPlus.py
```

---

## 🛠 Usage

1. Enter the **host** and **port range**.
2. Click **Check Ports**.
3. View colorful results in real-time.
4. Toggle **Only Show Open Ports** or **Export Results** from the Settings menu.

---

## 🧠 Example Inputs

- **Host**: `localhost` or `example.com`
- **Ports**: `20-25,80,443` or `1-1024`

---

## 📁 Exported Results

If enabled, results are saved to the chosen directory as:
```
scan_results_YYYYMMDD_HHMMSS.txt
```

---

## 💡 Customization

The app remembers your preferences using a simple `config.json` file:
```json
{
  "timeout": 0.3,
  "export_results": true,
  "export_directory": "",
  "show_open_only": true,
  "default_host": "localhost",
  "default_ports": "1-1024"
}
```

---

## 🤖 Future Ideas

- 🔄 Async scanning
- 🌐 Domain resolution and IP info
- 📊 Port usage stats visualization

---

## 🧑‍💻 Author

Made with ❤️ by **Jack Worthen**

> Contributions welcome! Fork it, star it, and scan responsibly!

---

## 📜 License

MIT License — use it, share it, break it (gently) 💥
